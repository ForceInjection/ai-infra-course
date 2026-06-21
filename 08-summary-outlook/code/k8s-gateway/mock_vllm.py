#!/usr/bin/env python3
"""Mock vLLM 后端 — 模拟 OpenAI 兼容 API

运行: python mock_vllm.py --port 8001 --model qwen --delay 0.05
"""

import argparse
import json
import random
import time
import uuid

from flask import Flask, jsonify, request, Response

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════
# 配置 (命令行参数)
# ═══════════════════════════════════════════════════════════
MODEL_NAME = "qwen"
BASE_DELAY = 0.05     # 基础延迟 (模拟 Prefill+Decode)
ERROR_RATE = 0.0      # 错误率 (0.0-1.0, 模拟故障)

# ═══════════════════════════════════════════════════════════
# OpenAI 兼容 API
# ═══════════════════════════════════════════════════════════
@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    # 模拟错误
    if random.random() < ERROR_RATE:
        return jsonify({"error": "Internal server error (simulated)"}), 500

    data = request.json or {}
    prompt = data.get("messages", [{"role": "user", "content": "hello"}])
    max_tokens = data.get("max_tokens", 50)

    # 模拟推理延迟 (Prefill + Decode)
    delay = BASE_DELAY + random.uniform(0, 0.1) * max_tokens / 50
    time.sleep(delay)

    # 构造符合 OpenAI 格式的响应
    response = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[{MODEL_NAME}] 这是一个模拟响应。您的输入有 {_count_tokens(prompt)} tokens。"
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": _count_tokens(prompt),
            "completion_tokens": max_tokens,
            "total_tokens": _count_tokens(prompt) + max_tokens,
        },
    }
    return jsonify(response)

@app.route("/v1/models")
def models():
    return jsonify({"data": [{"id": MODEL_NAME, "object": "model"}]})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL_NAME})

@app.route("/metrics")
def metrics():
    """模拟 vLLM Prometheus metrics"""
    return Response(
        f"# HELP vllm_gpu_prefix_cache_hit_rate GPU prefix cache hit rate\n"
        f"# TYPE vllm_gpu_prefix_cache_hit_rate gauge\n"
        f"vllm_gpu_prefix_cache_hit_rate{{model=\"{MODEL_NAME}\"}} {random.uniform(0.3, 0.9)}\n"
        f"# HELP vllm_request_success_total Total successful requests\n"
        f"# TYPE vllm_request_success_total counter\n"
        f"vllm_request_success_total{{model=\"{MODEL_NAME}\"}} {random.randint(100, 1000)}\n",
        content_type="text/plain",
    )

def _count_tokens(messages):
    if isinstance(messages, list):
        return sum(len(str(m.get("content", ""))) // 4 for m in messages)
    return len(str(messages)) // 4

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--model", default="qwen")
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--error-rate", type=float, default=0.0)
    args = parser.parse_args()

    MODEL_NAME = args.model
    BASE_DELAY = args.delay
    ERROR_RATE = args.error_rate

    print(f"Mock vLLM ({MODEL_NAME}) on port {args.port}")
    print(f"  delay={BASE_DELAY}s, error_rate={ERROR_RATE}")
    app.run(host="0.0.0.0", port=args.port, debug=False)
