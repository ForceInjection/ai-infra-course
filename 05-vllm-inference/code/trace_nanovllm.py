#!/usr/bin/env python3
"""nano-vllm 执行追踪 — 观察 Sequence 状态转换和 Block 分配

用法:
    # 默认追踪两个短 prompt
    python trace_nanovllm.py

    # 指定模型路径和 prompt
    python trace_nanovllm.py --model ~/huggingface/Qwen3-0.6B/ \\
        --prompts "你好" "什么是GPU?" --max-tokens 128

依赖:
    pip install nanovllm  (或 pip install git+https://github.com/ForceInjection/nano-vllm.git)

观察要点:
    1. Sequence 创建: [SEQ X] CREATED → WAITING 状态
    2. Block 分配: [BLOCK] ALLOCATE → block_table 和 free_blocks 变化
    3. 调度阶段: [SCHED] STEP → Prefill/Decode 交替
    4. Sequence 完成: status→FINISHED_STOPPED / FINISHED_LENGTH
    5. Block 回收: [BLOCK] DEALLOCATE → free_blocks 增加
    6. Preemption: [SCHED] PREEMPT → 显存不足时触发

课堂对应:
    模块 5: 大模型推理框架入门：以 vLLM 为例 — 实验 3 (PPT 第 49–50 页)
"""

import argparse
import os
import sys

from nanovllm import LLM, SamplingParams


def setup_tracing():
    """Monkey-patch nano-vllm 核心模块，在执行关键操作时输出日志。"""

    from nanovllm.engine import block_manager as bm_mod
    from nanovllm.engine import scheduler as sch_mod
    from nanovllm.engine import sequence as seq_mod

    # ── Sequence 创建 ──
    _orig_sequence_init = seq_mod.Sequence.__init__

    def _traced_init(self, token_ids, sampling_params=None):
        _orig_sequence_init(self, token_ids, sampling_params)
        print(
            f"[SEQ {self.seq_id}] CREATED | status=WAITING | "
            f"num_tokens={self.num_tokens} | num_blocks={self.num_blocks}"
        )

    seq_mod.Sequence.__init__ = _traced_init

    # ── Block 分配 ──
    _orig_allocate = bm_mod.BlockManager.allocate

    def _traced_allocate(self, seq, num_cached_blocks):
        _orig_allocate(self, seq, num_cached_blocks)
        print(
            f"[BLOCK] ALLOCATE seq={seq.seq_id} | "
            f"cached_blocks={num_cached_blocks} | "
            f"new_blocks={seq.num_blocks - num_cached_blocks} | "
            f"block_table={seq.block_table} | "
            f"free_blocks={len(self.free_block_ids)}"
        )

    bm_mod.BlockManager.allocate = _traced_allocate

    # ── Block 回收 ──
    _orig_deallocate = bm_mod.BlockManager.deallocate

    def _traced_deallocate(self, seq):
        print(
            f"[BLOCK] DEALLOCATE seq={seq.seq_id} | "
            f"block_table={seq.block_table}"
        )
        _orig_deallocate(self, seq)

    bm_mod.BlockManager.deallocate = _traced_deallocate

    # ── Preemption ──
    _orig_preempt = sch_mod.Scheduler.preempt

    def _traced_preempt(self, seq):
        print(f"[SCHED] PREEMPT seq={seq.seq_id} | reason=OOM (no free blocks)")
        _orig_preempt(self, seq)

    sch_mod.Scheduler.preempt = _traced_preempt

    # ── 每步调度 ──
    _orig_postprocess = sch_mod.Scheduler.postprocess

    def _traced_postprocess(self, seqs, token_ids, is_prefill):
        for seq, tok_id in zip(seqs, token_ids):
            phase = "PREFILL" if is_prefill else "DECODE"
            status = seq.status.name
            print(
                f"[SCHED] STEP seq={seq.seq_id} | phase={phase} | "
                f"token={tok_id} | num_tokens={seq.num_tokens} | "
                f"cached={seq.num_cached_tokens} | status→{status}"
            )
        _orig_postprocess(self, seqs, token_ids, is_prefill)

    sch_mod.Scheduler.postprocess = _traced_postprocess


def main():
    parser = argparse.ArgumentParser(description="nano-vllm 执行追踪")
    parser.add_argument(
        "--model",
        default=os.path.join(os.environ.get("HOME", ""), "huggingface/Qwen3-0.6B/"),
        help="模型路径 (默认: ~/huggingface/Qwen3-0.6B/)",
    )
    parser.add_argument(
        "--prompts",
        nargs="+",
        default=["你好，请介绍你自己。", "什么是GPU? 请详细解释。"],
        help="输入 prompt 列表",
    )
    parser.add_argument("--max-tokens", type=int, default=64, help="最大生成 token 数")
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=0.6,
        help="GPU 显存使用比例 (默认 0.6; 调低可触发 Preemption)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.model):
        print(f"错误: 模型路径不存在: {args.model}", file=sys.stderr)
        print("请先下载模型，例如:", file=sys.stderr)
        print(
            "  huggingface-cli download --resume-download Qwen/Qwen3-0.6B "
            f"--local-dir {args.model}",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── 安装追踪 ──
    setup_tracing()

    # ── 运行推理 ──
    print("=" * 60)
    print("nano-vllm 执行追踪开始")
    print(f"模型: {args.model}")
    print(f"显存利用: {args.gpu_memory_utilization * 100:.0f}%")
    print(f"prompts: {len(args.prompts)} 个")
    print("=" * 60)

    llm = LLM(
        args.model,
        enforce_eager=True,
        gpu_memory_utilization=args.gpu_memory_utilization,
    )
    sampling_params = SamplingParams(temperature=0.6, max_tokens=args.max_tokens)

    outputs = llm.generate(args.prompts, sampling_params)

    print("\n" + "=" * 60)
    print("输出结果:")
    for i, output in enumerate(outputs):
        print(f"\n--- Prompt {i + 1} ---")
        print(output["text"][:200])


if __name__ == "__main__":
    main()
