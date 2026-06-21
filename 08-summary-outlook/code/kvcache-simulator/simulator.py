#!/usr/bin/env python3
"""PagedAttention 碎片模拟器骨架

模拟 100 个并发请求的生命周期，对比 Naive vs PagedAttention 的显存利用率。

运行: python simulator.py --requests 100 --block-size 16 --gpu-mem-gb 40
"""

import argparse
import random
from dataclasses import dataclass, field
from typing import List, Optional

# ═══════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class Request:
    """一个推理请求"""
    req_id: int
    prompt_len: int          # prompt token 数
    output_len: int          # 实际生成的 token 数
    max_tokens: int           # 预分配的上限 (= output_len + margin)
    arrival_time: float      # 到达时间 (秒)
    completion_time: float = 0  # 完成时间 (模拟结束后填入)

@dataclass
class Block:
    """KV Cache Block (PagedAttention)"""
    block_id: int
    in_use: bool = False
    ref_count: int = 0

# ═══════════════════════════════════════════════════════════
# TODO 1: Naive 方案 — 预分配连续空间
# ═══════════════════════════════════════════════════════════

class NaiveManager:
    """预分配 max_tokens 连续 KV Cache 的简单方案

    模拟 HuggingFace Transformers 的做法:
    - 请求到达时立即分配 max_tokens × kv_per_token 的连续空间
    - 请求结束后释放整块
    - 如果找不到足够大的连续空间 → 拒绝请求 (或等待)
    """

    def __init__(self, total_tokens: int):
        """
        Args:
            total_tokens: GPU 总共能存储的 KV token 数
                          = (HBM_size - model_weights) / kv_per_token
        """
        self.total_tokens = total_tokens
        self.free_intervals = [(0, total_tokens)]  # (start, end) 空闲区间列表
        self.allocations = {}  # req_id → (start, end)

    def allocate(self, req: Request) -> bool:
        """为请求分配 max_tokens 的连续空间

        Returns:
            True 如果分配成功, False 如果空间不足
        """
        needed = req.max_tokens
        # TODO: 在 free_intervals 中找到第一个 ≥ needed 的空闲区间
        # TODO: 从该区间切割出 needed 大小, 更新 free_intervals
        # TODO: 记录到 self.allocations[req.req_id] = (start, start+needed)
        return False  # ← 替换

    def deallocate(self, req: Request):
        """释放请求占用的空间"""
        if req.req_id in self.allocations:
            # TODO: 将 (start, end) 归还到 free_intervals
            # TODO: 合并相邻的空闲区间 (关键: 不合并会导致外部碎片)
            del self.allocations[req.req_id]

    def stats(self):
        """计算碎片统计"""
        used = sum(end - start for start, end in self.allocations.values())
        # 内部碎片: 预分配但未实际使用的 token
        internal_frag = sum(
            (end - start) - self._find_request(req_id).output_len
            for req_id, (start, end) in self.allocations.items()
            if self._find_request(req_id)
        ) if self.allocations else 0
        # TODO: 计算外部碎片 (空闲但无法被最大等待请求使用的小空隙)
        return {
            "total_tokens": self.total_tokens,
            "used": used,
            "utilization": used / self.total_tokens if self.total_tokens else 0,
            "internal_frag": internal_frag,
            "external_frag": 0,  # TODO
        }

    def _find_request(self, req_id):
        return None  # TODO

# ═══════════════════════════════════════════════════════════
# TODO 2: PagedAttention 方案 — Block 管理
# ═══════════════════════════════════════════════════════════

class PagedAttentionManager:
    """PagedAttention 的 Block 管理器

    核心:
    - Block 大小固定 (如 16 tokens)
    - 按需分配: 请求到达时只分配 prompt_len 对应的 Block
    - 逐 Block 追加: 生成过程中按需追加 Block
    - ref_count: 多个请求可共享同一 Block (Prefix Cache)
    """

    def __init__(self, total_tokens: int, block_size: int = 16):
        self.block_size = block_size
        self.num_blocks = total_tokens // block_size
        self.blocks = [Block(i) for i in range(self.num_blocks)]
        self.free_block_ids = list(range(self.num_blocks))
        self.block_tables = {}  # req_id → [block_id, ...]

    def allocate(self, req: Request) -> bool:
        """按需分配 Block (只分配 prompt_len 的 Block)

        Returns:
            True 如果分配成功, False 如果 Block 不够
        """
        needed = (req.prompt_len + self.block_size - 1) // self.block_size
        # TODO: 从 free_block_ids 取 needed 个 Block
        # TODO: 记录到 self.block_tables[req.req_id] = [...]
        return False  # ← 替换

    def append(self, req: Request) -> bool:
        """追加 1 个 Block (Decode 阶段每次生成 block_size 个 token 后调用)"""
        # TODO: 检查 free_block_ids 是否为空
        # TODO: 分配 1 个 Block, 追加到 block_table
        return False  # ← 替换

    def deallocate(self, req: Request):
        """释放请求占用的所有 Block"""
        # TODO: 遍历 block_table, 将 Block 的 ref_count 减 1
        # TODO: ref_count == 0 时回收 Block 到 free_block_ids
        pass

    def stats(self):
        """计算碎片统计"""
        used_blocks = self.num_blocks - len(self.free_block_ids)
        used_tokens = used_blocks * self.block_size
        # 内部碎片: 最后一个 Block 中未使用的 token
        internal_frag = 0  # TODO: 遍历所有请求, 计算每个请求最后 Block 的浪费
        return {
            "total_blocks": self.num_blocks,
            "used_blocks": used_blocks,
            "free_blocks": len(self.free_block_ids),
            "utilization": used_tokens / (self.num_blocks * self.block_size),
            "internal_frag": internal_frag,
            "external_frag": 0,  # PagedAttention 无外部碎片!
        }

# ═══════════════════════════════════════════════════════════
# TODO 3: 事件模拟循环
# ═══════════════════════════════════════════════════════════

def generate_requests(num: int, seed: int = 42) -> List[Request]:
    """生成随机请求序列"""
    random.seed(seed)
    requests = []
    for i in range(num):
        req = Request(
            req_id=i,
            prompt_len=random.randint(100, 2000),
            output_len=random.randint(50, 500),
            max_tokens=0,  # 由管理器决定: Naive = output_len + 512 margin, PA = 按需
            arrival_time=random.uniform(0, 100),  # 100 秒内随机到达
        )
        req.max_tokens = req.output_len + 512  # Naive 方案用
        requests.append(req)
    return sorted(requests, key=lambda r: r.arrival_time)

def run_simulation(requests: List[Request], manager) -> dict:
    """运行离散事件模拟"""
    # TODO: 按到达时间处理请求
    #   1. 处理已完成请求 (deallocate)
    #   2. 处理新到达请求 (allocate)
    #   3. 模拟生成过程 (每个 step 生成 1 token, 每 block_size tokens 调用 append)
    #   4. 记录峰值显存
    # 简化: 不考虑实际生成时间, 只统计分配/释放的显存变化
    return manager.stats()

# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="PagedAttention Fragmentation Simulator")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--block-size", type=int, default=16)
    parser.add_argument("--gpu-mem-gb", type=float, default=40.0)
    parser.add_argument("--kv-per-token", type=int, default=57344,
                        help="KV Cache bytes per token (Qwen2.5-7B FP16: 57344)")
    args = parser.parse_args()

    # 计算 GPU 可存储的总 token 数 (扣除模型权重)
    model_weight = 14e9  # Qwen2.5-7B ≈ 14 GB
    kv_mem_available = (args.gpu_mem_gb * 1e9 - model_weight)
    total_tokens = int(kv_mem_available / args.kv_per_token)

    print(f"GPU Memory: {args.gpu_mem_gb} GB")
    print(f"KV memory available: {kv_mem_available / 1e9:.2f} GB")
    print(f"Total KV tokens: {total_tokens:,}")
    print(f"Block size: {args.block_size}")

    # 生成随机请求
    requests = generate_requests(args.requests)

    # TODO: 运行 Naive 方案
    # naive = NaiveManager(total_tokens)
    # naive_stats = run_simulation(requests, naive)

    # TODO: 运行 PagedAttention 方案
    # pa = PagedAttentionManager(total_tokens, args.block_size)
    # pa_stats = run_simulation(requests, pa)

    # TODO: 对比输出
    # print("\n=== Naive ===")
    # print(naive_stats)
    # print("\n=== PagedAttention ===")
    # print(pa_stats)

    print("\n[TODO] 实现 run_simulation 和两种 Manager 后, 取消上面的注释")

if __name__ == "__main__":
    main()
