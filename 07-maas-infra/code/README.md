# 模块 7 配套代码 — 推理服务平台

## 文件说明

| 文件            | 内容                                                                    | 对应 PPT        |
| --------------- | ----------------------------------------------------------------------- | --------------- |
| `ai_gateway.py` | Flask 简易 AI 网关 — 加权路由 + Token Bucket 限流 + 健康检查 + 故障转移 | 第 42 页 [动手] |

vLLM Router 生产级网关通过 pip 安装:  
`pip install vllm-router` (选做, 见 homework 任务 3)

## 环境要求

- Python ≥ 3.10
- Flask + requests: `pip install flask requests`
- vLLM ≥ 0.6.0 (后端，需要 GPU)
- 或使用任意 HTTP 服务模拟后端 (修改 `BACKENDS` 配置即可)

## 运行方法

```bash
# 1. 启动两个 vLLM 后端
vllm serve Qwen/Qwen2.5-0.5B-Instruct --port 8001 &
vllm serve Qwen/Qwen2.5-0.5B-Instruct --port 8002 &

# 2. 启动网关
python ai_gateway.py
```

## 测试

### 测试 1: 基本路由 (观察两个后端的负载分配)

```bash
for i in $(seq 1 10); do
  curl -s http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"test","messages":[{"role":"user","content":"say hi"}],"max_tokens":10}' &
done
```

### 测试 2: 限流 (观察 429 响应)

```bash
for i in $(seq 1 15); do
  curl -s -w "\nHTTP %{http_code}\n" http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-key" \
    -d '{"model":"test","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
done
```

### 测试 3: 故障转移 (kill 8001 后端，观察自动切换)

```bash
kill %1   # 停掉 8001 后端
curl -s http://localhost:8080/health  # 查看后端状态
curl -s http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"test","messages":[{"role":"user","content":"hello"}],"max_tokens":10}'
```

## 代码结构

```text
ai_gateway.py   (~140 行)
├── BACKENDS         # 后端地址 + 权重配置
├── TokenBucket      # Token Bucket 限流器 (线程安全)
├── health_check()   # 主动健康检查 (GET /v1/models)
├── select_backend() # 加权随机选择健康后端
└── Flask 路由:
    ├── /v1/chat/completions  # 认证 → 限流 → 路由 → 转发 (流式)
    └── /health               # 网关状态 + 后端健康
```
