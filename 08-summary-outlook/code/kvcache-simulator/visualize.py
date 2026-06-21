#!/usr/bin/env python3
"""实验可视化脚本

使用 matplotlib 生成大作业报告的图表。

TODO: 根据你的实验结果, 修改数据并生成以下图表:
  1. KV Cache 跨模型对比 (柱状图)
  2. 不同精度的并发容量对比 (分组柱状图)
  3. PagedAttention vs Naive 碎片率对比 (饼图或柱状图)
  4. Prefix Cache 命中率 vs 容量 (折线图)
"""

import matplotlib
matplotlib.use("Agg")  # 无 GUI 后端
import matplotlib.pyplot as plt
import numpy as np

# ═══════════════════════════════════════════════════════════
# 图表 1: 跨模型 KV Cache 对比
# ═══════════════════════════════════════════════════════════

def plot_model_comparison():
    """不同模型在 seq_len=4096, batch=8, FP16 下的 KV Cache 对比"""
    # TODO: 用你的 calculator.py 计算结果替换下面的示例数据
    models = ["Qwen2.5\n0.5B", "Qwen2.5\n7B", "Llama-3\n8B", "Qwen2.5\n72B", "Llama-3\n70B"]
    kv_cache_gb = [0.38, 3.6, 8.2, 20.5, 20.5]  # ← 替换为实际计算结果
    model_weights_gb = [1.0, 14.0, 16.0, 144.0, 140.0]  # ← 替换

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    bars1 = ax.bar(x - width/2, model_weights_gb, width, label="Model Weights", color="#3b82f6")
    bars2 = ax.bar(x + width/2, kv_cache_gb, width, label="KV Cache (seq=4096, batch=8)", color="#f97316")

    ax.set_ylabel("Memory (GB)")
    ax.set_title("KV Cache vs Model Weights Across Models (FP16)")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    # 标注数值
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{bar.get_height():.0f}", ha="center", fontsize=8)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{bar.get_height():.1f}", ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig("1_model_comparison.png", dpi=150)
    print("[OK] 1_model_comparison.png")

# ═══════════════════════════════════════════════════════════
# 图表 2: 精度 vs 并发容量
# ═══════════════════════════════════════════════════════════

def plot_precision_vs_concurrency():
    """不同精度下 Qwen2.5-7B 的最大并发数 (seq_len=4096, H100 80GB)"""
    # TODO: 替换为实际计算结果
    precisions = ["FP16", "FP8", "INT8", "INT4"]
    max_batch = [24, 48, 48, 96]  # ← 替换 (FP8 和 INT8 都是 1 byte)
    kv_per_req = [1.75, 0.88, 0.88, 0.44]  # GB per request ← 替换

    fig, ax1 = plt.subplots(figsize=(8, 5))

    bars = ax1.bar(precisions, max_batch, color=["#ef4444", "#f97316", "#eab308", "#22c55e"])
    ax1.set_ylabel("Max Concurrent Requests", color="#1e293b")
    ax1.set_ylim(0, max(max_batch) * 1.2)

    ax2 = ax1.twinx()
    ax2.plot(precisions, kv_per_req, "D-", color="#3b82f6", linewidth=2, markersize=10)
    ax2.set_ylabel("KV Cache per Request (GB)", color="#3b82f6")

    ax1.set_title("Max Concurrency vs KV Cache Precision (Qwen2.5-7B, seq=4096, H100 80GB)")

    for bar, val in zip(bars, max_batch):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(val), ha="center", fontweight="bold")

    plt.tight_layout()
    plt.savefig("2_precision_vs_concurrency.png", dpi=150)
    print("[OK] 2_precision_vs_concurrency.png")

# ═══════════════════════════════════════════════════════════
# 图表 3: PagedAttention vs Naive 碎片率
# ═══════════════════════════════════════════════════════════

def plot_fragmentation():
    """PagedAttention vs Naive 碎片率对比"""
    # TODO: 用你的 simulator.py 结果替换
    categories = ["Used", "Internal\nFrag", "External\nFrag"]
    naive_values = [25, 60, 15]   # ← 替换
    pa_values = [96, 4, 0]         # ← 替换

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width/2, naive_values, width, label="Naive (Pre-allocation)", color="#ef4444")
    ax.bar(x + width/2, pa_values, width, label="PagedAttention", color="#22c55e")

    ax.set_ylabel("Memory Distribution (%)")
    ax.set_title("KV Cache Memory Fragmentation: Naive vs PagedAttention")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig("3_fragmentation.png", dpi=150)
    print("[OK] 3_fragmentation.png")

# ═══════════════════════════════════════════════════════════
# 图表 4: Prefix Cache 命中率 vs 容量
# ═══════════════════════════════════════════════════════════

def plot_cache_hit_rate():
    """Prefix Cache 命中率随 Cache 容量的变化"""
    # TODO: 用你的 lru_cache.py 结果替换
    capacities = [500, 1000, 2000, 5000, 10000]
    hit_rates = [0.35, 0.58, 0.78, 0.92, 0.97]  # ← 替换

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(capacities, hit_rates, "o-", color="#8b5cf6", linewidth=2, markersize=8)
    ax.set_xlabel("Cache Capacity (blocks)")
    ax.set_ylabel("Hit Rate")
    ax.set_title("Prefix Cache Hit Rate vs Cache Capacity")
    ax.set_xscale("log")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)

    for cap, rate in zip(capacities, hit_rates):
        ax.annotate(f"{rate:.0%}", (cap, rate), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=9)

    plt.tight_layout()
    plt.savefig("4_cache_hit_rate.png", dpi=150)
    print("[OK] 4_cache_hit_rate.png")

# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating experiment charts...\n")

    plot_model_comparison()
    plot_precision_vs_concurrency()
    plot_fragmentation()
    plot_cache_hit_rate()

    print("\nDone. Add these charts to your REPORT.md.")
