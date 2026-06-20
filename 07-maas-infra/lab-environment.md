# 模块 7：从推理引擎到服务平台 — 实验环境说明

## 环境要求

### 硬件要求

| 项目 | 最低配置          | 推荐配置                |
| ---- | ----------------- | ----------------------- |
| CPU  | 8 核, 32 GB 内存  | 16 核+, 64 GB+          |
| 内存 | 32 GB             | 64 GB+                  |
| 磁盘 | 100 GB SSD        | 200 GB+                 |
| GPU  | 1-2 × ≥ 8 GB 显存 | 2+ GPU (用于多后端实验) |

### 软件要求

| 软件        | 版本    | 用途                                             |
| ----------- | ------- | ------------------------------------------------ |
| Python      | ≥ 3.10  | 网关实现 (Flask + requests)                      |
| vLLM        | ≥ 0.6.0 | 推理引擎 (后端)                                  |
| Flask       | latest  | 网关 Web 框架 (`pip install flask requests`)     |
| Kubernetes  | ≥ 1.28  | 容器编排 (进阶实验可选)                          |
| vLLM Router | latest  | 生产级 AI 网关 (选做: `pip install vllm-router`) |

---

## 环境搭建

### Step 1: 安装 Flask + 启动 vLLM 后端

```bash
kubectl get nodes
kubectl describe node <node> | grep nvidia.com/gpu
```

### Step 2: 部署 vLLM 推理后端

```yaml
# vllm-backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-backend-1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm-backend
      instance: "1"
  template:
    metadata:
      labels:
        app: vllm-backend
        instance: "1"
    spec:
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          args: ["--model", "Qwen/Qwen2.5-0.5B-Instruct", "--port", "8000"]
          resources:
            limits:
              nvidia.com/gpu: 1
          ports:
            - containerPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-backend-1-svc
spec:
  selector:
    app: vllm-backend
    instance: "1"
  ports:
    - port: 8000
```

### Step 3: 运行 Flask 网关

```python
# simple_gateway.py
from flask import Flask, request, Response
import requests
import random

app = Flask(__name__)

BACKENDS = [
    "http://vllm-backend-1-svc:8000",
    "http://vllm-backend-2-svc:8000",
]

@app.route('/v1/chat/completions', methods=['POST'])
def chat():
    backend = random.choice(BACKENDS)  # 简单轮询
    resp = requests.post(
        f"{backend}/v1/chat/completions",
        json=request.json,
        stream=True
    )
    return Response(resp.iter_content(chunk_size=1024),
                    content_type=resp.headers['Content-Type'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

---

## 环境验证

```bash
# 1. 后端可用
curl http://vllm-backend-1-svc:8000/v1/models

# 2. 网关可用
curl http://gateway:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "test", "messages": [{"role": "user", "content": "hi"}]}'
```
