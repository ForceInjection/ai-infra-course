# 模块 6 配套代码 — KV Cache 显存计算脚本

## 文件说明

| 文件                              | 内容                                                   | 对应 PPT             | 来源                           |
| --------------------------------- | ------------------------------------------------------ | -------------------- | ------------------------------ |
| `calculate_qwen3_memory.py`       | 通用 GQA/MHA 模型显存估算器                            | 第 6–7 页 [手算]     | [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/memory_calc/) |
| `calculate_deepseek_v4_memory.py` | DeepSeek V4 专用估算器 (K=V共享/MLA/Indexer Cache/MoE) | 第 8 页 [跨模型对比] | [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/memory_calc/) |
| `qwen3_06b_config.json`           | Qwen3-0.6B 模型配置样例                                | —                    | HuggingFace config.json        |
| `deepseek_v4_pro_config.json`     | DeepSeek V4 Pro 配置样例                               | —                    | HuggingFace config.json        |

## 环境要求

- Python ≥ 3.8 (零依赖，仅使用标准库)

## 运行方法

### 通用 GQA 模型 (Qwen3 / Llama-3 / Qwen2.5 等)

```bash
# 使用预设模型 (推荐)
python calculate_qwen3_memory.py --preset qwen2.5-7b --gpu-mem-gib 80
python calculate_qwen3_memory.py --preset llama3-8b --gpu-mem-gib 80
python calculate_qwen3_memory.py --preset qwen2.5-72b --gpu-mem-gib 80 --num-gpus 2
python calculate_qwen3_memory.py --preset llama3-70b --gpu-mem-gib 80 --num-gpus 4

# 自定义序列长度场景
python calculate_qwen3_memory.py --preset qwen2.5-7b \
    --gpu-mem-gib 80 --scenarios 2048 4096 8192 32768

# FP8 KV Cache 效果
python calculate_qwen3_memory.py --preset qwen2.5-72b \
    --gpu-mem-gib 80 --num-gpus 2 --kv-bytes 1

# 自定义模型参数
python calculate_qwen3_memory.py \
    --L 32 --H_kv 8 --head-dim 128 --params 8.0 \
    --gpu-mem-gib 80 --scenarios 2048 8192 32768

# 列出所有预设
python calculate_qwen3_memory.py --help
```

**预设模型**: `qwen3-0.6b`, `qwen2.5-7b`, `qwen2.5-72b`, `llama3-8b`, `llama3-70b`

### DeepSeek V4 系列

```bash
# 使用本地 config.json
python calculate_deepseek_v4_memory.py \
    --config deepseek_v4_pro_config.json \
    --gpu-mem-gib 80 \
    --num-gpus 8

# 自动从 HuggingFace 下载 config.json
python calculate_deepseek_v4_memory.py \
    --gpu-mem-gib 80 \
    --num-gpus 8
```

## 预期输出

```text
$ python calculate_qwen3_memory.py --preset qwen2.5-7b --gpu-mem-gib 80 --scenarios 2048 8192 32768

--- Analysis for Qwen2.5-7B ---
Config: L=28, H_kv=4, head_dim=128, params=7.0B, kv_dtype=FP16/BF16

1. Model Weights:
   Total:     13.04 GiB

2. KV Cache Per Token:
   Formula: 2 × 2 × 28 × 4 × 128
   Value:   57,344 Bytes
   ≈        56.00 KiB

3. GPU Budget (per GPU: 80.00 GiB)
   - Model weights:  13.04 GiB
   - Overhead:       1.40 GiB
   = Available:      65.56 GiB
   Max tokens (total, single GPU): 1,227,611

4. Max Concurrency (B_max) for different Sequence Lengths (S):
   S               B_max       KV Cache/req           Total KV
   ---------- ---------- ------------------ ------------------
   2048              599         112.00 MiB          65.52 GiB
   8192              149         448.00 MiB          65.19 GiB
   32768              37           1.75 GiB          64.75 GiB

5. Impact of FP8 KV Cache:
   FP8 per token: 28.00 KiB (vs FP16: 56.00 KiB)
   FP8 max tokens: 2,455,221 (vs FP16: 1,227,611)
   → FP8 doubles your concurrent capacity
```

## 课堂使用

PPT 第 6–9 页手算练习后，用脚本验证：

| PPT 页  | 内容             | 命令                                                                                   |
| ------- | ---------------- | -------------------------------------------------------------------------------------- |
| 第 6 页 | 手算 Qwen2.5-7B  | `python calculate_qwen3_memory.py --preset qwen2.5-7b --gpu-mem-gib 80`                |
| 第 7 页 | 手算 Qwen2.5-72B | `python calculate_qwen3_memory.py --preset qwen2.5-72b --gpu-mem-gib 80 --num-gpus 2`  |
| 第 8 页 | 跨模型对比       | `python calculate_qwen3_memory.py --preset llama3-8b --gpu-mem-gib 80` + DeepSeek 脚本 |
| 第 9 页 | FP8 效果         | `--kv-bytes 1` 参数对比                                                                |
