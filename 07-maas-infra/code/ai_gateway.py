#!/usr/bin/env python3
"""简易 AI 网关 — 路由 + Token Bucket 限流 + 健康检查 + 故障转移

课堂动手题 (模块 7 · 第 42 页): 体验推理网关的核心机制。

用法:
    # 1. 启动两个 vLLM 后端
    vllm serve Qwen/Qwen2.5-0.5B-Instruct --port 8001 &
    vllm serve Qwen/Qwen2.5-0.5B-Instruct --port 8002 &

    # 2. 启动网关
    pip install flask requests
    python ai_gateway.py

    # 3. 测试
    curl http://localhost:8080/v1/chat/completions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer test-key" \
      -d '{"model":"test","messages":[{"role":"user","content":"say hi"}],"max_tokens":10}'

测试场景:
    1. 基本路由: 发送 10 个请求，观察负载分配
    2. 限流: 快速发送 15 个请求 (相同 API Key)，观察 429 响应
    3. 故障转移: kill 8001 后端，观察请求自动切换到 8002
"""

import random
import threading
import time
from collections import defaultdict

import requests
from flask import Flask, Response, jsonify, request

app = Flask(__name__)

# ============ 配置 ============
BACKENDS = {
    "default": [
        {"url": "http://localhost:8001", "weight": 1},
        {"url": "http://localhost:8002", "weight": 1},
    ],
}

API_KEYS = {
    "test-key": "default",     # API Key → 后端组
    "admin-key": "default",
}


# ============ Token Bucket 限流 ============
class TokenBucket:
    """Token Bucket 限流器。

    rate:    每秒补充的 Token 数 (tokens/s)
    capacity: 桶最大容量 (允许的 burst)
    """

    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
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


# 每个 API Key 独立的 Token Bucket (默认: 5 req/s, burst 10)
buckets = defaultdict(lambda: TokenBucket(rate=5, capacity=10))


# ============ 健康检查 ============
def health_check(backend_url):
    """主动健康检查: 查询 vLLM /v1/models 端点。"""
    try:
        r = requests.get(f"{backend_url}/v1/models", timeout=2)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False


# ============ 加权随机路由 ============
def select_backend():
    """加权随机选择健康后端。"""
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


# ============ API 端点 ============
@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    # 1. 认证
    api_key = request.headers.get("Authorization", "anonymous")
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    if api_key not in API_KEYS:
        return jsonify({"error": "Invalid API Key"}), 401

    # 2. 限流
    if not buckets[api_key].consume():
        return jsonify({"error": "Rate limit exceeded. Retry later."}), 429

    # 3. 路由选择
    backend = select_backend()
    if not backend:
        return jsonify({"error": "No healthy backend available"}), 503

    # 4. 转发请求 (流式)
    try:
        resp = requests.post(
            f"{backend['url']}/v1/chat/completions",
            json=request.json,
            stream=True,
            timeout=60,
        )
        return Response(
            resp.iter_content(chunk_size=1024),
            status=resp.status_code,
            content_type=resp.headers.get("Content-Type", "application/json"),
        )
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Backend error: {str(e)}"}), 502


@app.route("/health")
def health():
    """网关自身健康检查 + 后端状态。"""
    statuses = {b["url"]: health_check(b["url"]) for b in BACKENDS["default"]}
    return jsonify({"status": "ok", "backends": statuses})


if __name__ == "__main__":
    print("=" * 50)
    print("AI Gateway — 简易推理网关")
    print(f"后端: {[b['url'] for b in BACKENDS['default']]}")
    print(f"限流: 5 req/s per API Key, burst 10")
    print("端点: http://localhost:8080/v1/chat/completions")
    print("=" * 50)
    app.run(host="0.0.0.0", port=8080, debug=False)
