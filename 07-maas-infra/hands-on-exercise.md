# 模块 7：云原生 AI 推理基础设施进阶：构建 MaaS — 课堂动手题

## 题目：搭建 MaaS 推理接入层

### 题目描述

使用 Python 实现一个简化的 AI 网关，具备多模型路由、简单限流和故障转移功能，对接多个 vLLM 推理后端。

### 预计时间
20–25 分钟

---

## Step 1: 部署两个 vLLM 推理后端 (5 min)

```bash
# 后端 1 (端口 8001)
vllm serve Qwen/Qwen2.5-0.5B-Instruct --port 8001 &

# 后端 2 (端口 8002)
vllm serve Qwen/Qwen2.5-0.5B-Instruct --port 8002 &

# 验证
curl http://localhost:8001/v1/models
curl http://localhost:8002/v1/models
```

---

## Step 2: 实现 AI 网关 (12 min)

```python
# ai_gateway.py
import time
import random
from collections import defaultdict
from flask import Flask, request, jsonify, Response
import requests
import threading

app = Flask(__name__)

# ============ 配置 ============
BACKENDS = {
    "default": [
        {"url": "http://localhost:8001", "weight": 1},
        {"url": "http://localhost:8002", "weight": 1},
    ],
}

# ============ 限流 (简单 Token Bucket) ============
class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate          # tokens per second
        self.capacity = capacity  # max tokens
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens=1):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

# 每个 API key 一个 bucket
buckets = defaultdict(lambda: TokenBucket(rate=5, capacity=10))

# ============ 健康检查 ============
def health_check(backend_url):
    try:
        r = requests.get(f"{backend_url}/v1/models", timeout=2)
        return r.status_code == 200
    except:
        return False

# ============ 路由 ============
def select_backend():
    """加权随机选择后端"""
    backends = BACKENDS["default"]
    healthy = [b for b in backends if health_check(b["url"])]
    if not healthy:
        return None
    total_weight = sum(b["weight"] for b in healthy)
    r = random.uniform(0, total_weight)
    upto = 0
    for b in healthy:
        upto += b["weight"]
        if r <= upto:
            return b
    return healthy[0]

# ============ API ============
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    # 1. 认证
    api_key = request.headers.get('Authorization', 'anonymous')
    if api_key.startswith('Bearer '):
        api_key = api_key[7:]

    # 2. 限流
    if not buckets[api_key].consume():
        return jsonify({"error": "Rate limit exceeded"}), 429

    # 3. 路由选择
    backend = select_backend()
    if not backend:
        return jsonify({"error": "No healthy backend"}), 503

    # 4. 转发请求
    try:
        resp = requests.post(
            f"{backend['url']}/v1/chat/completions",
            json=request.json,
            stream=True,
            timeout=60
        )
        return Response(
            resp.iter_content(chunk_size=1024),
            status=resp.status_code,
            content_type=resp.headers.get('Content-Type', 'application/json')
        )
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Backend error: {str(e)}"}), 502

@app.route('/health')
def health():
    statuses = {b["url"]: health_check(b["url"]) for b in BACKENDS["default"]}
    return jsonify({"status": "ok", "backends": statuses})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
```

```bash
# 运行网关
pip install flask requests
python ai_gateway.py &
```

---

## Step 3: 测试网关功能 (8 min)

### 测试 1: 基本路由和负载均衡

```bash
for i in $(seq 1 10); do
  curl -s http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"test","messages":[{"role":"user","content":"say hi"}],"max_tokens":10}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'][:50])" &
done
```

观察网关日志中不同后端接收的请求数量。

### 测试 2: 限流

```bash
# 快速发送多个请求
for i in $(seq 1 15); do
  curl -s -w "\nHTTP %{http_code}\n" http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-key" \
    -d '{"model":"test","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
done
```

观察 429 响应何时出现。

### 测试 3: 故障转移

```bash
# 停掉后端 1
kill %1  # vLLM on 8001

# 再次发送请求
curl -s http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"test","messages":[{"role":"user","content":"hello"}],"max_tokens":10}'

# 观察是否被路由到后端 2
```

---

## 讲解要点

### 1. AI 网关 vs API 网关
- 传统 (Kong/nginx): 基于 URL/Header 路由，限流 per request
- AI 网关: 基于模型名/语义路由，限流 per token，流式代理
- 核心差异: AI 网关需要理解推理请求的语义和生命周期

### 2. 负载均衡策略的影响
- Random: 简单但可能导致负载不均
- Round-robin: 均匀但忽略 Prefix Cache 亲和性
- Consistent Hashing: 同 session → 同后端 → 高 Prefix Cache 命中率
- 生产环境推荐: Session-affine 路由 + 后端过载时的 fallback

### 3. 限流设计
- Token Bucket: 允许突发 (burst capacity)，限制长时平均速率
- Per API Key: 不同租户不同配额
- 多层限流: 网关 + 引擎 (双重保护)
- 限流后的处理: 429 → 客户端重试 + 指数退避

### 4. 健康检查与故障转移
- Active: 定期 ping `/v1/models`
- Passive: 请求失败时标记 unhealthy
- Circuit Breaker: 连续失败 N 次 → 熔断 → 半开后试探 → 恢复或继续熔断

### 5. 生产级增强
- 模型注册中心 (etcd/consul): 动态发现后端
- API 兼容性 (OpenAI format): 降低用户接入成本
- 审计日志: 记录每次调用的 token 用量和延迟
