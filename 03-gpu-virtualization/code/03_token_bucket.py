#!/usr/bin/env python3
"""
模块 3: GPU 虚拟化 — 令牌桶 (Token Bucket) 算力限制演示
PPT 第 15-16 页 [HAMi cuLaunchKernel 拦截]

HAMi 用令牌桶限制每个容器的 GPU 计算时间:
  - 每个容器每秒获得 N 个令牌 (token)
  - 每次 cuLaunchKernel 消耗 1 个令牌
  - 令牌用完 → kernel 启动被阻塞 (模拟 CUDA 调用延迟)
  - 令牌按固定速率补充 (refill rate)

本脚本模拟 2 个容器共享 1 块 GPU，各有独立令牌桶配额。

运行:
  python3 03_token_bucket.py
"""

import time
import random


class TokenBucket:
    """令牌桶 — 模拟 HAMi 对 cuLaunchKernel 的调用限制"""

    def __init__(self, name: str, rate: int, capacity: int):
        """
        name:     容器名称
        rate:     每秒补充令牌数 (模拟 HAMi 的 core utilization 配额)
        capacity: 桶容量 (允许的最大突发调用)
        """
        self.name = name
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity       # 当前令牌数
        self.last_refill = time.monotonic()
        self.total_launched = 0      # 成功启动的 kernel 数
        self.total_blocked = 0       # 被阻塞的 kernel 数

    def _refill(self):
        """按经过的时间补充令牌"""
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def acquire(self) -> bool:
        """尝试获取 1 个令牌。成功返回 True，否则 False。"""
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            self.total_launched += 1
            return True
        else:
            self.total_blocked += 1
            return False


def simulate(container_a: TokenBucket, container_b: TokenBucket, duration: float = 5.0):
    """模拟两个容器交替提交 kernel，各有限速"""

    print(f"\n{'='*65}")
    print(f"  令牌桶算力限制 — 模拟 HAMi cuLaunchKernel 拦截")
    print(f"{'='*65}")
    print(f"  {container_a.name}: {container_a.rate} tokens/s, 容量 {container_a.capacity}")
    print(f"  {container_b.name}: {container_b.rate} tokens/s, 容量 {container_b.capacity}")
    print(f"  模拟时长: {duration:.0f}s\n")
    print(f"  {'时间':>6s}  {'容器':>10s}  {'结果':>8s}  {'剩余 token':>10s}")
    print(f"  {'-'*50}")

    start = time.monotonic()
    step = 0

    while time.monotonic() - start < duration:
        step += 1
        # 两个容器交替提交 kernel
        for bucket in (container_a, container_b):
            ok = bucket.acquire()
            elapsed = time.monotonic() - start
            status = "✓ 启动" if ok else "✗ 阻塞"
            print(f"  {elapsed:5.2f}s  {bucket.name:>10s}  {status:>8s}  {bucket.tokens:8.1f}")

        time.sleep(0.3)

    print(f"  {'-'*50}")
    for bucket in (container_a, container_b):
        total = bucket.total_launched + bucket.total_blocked
        print(f"  {bucket.name}: 成功 {bucket.total_launched}/{total}"
              f" ({100*bucket.total_launched/total:.0f}%), 阻塞 {bucket.total_blocked}")


def simulate_burst(bucket: TokenBucket, idle_time: float = 2.0, burst_count: int = 6):
    """演示 burst: 空闲积攒 → 一次性爆发"""
    print(f"\n{'='*65}")
    print(f"  Burst (突发) 演示 — {bucket.name}")
    print(f"{'='*65}")
    print(f"  速率: {bucket.rate} tokens/s, 容量: {bucket.capacity}")
    print(f"  策略: 先空闲 {idle_time:.0f}s 积攒 token → 瞬间提交 {burst_count} 个 kernel\n")

    # 阶段 1: 空闲积攒
    print(f"  [阶段 1] 容器空闲 {idle_time:.0f}s, 令牌积攒中...")
    time.sleep(idle_time)
    bucket._refill()
    print(f"  [阶段 1] 积攒完成 → 令牌数: {bucket.tokens:.1f}\n")

    # 阶段 2: 突发提交
    print(f"  [阶段 2] 瞬间提交 {burst_count} 个 kernel (burst):")
    print(f"  {'请求':>6s}  {'结果':>6s}  {'剩余':>6s}")
    for i in range(burst_count):
        ok = bucket.acquire()
        print(f"  #{i+1:4d}   {'✓ 通过' if ok else '✗ 阻塞':>6s}  {bucket.tokens:5.1f}")

    print(f"\n  解析: capacity={bucket.capacity} → 最多积攒 {bucket.capacity} 个令牌")
    print(f"  前 {bucket.capacity} 个请求用积攒的令牌一次性通过 (burst)")
    print(f"  之后的请求需要等待令牌按 {bucket.rate} tokens/s 补充 → 阻塞")


if __name__ == "__main__":
    # --- 演示 1: 持续提交, 对比配额 ---
    a = TokenBucket("容器A(高配额)", rate=4, capacity=4)
    b = TokenBucket("容器B(低配额)", rate=1, capacity=2)
    simulate(a, b, duration=5.0)

    # --- 演示 2: burst 行为 ---
    c = TokenBucket("容量=4", rate=2, capacity=4)
    simulate_burst(c, idle_time=2.0, burst_count=6)

    # --- 思考题 ---
    print(f"\n{'─'*65}")
    print("  思考题 (对应 PPT 第 15-16 页)")
    print(f"{'─'*65}")
    print("1. 观察容器 A/B 的阻塞比例，谁的阻塞更多？为什么？")
    print("   -> 容器 B 只有 1 token/s，提交频率超过补充速率就会阻塞")
    print()
    print("2. 把容器 B 的 rate 改为 4，两个容器行为应该一致。验证一下。")
    print("   -> 修改 TokenBucket('容器B', rate=4, capacity=4)，重新运行")
    print()
    print("3. capacity 参数有什么用？")
    print("   -> 允许\"突发\"(burst)：空闲一段时间后积攒的令牌可以一次性花掉")
    print("   -> HAMi 中对应: 容器偶尔可以连续启动几个 kernel，但不能持续超配额")
    print()
    print("4. 这个令牌桶是如何和 HAMi 的 cuLaunchKernel 拦截关联的?")
    print("   -> libvgpu.so 拦截 cuLaunchKernel → 调用 acquire()")
    print("   -> 有令牌 → 调用真正的 cuLaunchKernel → kernel 正常运行")
    print("   -> 无令牌 → 阻塞等待 (或返回错误) → kernel 延迟执行")
    print(f"{'─'*65}")
