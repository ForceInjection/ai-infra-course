# 模块 7：云原生 AI 推理基础设施进阶：构建 MaaS — 实验环境说明

## 环境要求

### 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 8 核, 32 GB 内存 | 16 核+, 64 GB+ |
| 内存 | 32 GB | 64 GB+ |
| 磁盘 | 100 GB SSD | 200 GB+ |
| GPU | 1-2 × ≥ 8 GB 显存 | 2+ GPU (用于多后端实验) |

### 软件要求

| 软件 | 版本 | 用途 |
|------|------|------|
| Kubernetes | ≥ 1.28 | 容器编排 |
| kubectl | ≥ 1.28 | K8s CLI |
| Helm | ≥ 3.12 | 包管理 |
| vLLM | ≥ 0.6.0 | 推理引擎 |
| Python | ≥ 3.10 | API 调用测试 |

---

## 环境搭建

### Step 1: 确认 K8s 集群 + GPU

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

### Step 3: 部署简单网关 (Python 实现)

如果 llm-d 部署复杂，可以使用一个简化的 Python 网关快速体验：

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
