# 模块 5 配套代码 — vLLM 推理框架

## 文件说明

| 文件                | 内容                            | 对应 PPT             |
| ------------------- | ------------------------------- | -------------------- |
| `trace_nanovllm.py` | nano-vllm monkey-patch 追踪脚本 | 第 49–50 页 [动手 2] |

nano-vllm 源码在独立仓库，无需复制到此处:  
https://github.com/ForceInjection/nano-vllm

## 环境要求

- Python ≥ 3.10
- CUDA ≥ 12.1
- GPU with Compute Capability ≥ 7.0 (≥ 8 GB 显存推荐)
- nano-vllm: `pip install git+https://github.com/ForceInjection/nano-vllm.git`
- 模型: Qwen3-0.6B (~1.2 GB, `huggingface-cli download Qwen/Qwen3-0.6B`)

## 运行方法

```bash
# 默认追踪 (两个短 prompt)
python trace_nanovllm.py

# 自定义模型和 prompt
python trace_nanovllm.py \
    --model ~/huggingface/Qwen3-0.6B/ \
    --prompts "你好" "什么是GPU?" "介绍一下你自己" \
    --max-tokens 128

# 降低显存利用 → 更容易触发 Preemption
python trace_nanovllm.py --gpu-memory-utilization 0.3
```

## 预期输出

```text
============================================================
nano-vllm 执行追踪开始
模型: ~/huggingface/Qwen3-0.6B/
显存利用: 60%
prompts: 2 个
============================================================
[SEQ 0] CREATED | status=WAITING | num_tokens=7 | num_blocks=1
[SEQ 1] CREATED | status=WAITING | num_tokens=12 | num_blocks=1
[BLOCK] ALLOCATE seq=0 | cached_blocks=0 | new_blocks=1 | block_table=[0] | free_blocks=119
[SCHED] STEP seq=0 | phase=PREFILL | token=... | num_tokens=8 | cached=7 | status→RUNNING
[BLOCK] ALLOCATE seq=1 | cached_blocks=0 | new_blocks=1 | block_table=[1] | free_blocks=118
[SCHED] STEP seq=1 | phase=PREFILL | token=... | num_tokens=13 | cached=12 | status→RUNNING
[SCHED] STEP seq=0 | phase=DECODE | token=... | num_tokens=9 | cached=8 | status→RUNNING
...
[SCHED] STEP seq=0 | phase=DECODE | token=... | num_tokens=71 | cached=70 | status→FINISHED
[BLOCK] DEALLOCATE seq=0 | block_table=[0, 2, 3]
...
```

## 观察要点

| 日志前缀             | 观察内容                                                                                       |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| `[SEQ] CREATED`      | Sequence 何时创建 (WAITING 状态)，num_tokens/num_blocks                                        |
| `[BLOCK] ALLOCATE`   | Block 分配详情: cached_blocks (Prefix Cache 命中数)、new_blocks、block_table、free_blocks 变化 |
| `[SCHED] STEP`       | Prefill/Decode 交替执行，num_tokens 和 cached 的推进                                           |
| `[BLOCK] DEALLOCATE` | Sequence 完成或 Preemption 时的 Block 回收                                                     |
| `[SCHED] PREEMPT`    | 显存不足时的抢占 (调低 `--gpu-memory-utilization` 更容易观察)                                  |
