#!/usr/bin/env python3
"""Prefix Cache LRU 命中率模拟器

模拟 200 个带不同 System Prompt 的请求, 统计不同 Cache 容量下的命中率。

运行: python lru_cache.py --requests 200 --capacity 1000 --block-size 16
"""

import argparse
import hashlib
import random
from collections import OrderedDict
from dataclasses import dataclass

# ═══════════════════════════════════════════════════════════
# TODO 1: 链式哈希 (参考模块 5 BlockManager)
# ═══════════════════════════════════════════════════════════

def chain_hash(tokens: list, prefix_hash: int = 0) -> int:
    """计算 Block 的链式哈希

    每个 Block 的 hash 依赖前一个 Block 的 hash (prefix_hash),
    形成链: Block[0] → Block[1] → Block[2] → ...

    这样保证了: 相同 prefix → 完全相同的 hash 链 → 不会错误共享
    """
    # TODO: 使用 hashlib.sha256 或 xxhash 实现链式哈希
    # h = hashlib.sha256()
    # h.update(prefix_hash.to_bytes(8, 'little'))
    # for token in tokens:
    #     h.update(token.to_bytes(4, 'little'))
    # return int.from_bytes(h.digest()[:8], 'little')
    return 0  # ← 替换

# ═══════════════════════════════════════════════════════════
# TODO 2: LRU Cache
# ═══════════════════════════════════════════════════════════

class LRUCache:
    """LRU (Least Recently Used) Cache 模拟器

    每个 Cache 条目 = (block_hash → 是否命中)
    容量满时淘汰最久未使用的条目
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()  # hash → timestamp (或任意值)
        self.hits = 0
        self.misses = 0

    def access(self, block_hash: int) -> bool:
        """访问一个 Block hash, 返回是否命中"""
        # TODO: 如果 hash 在 cache 中:
        #   - 移动到 OrderedDict 末尾 (标记为最近使用)
        #   - hits += 1
        #   - 返回 True
        # TODO: 如果不在:
        #   - 如果 cache 满: 淘汰最旧的条目 (OrderedDict.popitem(last=False))
        #   - 添加新条目
        #   - misses += 1
        #   - 返回 False
        return False  # ← 替换

    @property
    def hit_rate(self):
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

# ═══════════════════════════════════════════════════════════
# TODO 3: 请求生成与模拟
# ═══════════════════════════════════════════════════════════

@dataclass
class SimRequest:
    """模拟请求"""
    req_id: int
    system_prompt_len: int    # System Prompt 长度 (tokens)
    system_prompt_hash: int   # System Prompt 的 hash (简化: 用随机种子代替)
    blocks: list              # System Prompt 的 Block hash 列表

def generate_requests(num: int, block_size: int = 16, seed: int = 42) -> list:
    """生成模拟请求

    将 200 个请求分为 4 组, 每组共享不同的 System Prompt 长度:
    - 组 1: 256 tokens  (16 blocks)
    - 组 2: 512 tokens  (32 blocks)
    - 组 3: 1024 tokens (64 blocks)
    - 组 4: 2048 tokens (128 blocks)
    """
    random.seed(seed)
    requests = []
    groups = [256, 512, 1024, 2048]
    per_group = num // len(groups)

    for g_idx, prompt_len in enumerate(groups):
        # TODO: 为每组生成唯一的 base_hash (模拟相同的 System Prompt)
        base_hash = random.randint(0, 2**63 - 1)
        num_blocks = prompt_len // block_size

        for i in range(per_group):
            # TODO: 生成每个请求的 Block hash 链
            # 同一组的请求共享相同的 System Prompt → 前 num_blocks 个 hash 相同
            # 后面是不同的 user prompt → hash 不同
            blocks = []
            # 共享的 System Prompt blocks
            for b in range(num_blocks):
                blocks.append(chain_hash([base_hash, b], base_hash))
            # 不同的 user prompt blocks (简化: 随机)
            for b in range(random.randint(1, 8)):  # user prompt 1-8 blocks
                blocks.append(random.randint(0, 2**63 - 1))

            requests.append(SimRequest(
                req_id=g_idx * per_group + i,
                system_prompt_len=prompt_len,
                system_prompt_hash=base_hash,
                blocks=blocks,
            ))

    return requests

# ═══════════════════════════════════════════════════════════
# TODO 4: 主模拟
# ═══════════════════════════════════════════════════════════

def run_simulation(requests, cache_capacity):
    """运行命中率模拟"""
    cache = LRUCache(cache_capacity)

    # TODO: 对每个请求, 遍历其 Block 列表
    # 对于 System Prompt 部分的 Block: 如果命中 → 跳过 Prefill (TTFT -90%)
    # 对于 User Prompt 部分的 Block: 通常不命中 (每次不同)
    # 记录每个请求的命中 Block 数和总 Block 数

    for req in requests:
        for block_hash in req.blocks:
            cache.access(block_hash)

    return cache.hit_rate

def main():
    parser = argparse.ArgumentParser(description="Prefix Cache Hit Rate Simulator")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--capacity", type=int, default=1000, help="Cache capacity (blocks)")
    parser.add_argument("--block-size", type=int, default=16)
    args = parser.parse_args()

    requests = generate_requests(args.requests, args.block_size)

    # TODO: 对比不同 Cache 容量下的命中率
    print("Prefix Cache Hit Rate Simulation")
    print(f"Requests: {len(requests)}")
    print(f"Block size: {args.block_size}\n")

    capacities = [500, 1000, 2000, 5000, 10000]
    print(f"{'Capacity':<10} {'Hit Rate':<10}")
    print(f"{'-'*10} {'-'*10}")
    for cap in capacities:
        rate = 0.0  # TODO: run_simulation(requests, cap)
        print(f"{cap:<10} {rate:<10.2%}")

    # TODO 5 (选做): 对比不同 System Prompt 长度下的加速比
    # TODO: 计算 TTFT 加速比 (假设命中 = 跳过 Prefill, -90% TTFT)

if __name__ == "__main__":
    main()
