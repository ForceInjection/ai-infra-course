#!/usr/bin/env python3
"""简易 vLLM Mock 后端 — 用于本地测试 AI 网关，无需 GPU 和真实模型。

用法:
    # 启动两个 mock 后端 (不同端口)
    python3 mock_vllm.py --port 8001 &
    python3 mock_vllm.py --port 8002 &

    # 然后按正常流程测试网关
    python3 ai_gateway.py
"""

import argparse
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler


class MockVLLM(BaseHTTPRequestHandler):
    """模拟 vLLM 的 OpenAI 兼容 API (仅 /v1/models 和 /v1/chat/completions)。"""

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/v1/models":
            self._json({"object": "list", "data": [{"id": "mock-model"}]})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        if "/v1/chat/completions" in self.path:
            # 读取请求体 (但不解析, 直接返回固定响应)
            content_len = int(self.headers.get("Content-Length", 0))
            self.rfile.read(content_len)

            self._json({
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "mock-model",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"[mock vLLM :{self.server.server_port}] 这是一个模拟响应。",
                    },
                    "finish_reason": "stop",
                }],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 8,
                    "total_tokens": 13,
                },
            })
        else:
            self._json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        """抑制默认日志 (改用自定义格式)。"""
        print(f"[mock:{self.server.server_port}] {args[0]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="vLLM Mock 后端")
    parser.add_argument("--port", type=int, default=8001, help="监听端口 (默认 8001)")
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), MockVLLM)
    print(f"[mock vLLM] 监听 0.0.0.0:{args.port} — /v1/models, /v1/chat/completions")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[mock vLLM :{args.port}] 已停止")
