#!/usr/bin/env python3
"""Estimate LLM inference memory usage for MHA/GQA models.

Supports any dense model with MHA or GQA attention (Qwen2.5, Llama-3, etc.).
本脚本纯 Python 零依赖，在笔记本/台式机上即可运行 (不需要 GPU)。
模块 6 的 vLLM + LMCache 实验部分仍需 GPU (≥ 8 GB)。

Examples:
    # Qwen3-0.6B (default)
    python calculate_qwen3_memory.py

    # Llama-3-8B on 80GB GPU
    python calculate_qwen3_memory.py --L 32 --H_kv 8 --head-dim 128 \\
        --params 8.0 --gpu-mem-gib 80

    # Qwen2.5-7B on H100 80GB with custom scenarios
    python calculate_qwen3_memory.py --L 28 --H_kv 4 --head-dim 128 \\
        --params 7.0 --gpu-mem-gib 80 --scenarios 2048 4096 8192 32768

    # Qwen2.5-72B with FP8 KV Cache
    python calculate_qwen3_memory.py --L 80 --H_kv 8 --head-dim 128 \\
        --params 72.0 --gpu-mem-gib 80 --kv-bytes 1 --num-gpus 2
"""

import argparse


def format_size(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} Bytes"
    elif bytes_val < 1024 ** 2:
        return f"{bytes_val / 1024:.2f} KiB"
    elif bytes_val < 1024 ** 3:
        return f"{bytes_val / 1024 ** 2:.2f} MiB"
    else:
        return f"{bytes_val / 1024 ** 3:.2f} GiB"


def parse_args():
    p = argparse.ArgumentParser(
        description="Estimate LLM inference memory for MHA/GQA models.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python %(prog)s
  python %(prog)s --L 32 --H_kv 8 --head-dim 128 --params 8.0 --gpu-mem-gib 80
  python %(prog)s --L 80 --H_kv 8 --head-dim 128 --params 72.0 --gpu-mem-gib 80 --num-gpus 2
        """,
    )
    # Model config
    p.add_argument("--L", type=int, default=28, help="num_hidden_layers (default: 28, Qwen3-0.6B)")
    p.add_argument("--H_kv", type=int, default=8, help="num_key_value_heads (default: 8)")
    p.add_argument("--head-dim", type=int, default=64, help="head_dim = hidden_size / num_attention_heads (default: 64, Qwen3-0.6B)")
    p.add_argument("--params", type=float, default=0.6, help="Model params in billions (default: 0.6)")
    p.add_argument("--kv-bytes", type=float, default=2, help="KV Cache dtype bytes: FP16/BF16=2, FP8=1, INT8=1 (default: 2)")
    # Hardware config
    p.add_argument("--gpu-mem-gib", type=float, default=40.0, help="GPU memory budget in GiB (default: 40)")
    p.add_argument("--overhead-gib", type=float, default=1.4, help="Reserved overhead in GiB: CUDA context + activations + fragmentation (default: 1.4)")
    p.add_argument("--num-gpus", type=int, default=1, help="Number of GPUs for tensor parallelism (default: 1)")
    # Scenario config
    p.add_argument("--scenarios", type=int, nargs="*", default=[512, 4096, 32768], help="Sequence lengths to estimate max concurrency for (default: 512 4096 32768)")
    # Presets
    p.add_argument("--preset", choices=["qwen3-0.6b", "qwen2.5-7b", "qwen2.5-72b", "llama3-8b", "llama3-70b"],
                   help="Use a preset model configuration (overrides --L --H_kv --head-dim --params)")
    return p.parse_args()


PRESETS = {
    # head_dim = hidden_size / num_attention_heads (for KV cache formula)
    # Note: HuggingFace config.json "head_dim" may differ from KV-cache head_dim.
    #   Qwen3-0.6B config.json has head_dim=128, but KV-cache uses 1024/16=64.
    "qwen3-0.6b":   {"L": 28, "H_kv": 8,  "head_dim": 64,  "params": 0.6,  "name": "Qwen3-0.6B"},
    "qwen2.5-7b":   {"L": 28, "H_kv": 4,  "head_dim": 128, "params": 7.0,  "name": "Qwen2.5-7B"},
    "qwen2.5-72b":  {"L": 80, "H_kv": 8,  "head_dim": 128, "params": 72.0, "name": "Qwen2.5-72B"},
    "llama3-8b":    {"L": 32, "H_kv": 8,  "head_dim": 128, "params": 8.0,  "name": "Llama-3-8B"},
    "llama3-70b":   {"L": 80, "H_kv": 8,  "head_dim": 128, "params": 70.0, "name": "Llama-3-70B"},
}


def validate_args(args):
    """Validate numerical arguments to prevent division-by-zero or negative memory."""
    if args.L <= 0 or args.H_kv <= 0 or args.head_dim <= 0:
        raise ValueError("L, H_kv, and head_dim must be positive")
    if args.kv_bytes <= 0:
        raise ValueError("kv_bytes must be positive")
    if args.num_gpus < 1:
        raise ValueError("num_gpus must be at least 1")
    if args.gpu_mem_gib <= args.overhead_gib:
        raise ValueError(
            f"gpu_mem_gib ({args.gpu_mem_gib}) must exceed overhead_gib ({args.overhead_gib})"
        )


def calculate_memory(args):
    validate_args(args)
    # Apply preset if specified
    if args.preset:
        preset = PRESETS[args.preset]
        L = preset["L"]
        H_kv = preset["H_kv"]
        head_dim = preset["head_dim"]
        params_B = preset["params"]
        model_name = preset["name"]
    else:
        L = args.L
        H_kv = args.H_kv
        head_dim = args.head_dim
        params_B = args.params
        model_name = f"Custom (L={L}, H_kv={H_kv}, head_dim={head_dim})"

    b_kv = args.kv_bytes
    param_count = params_B * 10 ** 9

    print(f"--- Analysis for {model_name} ---")
    print(f"Config: L={L}, H_kv={H_kv}, head_dim={head_dim}, "
          f"params={params_B}B, kv_dtype={'FP8' if b_kv == 1 else 'FP16/BF16'}")
    if args.num_gpus > 1:
        print(f"GPUs: {args.num_gpus} (TP={args.num_gpus})")

    # 1. Model Weights
    b_w = 2  # BF16/FP16 weights
    mem_weights = param_count * b_w
    mem_weights_per_gpu = mem_weights / args.num_gpus
    print(f"\n1. Model Weights:")
    print(f"   Total:     {format_size(mem_weights)}")
    if args.num_gpus > 1:
        print(f"   Per GPU:   {format_size(mem_weights_per_gpu)} (TP={args.num_gpus})")

    # 2. KV Cache Per Token
    # Formula: 2 (K+V) × L × H_kv × head_dim × kv_bytes
    kv_per_token = 2 * b_kv * L * H_kv * head_dim
    print(f"\n2. KV Cache Per Token:")
    print(f"   Formula: 2 × {b_kv:.0f} × {L} × {H_kv} × {head_dim}")
    print(f"   Value:   {kv_per_token:,.0f} Bytes")
    print(f"   ≈        {format_size(kv_per_token)}")

    print(f"   (GQA: {H_kv} KV heads — vs MHA would be proportionally larger)")

    # 3. GPU Memory Budget
    gpu_mem_total = args.gpu_mem_gib * 1024 ** 3
    mem_overhead = args.overhead_gib * 1024 ** 3
    mem_available_per_gpu = gpu_mem_total - mem_weights_per_gpu - mem_overhead

    print(f"\n3. GPU Budget (per GPU: {format_size(gpu_mem_total)})")
    print(f"   - Model weights:  {format_size(mem_weights_per_gpu)}")
    print(f"   - Overhead:       {format_size(mem_overhead)}")
    print(f"   = Available:      {format_size(mem_available_per_gpu)}")

    # Under TP, KV heads are sharded: each GPU stores H_kv/num_gpus
    kv_per_token_per_gpu = kv_per_token / args.num_gpus
    max_tokens = mem_available_per_gpu / kv_per_token_per_gpu
    print(f"   KV-per-token (per GPU): {format_size(kv_per_token_per_gpu)}")
    print(f"   Max tokens (per GPU):   {max_tokens:,.0f}")

    # 4. Scenarios
    scenarios = args.scenarios
    print(f"\n4. Max Concurrency (B_max) for different Sequence Lengths (S):")
    if args.num_gpus > 1:
        print(f"   (TP={args.num_gpus}: KV sharded, per-GPU KV cost = {format_size(kv_per_token_per_gpu)}/token)")
    print(f"   {'S':<10} {'B_max':>10} {'KV Cache/req':>18} {'Total KV':>18}")
    print(f"   {'-'*10} {'-'*10} {'-'*18} {'-'*18}")
    for S in scenarios:
        kv_per_req = kv_per_token_per_gpu * S
        b_max = int(max_tokens / S)
        total_kv = kv_per_req * b_max
        print(f"   {S:<10} {b_max:>10} {format_size(kv_per_req):>18} {format_size(total_kv):>18}")

    # 5. Impact of quantization
    if b_kv == 2:
        kv_fp8 = kv_per_token_per_gpu // 2
        max_tokens_fp8 = mem_available_per_gpu / kv_fp8
        print(f"\n5. Impact of FP8 KV Cache:")
        print(f"   FP8 per token: {format_size(kv_fp8)} (vs FP16: {format_size(kv_per_token)})")
        print(f"   FP8 max tokens: {max_tokens_fp8:,.0f} (vs FP16: {max_tokens:,.0f})")
        print(f"   → FP8 doubles your concurrent capacity")
        for S in scenarios[:2]:
            print(f"   S={S}: B_max FP16={int(max_tokens/S)}, FP8={int(max_tokens_fp8/S)}")


if __name__ == "__main__":
    calculate_memory(parse_args())
