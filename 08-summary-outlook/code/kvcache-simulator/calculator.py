#!/usr/bin/env python3
"""KV Cache 显存计算工具骨架

运行: python calculator.py --preset qwen2.5-7b --seq-len 4096 --batch 8
      python calculator.py --L 32 --H_kv 8 --head-dim 128 --dtype fp16 --seq-len 4096 --batch 8

参考: 模块 6 code/calculate_qwen3_memory.py (需独立实现, 不可直接复制)
"""

import argparse
import sys

# ═══════════════════════════════════════════════════════════
# 模型预设
# ═══════════════════════════════════════════════════════════
PRESETS = {
    "qwen2.5-0.5b":  {"L": 24, "H_kv": 2,  "head_dim": 64,  "params_B": 0.5,  "name": "Qwen2.5-0.5B"},
    "qwen2.5-7b":    {"L": 28, "H_kv": 4,  "head_dim": 128, "params_B": 7.0,  "name": "Qwen2.5-7B"},
    "qwen2.5-72b":   {"L": 80, "H_kv": 8,  "head_dim": 128, "params_B": 72.0, "name": "Qwen2.5-72B"},
    "llama3-8b":     {"L": 32, "H_kv": 8,  "head_dim": 128, "params_B": 8.0,  "name": "Llama-3-8B"},
    "llama3-70b":    {"L": 80, "H_kv": 8,  "head_dim": 128, "params_B": 70.0, "name": "Llama-3-70B"},
    # TODO: 添加 DeepSeek-V3 MLA 预设 (提示: H_kv=1, head_dim=512, params_B=671, 但每 token 仅激活 ~37B)
}

# dtype → bytes 映射
DTYPE_BYTES = {"fp16": 2, "fp8": 1, "int8": 1, "int4": 0.5}

# ═══════════════════════════════════════════════════════════
# TODO 1: KV Cache 计算函数
# ═══════════════════════════════════════════════════════════
def calc_kv_cache(L, H_kv, head_dim, n_tokens, dtype_bytes):
    """计算 KV Cache 大小

    公式: 2 × L × H_kv × head_dim × n_tokens × dtype_bytes

    参数:
        L:           num_hidden_layers
        H_kv:        num_key_value_heads (GQA)
        head_dim:    head_dimension (hidden_size / num_attention_heads)
        n_tokens:    总 token 数 (prompt + generated)
        dtype_bytes: 每元素字节数 (FP16=2, FP8=1, INT8=1, INT4=0.5)

    返回:
        KV Cache 大小 (bytes)
    """
    # TODO: 实现公式
    return 0  # ← 替换为正确实现

# ═══════════════════════════════════════════════════════════
# TODO 2: 格式化输出
# ═══════════════════════════════════════════════════════════
def format_size(bytes_val):
    """将字节数格式化为人类可读的字符串"""
    if bytes_val < 1024:
        return f"{bytes_val:.0f} B"
    elif bytes_val < 1024**2:
        return f"{bytes_val/1024:.2f} KiB"
    elif bytes_val < 1024**3:
        return f"{bytes_val/1024**2:.2f} MiB"
    else:
        return f"{bytes_val/1024**3:.2f} GiB"

# ═══════════════════════════════════════════════════════════
# TODO 3: 主计算逻辑
# ═══════════════════════════════════════════════════════════
def calculate(args):
    """主计算函数"""
    # 解析模型配置
    if args.preset:
        preset = PRESETS[args.preset]
        L, H_kv, head_dim, params_B, name = (
            preset["L"], preset["H_kv"], preset["head_dim"],
            preset["params_B"], preset["name"]
        )
    else:
        L, H_kv, head_dim, params_B = args.L, args.H_kv, args.head_dim, args.params
        name = f"Custom (L={L}, H_kv={H_kv}, head_dim={head_dim})"

    dtype_bytes = DTYPE_BYTES[args.dtype]

    print(f"=== {name} ===")
    print(f"L={L}, H_kv={H_kv}, head_dim={head_dim}, dtype={args.dtype}\n")

    # 1. 模型权重
    model_weight = params_B * 1e9 * 2  # BF16/FP16 = 2 bytes per param
    print(f"1. Model Weights: {format_size(model_weight)}")

    # 2. KV Cache
    # TODO: 对于每个预设模型, 计算不同 seq_len 和 batch 下的 KV Cache
    # 提示: n_tokens = seq_len × batch (简化, 假设所有请求长度相同)
    print(f"\n2. KV Cache per Token: ", end="")
    kv_per_token = calc_kv_cache(L, H_kv, head_dim, 1, dtype_bytes)
    print(f"{format_size(kv_per_token)}")

    # TODO: 输出表格 — 不同 seq_len × batch 的 KV Cache
    print(f"\n3. KV Cache Table ({args.dtype}):")
    print(f"   {'seq_len':<10} {'batch':<8} {'KV Cache':<15} {'+Model':<15} {'Total':<15}")
    print(f"   {'-'*10} {'-'*8} {'-'*15} {'-'*15} {'-'*15}")
    for seq_len in [2048, 4096, 8192, 32768]:
        for batch in [1, 8, 32]:
            # TODO: 计算 KV Cache + 模型权重 + 总显存
            kv = 0  # ← 替换
            total = 0  # ← 替换
            print(f"   {seq_len:<10} {batch:<8} {format_size(kv):<15} {format_size(model_weight):<15} {format_size(total):<15}")

    # TODO 4: 不同精度对比 (FP16 vs FP8 vs INT8 vs INT4)
    # TODO: 输出并发容量对比表

    # TODO 5 (选做): GQA vs MHA 对比
    # 对于 Llama-3-70B: H_kv=8 (GQA) vs H_kv=64 (MHA)
    # 展示 GQA 省了多少 KV Cache

def main():
    parser = argparse.ArgumentParser(description="KV Cache Memory Calculator")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Model preset")
    parser.add_argument("--L", type=int, help="num_hidden_layers")
    parser.add_argument("--H_kv", type=int, help="num_key_value_heads")
    parser.add_argument("--head-dim", type=int, help="head dimension")
    parser.add_argument("--params", type=float, help="Model params (billions)")
    parser.add_argument("--dtype", choices=list(DTYPE_BYTES.keys()), default="fp16")
    parser.add_argument("--seq-len", type=int, default=4096)
    parser.add_argument("--batch", type=int, default=1)
    args = parser.parse_args()

    if not args.preset and not (args.L and args.H_kv and args.head_dim and args.params):
        parser.error("Either --preset or --L/--H_kv/--head-dim/--params is required")

    calculate(args)

if __name__ == "__main__":
    main()
