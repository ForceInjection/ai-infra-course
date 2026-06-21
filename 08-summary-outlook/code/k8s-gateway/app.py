#!/usr/bin/env python3
"""AI 网关骨架 — Flask 实现

已提供: Flask 框架 / Token Bucket 限流器 / 健康检查 / OpenAI 兼容路由框架
TODO:   LB 策略实现 / 请求日志 / 流式转发

运行: pip install flask requests && python app.py
参考: 模块 7 code/ai_gateway.py
"""

import json
import random
import threading
import time
from collections import defaultdict

import requests
from flask import Flask, Response, jsonify, request

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════
# 配置 (可通过 ConfigMap / 环境变量覆盖)
# ═══════════════════════════════════════════════════════════
BACKENDS = [
    {"url": "http://localhost:8001", "weight": 1, "model": "qwen"},
    {"url": "http://localhost:8002", "weight": 2, "model": "qwen"},
    {"url": "http://localhost:8003", "weight": 1, "model": "qwen"},
]

API_KEYS = {
    "sk-test-1": "free",
    "sk-test-2": "pro",
}

# ═══════════════════════════════════════════════════════════
# Token Bucket 限流器 (已实现)
# ═══════════════════════════════════════════════════════════
class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens=1):
        with self.lock:
            now = time.time()
            self.tokens = min(self.capacity,
                              self.tokens + (now - self.last_refill) * self.rate)
            self.last_refill = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

# 每 API Key 独立限流
buckets = defaultdict(lambda: TokenBucket(rate=5, capacity=10))

# ═══════════════════════════════════════════════════════════
# TODO 1: 负载均衡策略
# ═══════════════════════════════════════════════════════════

def select_backend_round_robin(backends):
    """加权轮询"""
    # TODO: 维护全局计数器, 按权重轮询选择后端
    pass

def select_backend_consistent_hash(backends, key):
    """一致性哈希"""
    # TODO: 构造 Hash Ring, hash(key) → 环上顺时针找最近节点
    # 提示: 每个后端映射 100-200 个虚拟节点到环上
    pass

def select_backend_least_connections(backends):
    """最少连接"""
    # TODO: 维护每个后端的活跃连接数, 选最少的
    pass

# 默认 LB 策略 (可在请求中通过 header 切换)
LB_POLICY = "round_robin"  # round_robin | consistent_hash | least_connections

def select_backend():
    """根据 LB_POLICY 选择健康后端"""
    healthy = [b for b in BACKENDS if health_check(b["url"])]
    if not healthy:
        return None

    # TODO: 根据 LB_POLICY 调用对应的 select_backend_* 函数
    # 当前用简单的加权随机作为占位
    total_weight = sum(b["weight"] for b in healthy)
    r = random.uniform(0, total_weight)
    upto = 0
    for b in healthy:
        upto += b["weight"]
        if r <= upto:
            return b
    return healthy[0]

# ═══════════════════════════════════════════════════════════
# 健康检查 (已实现)
# ═══════════════════════════════════════════════════════════
def health_check(backend_url):
    try:
        r = requests.get(f"{backend_url}/health", timeout=2)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False

# ═══════════════════════════════════════════════════════════
# TODO 2: 请求日志
# ═══════════════════════════════════════════════════════════
def log_request(api_key, model, backend_url, latency_ms, tokens, status):
    """JSON 格式请求日志"""
    # TODO: 输出 JSON 格式日志
    # log = {"timestamp": ..., "api_key": ..., "model": ..., ...}
    # print(json.dumps(log))
    pass

# ═══════════════════════════════════════════════════════════
# OpenAI 兼容 API (框架已实现, TODO: 完善流式转发)
# ═══════════════════════════════════════════════════════════
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
        return jsonify({"error": "Rate limit exceeded"}), 429

    # 3. 路由
    backend = select_backend()
    if not backend:
        return jsonify({"error": "No healthy backend"}), 503

    # 4. 转发 (TODO: 流式转发 SSE)
    start = time.time()
    try:
        resp = requests.post(
            f"{backend['url']}/v1/chat/completions",
            json=request.json,
            timeout=60,
        )
        latency_ms = (time.time() - start) * 1000
        # TODO: log_request(...)
        return Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get("Content-Type", "application/json"),
        )
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Backend error: {str(e)}"}), 502

@app.route("/health")
def health():
    statuses = {b["url"]: health_check(b["url"]) for b in BACKENDS}
    return jsonify({"status": "ok", "backends": statuses})

# TODO 3 (选做): /metrics 端点 — 暴露 Prometheus 格式指标
# @app.route("/metrics")
# def metrics():
#     return Response("...", content_type="text/plain")

if __name__ == "__main__":
    print(f"Gateway starting with LB policy: {LB_POLICY}")
    print(f"Backends: {[b['url'] for b in BACKENDS]}")
    app.run(host="0.0.0.0", port=8080, debug=False)
