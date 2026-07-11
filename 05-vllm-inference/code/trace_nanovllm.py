#!/usr/bin/env python3
"""nano-vllm 执行追踪 — 观察 Sequence 状态转换和 Block 分配

用法:
    # 注意: 需设置 PYTHONPATH 指向 nano-vllm 源码目录
    export PYTHONPATH=/tmp/nano-vllm:$PYTHONPATH

    # 默认追踪两个短 prompt (需先下载 Qwen3-0.6B 到 ~/huggingface/)
    python3 trace_nanovllm.py

    # 指定模型路径和 prompt
    python3 trace_nanovllm.py --model ~/huggingface/Qwen3-0.6B/          --prompts "你好" "什么是GPU?" --max-tokens 128

    # 降低显存利用 → 更容易触发 Preemption
    python3 trace_nanovllm.py --gpu-memory-utilization 0.3

依赖:
    - nano-vllm (源码): https://github.com/ForceInjection/nano-vllm
    - PyTorch 2.6.0+cu124, flash-attn 2.7.4.post1
    - 模型: Qwen3-0.6B (~1.5 GB, 从 ModelScope 或 HuggingFace 下载)
    完整安装步骤见 code/README.md

输出说明 (对应 PPT 第 49–50 页):
    [SEQ X] CREATED   — Sequence 创建，初始 num_tokens/num_blocks
    [BLOCK] ALLOCATE  — Block 分配: cached_blocks/Prefix Cache 命中数, block_table, 剩余 free_blocks
    [SCHED] STEP      — Scheduler 每步调度: Prefill 或 Decode 阶段, token ID, 进度
    [BLOCK] DEALLOCATE— Sequence 完成或 Preemption 时回收 Block
    [SCHED] PREEMPT   — 显存不足触发抢占 (降低 gpu_memory_utilization 更容易观察)
"""

import argparse
import os
import sys


def setup_tracing():
    """Monkey-patch nano-vllm 核心模块，在关键操作点注入追踪日志。

    通过替换以下方法实现无侵入追踪:
      - Sequence.__init__   → 打印序列创建
      - BlockManager.allocate/deallocate → 打印显存块分配/回收
      - Scheduler.preempt   → 打印抢占事件
      - Scheduler.postprocess → 打印每步 Prefill/Decode 调度

    注意: warmup 阶段创建的假序列 (num_tokens=4096) 会被自动过滤。
    """

    from nanovllm.engine import block_manager as bm_mod
    from nanovllm.engine import scheduler as sch_mod
    from nanovllm.engine import sequence as seq_mod
    from nanovllm.sampling_params import SamplingParams as _SP

    # ── Sequence 创建 ──
    # nano-vllm 在 warmup 时会创建 num_tokens=4096 的假序列用于 CUDA Graph 预热。
    # 通过 num_tokens < 4096 过滤掉这些预热序列，只追踪用户的实际请求。
    _orig_sequence_init = seq_mod.Sequence.__init__

    def _traced_init(self, token_ids, sampling_params=_SP()):
        _orig_sequence_init(self, token_ids, sampling_params)
        if self.num_tokens < 4096:
            print(
                f"[SEQ {self.seq_id}] CREATED | "
                f"num_tokens={self.num_tokens} | "
                f"num_blocks={self.num_blocks}"
            )

    seq_mod.Sequence.__init__ = _traced_init

    # ── Block 分配 ──
    # BlockManager.allocate 在每次 Sequence 需要新显存块时调用。
    # num_cached_blocks > 0 表示 Prefix Cache 命中 (复用了已有 Block)。
    _orig_allocate = bm_mod.BlockManager.allocate

    def _traced_allocate(self, seq, num_cached_blocks):
        _orig_allocate(self, seq, num_cached_blocks)
        print(
            f"[BLOCK] ALLOCATE seq={seq.seq_id} | "
            f"cached={num_cached_blocks} | "
            f"new={seq.num_blocks - num_cached_blocks} | "
            f"block_table={seq.block_table} | "
            f"free_blocks={len(self.free_block_ids)}"
        )

    bm_mod.BlockManager.allocate = _traced_allocate

    # ── Block 回收 ──
    # Sequence 生成完成或被 Preempt 时回收其占用的所有 Block。
    _orig_deallocate = bm_mod.BlockManager.deallocate

    def _traced_deallocate(self, seq):
        print(
            f"[BLOCK] DEALLOCATE seq={seq.seq_id} | "
            f"block_table={seq.block_table}"
        )
        _orig_deallocate(self, seq)

    bm_mod.BlockManager.deallocate = _traced_deallocate

    # ── Preemption ──
    # 显存不足时 Scheduler 会抢占 (驱逐) 低优先级 Sequence，释放其 Block。
    _orig_preempt = sch_mod.Scheduler.preempt

    def _traced_preempt(self, seq):
        print(f"[SCHED] PREEMPT seq={seq.seq_id} | reason=OOM (no free blocks)")
        _orig_preempt(self, seq)

    sch_mod.Scheduler.preempt = _traced_preempt

    # ── 每步调度 ──
    # Scheduler.postprocess 在每个调度周期 (Prefill 或 Decode) 后更新 Sequence 状态。
    # Prefill: 一次处理 prompt 中所有 tokens，产生首个输出 token
    # Decode:  每次产生 1 个 token，重复直到 max_tokens 或 EOS
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

    # 检查模型是否存在
    if not os.path.isdir(args.model):
        print(f"错误: 模型路径不存在: {args.model}", file=sys.stderr)
        print("请先下载模型，例如:", file=sys.stderr)
        print(
            "  modelscope download --model Qwen/Qwen3-0.6B "
            f"--local-dir {args.model}",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── 安装 Monkey-Patch 追踪 ──
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

    # ── 打印输出 ──
    print("\n" + "=" * 60)
    print("输出结果:")
    for i, output in enumerate(outputs):
        print(f"\n--- Prompt {i + 1} ---")
        print(output["text"][:200])


if __name__ == "__main__":
    main()
