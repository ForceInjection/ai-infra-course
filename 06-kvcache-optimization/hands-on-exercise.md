# 模块 6：大模型推理加速实践：KV Cache 原理与优化 — 课堂动手题

## 题目：KV Cache 加速效果验证

### 题目描述

1. 验证 Prefix Caching 的加速效果
2. 使用 LMCache 实现跨请求的 KV Cache 复用
3. 计算不同模型的 KV Cache 显存需求

### 预计时间

20–25 分钟

---

## Part 1: KV Cache 显存计算 (5 min)

```python
# kv_calc.py
import sys
sys.path.insert(0, '/Users/wangtianqing/Project/wechat/AI-fundamentals/09_inference_system/memory_calc')

def calc_kv_cache(n_layers, n_kv_heads, d_head, seq_len, batch, dtype_bytes=2):
    """计算 KV Cache 显存 (GB)"""
    kv = 2 * n_layers * n_kv_heads * d_head * seq_len * batch * dtype_bytes
    return kv / (1024**3)

# 常见模型配置
models = {
    "Qwen2.5-0.5B": (24, 2, 64),
    "Qwen2.5-7B":   (28, 4, 128),
    "Qwen2.5-72B":  (80, 8, 128),
    "DeepSeek-V3":  (61, 8, 128),   # 671B MoE, 约 37B 激活
}

print("KV Cache 显存计算 (FP16)")
print("=" * 60)
print(f"{'Model':<18} {'seq_len':>8} {'batch':>6} {'KV(GB)':>8}")
print("-" * 60)

for name, (L, H, D) in models.items():
    for seq_len in [2048, 4096, 8192, 32768]:
        for batch in [1, 8]:
            kv = calc_kv_cache(L, H, D, seq_len, batch)
            print(f"{name:<18} {seq_len:>8} {batch:>6} {kv:>8.1f}")

# 思考: 你的 GPU 显存能支撑什么样的 (seq_len, batch) 组合？
```

---

## Part 2: Prefix Caching 加速验证 (10 min)

### Step 1: 启动 vLLM 服务

```bash
vllm serve Qwen/Qwen2.5-0.5B-Instruct \
    --host 0.0.0.0 --port 8000 \
    --max-model-len 4096 \
    --enable-prefix-caching &
```

### Step 2: 编写测试脚本

```python
# prefix_cache_bench.py
import time
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="none")

# 长系统 Prompt (模拟 RAG 场景中的知识库上下文)
SYSTEM_PROMPT = """你是一个专业的AI基础设施专家。
你的知识包括: GPU架构、CUDA编程、容器技术、Kubernetes、大模型推理优化等。
请用专业且简洁的方式回答问题。
""" * 30  # 约 1500 tokens

def benchmark_ttft(system_prompt, user_prompt, label, warmup=False):
    start = time.time()
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-0.5B-Instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=50,
        stream=True
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            ttft = time.time() - start
            if not warmup:
                print(f"[{label}] TTFT: {ttft*1000:.0f} ms")
            return ttft

# Warmup
benchmark_ttft(SYSTEM_PROMPT, "什么是GPU?", "WARMUP", warmup=True)

# Test 1: 首次请求 (无缓存)
benchmark_ttft(SYSTEM_PROMPT, "什么是GPU?", "NO CACHE")

# Test 2: 相同 System Prompt，不同问题 (应命中缓存)
benchmark_ttft(SYSTEM_PROMPT, "什么是CUDA?", "CACHED")

# Test 3: 不同 System Prompt (不命中缓存)
benchmark_ttft("你是一个诗人。" * 500, "什么是GPU?", "DIFFERENT PREFIX")
```

### Step 3: 分析结果

```bash
python prefix_cache_bench.py
```

预期结果: CACHED 的 TTFT 比 NO CACHE 降低 50-80%。

---

## Part 3: LMCache 跨请求缓存 (10 min)

```bash
# 启动 vLLM + LMCache
vllm serve Qwen/Qwen2.5-0.5B-Instruct \
    --host 0.0.0.0 --port 8000 \
    --enable-lmcache
```

```python
# lmcache_test.py
import time, requests

BASE = "http://localhost:8000"
PROMPTS = [
    "什么是GPU的Tensor Core?",
    "什么是CPU的SIMD指令?",
]

for i, prompt in enumerate(PROMPTS):
    start = time.time()
    r = requests.post(f"{BASE}/v1/chat/completions", json={
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "messages": [
            {"role": "system", "content": "你是AI专家。" * 100},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100
    })
    ttft = time.time() - start
    print(f"Request {i+1} ('{prompt}'): TTFT={ttft*1000:.0f}ms")
```

---

## 讲解要点

### 1. KV Cache 显存公式的直观理解

- `× 2`: Key + Value 两组矩阵
- `× n_layers`: 每层都需要自己的 KV Cache
- `× n_kv_heads × d_head`: 每个 head 的维度
- `× seq_len × batch_size`: 每个序列、每个位置
- GQA 把 KV heads 减少 → Cache 显著减小 (Qwen2.5-7B 用 4 KV heads vs 28 Q heads)

### 2. Prefix Caching 的命中条件

- 必须是 **完全相同的前缀 token 序列**
- 从 prompt 起始位置匹配，不是子串匹配
- Hash 以 block (16 tokens) 为单位，块级匹配
- 命中后该 block 的 Prefill 被跳过 → 加速

### 3. LMCache vs APC 的区别

- APC: 单节点内，前缀匹配，自动生效
- LMCache: 跨节点共享，分层存储，支持非前缀复用 (CacheBlend)
- LMCache 适合集群级部署，APC 适合单节点

### 4. Offloading 的延迟代价

- GPU HBM 访问 ~1 TB/s → 延迟 ~0.1 μs
- CPU DRAM 访问 ~100 GB/s → 延迟 ~0.1 μs (但 copy 到 GPU 才有 ~10 μs)
- NVMe 访问 ~3-7 GB/s → 延迟 ~100 μs
- 结论: Offloading 到 CPU 可行，到 NVMe 需谨慎 (延迟敏感场景不可接受)
