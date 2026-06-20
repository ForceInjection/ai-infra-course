# 模块 7：从推理引擎到服务平台 — 课堂动手题

## 题目：实现 AI 网关 — 路由 + 限流 + 故障转移

> 对应 PPT 第 42 页

### 题目描述

使用 Python + Flask 实现一个简化 AI 网关，体验推理网关的核心机制：Token Bucket 限流、加权随机路由、健康检查与故障转移。对接两个 vLLM 推理后端。

### 预计时间

15–20 分钟

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

### 1. AI 网关 vs 通用 API 网关

- 通用 (Kong/Nginx): 基于 URL/Header 路由，限流 per request，不理解请求内容
- AI 网关 (vLLM Router): 基于模型名/语义路由，限流 per token (加权限流)，流式代理，推理感知——知道 Cache 命中率、GPU 利用率
- 核心差异: AI 网关需要理解推理请求的语义和生命周期。「看见的是推理任务，不只是 HTTP 请求」

### 2. 负载均衡策略的演进

- Random: 简单但 Cache 亲和性为 0 → Prefix Cache 命中率 ~30%
- Consistent Hash: 同用户 → 同后端 → Cache 命中率 ~60%
- Cache-Aware (vLLM Router 默认): 查 Worker 的 Cache 命中率→选最高的 → 命中率 ~85%
- 生产推荐: Cache-Aware 优先 + Power of Two 回退

### 3. Token Bucket 限流

- 原理: 固定速率产 Token，请求消耗 Token。允许 burst (桶容量)，限制长时平均速率
- 三级限流: Per-User / Per-Model / Per-IP
- 推理加权限流: `cost = input_tokens × 1.0 + output_tokens × 2.0` (Decode token 更贵)
- 限流后处理: HTTP 429 + `Retry-After` header → 客户端指数退避重试

### 4. 健康检查与 Circuit Breaker

- 主动: 定期 GET `/health` or `/v1/models`
- 被动: 请求失败 (5xx/超时) → 熔断器记录
- Circuit Breaker: CLOSED → (失败 N 次) → OPEN (快速失败) → (超时) → HALF-OPEN → (成功) → CLOSED
- vLLM Router: per-worker 粒度，一个挂了不影响其他

### 5. 从课堂到生产

- 课堂实现: Flask + Token Bucket + 加权随机 → 200 行，理解核心机制
- 生产方案: vLLM Router (Rust) → Cache-Aware LB + Semantic Router + Circuit Breaker + K8s 原生
- 生产还需要: 审计日志、Prometheus Metrics、金丝雀发布、多副本反亲和
