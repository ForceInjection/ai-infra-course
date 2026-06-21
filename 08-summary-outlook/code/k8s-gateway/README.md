# 方向 B: K8s GPU 调度 — 从 YAML 到容器启动

**难度**: ★★★☆ &nbsp;|&nbsp; **覆盖模块**: 1 (容器), 4 (K8s), 7 (服务平台)

## 快速开始

```bash
# 有 K8s 集群
kubectl apply -f k8s-backend.yaml
kubectl apply -f k8s-gateway.yaml
kubectl apply -f k8s-configmap.yaml
kubectl apply -f k8s-hpa.yaml
kubectl get pods -w  # 观察调度过程

# 无 K8s 集群: 用 docker-compose
docker-compose up -d
curl http://localhost:8080/health

# 验证 K8s YAML 语法
kubectl --dry-run=client -f k8s-backend.yaml
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `app.py` | Flask 网关骨架 — Token Bucket 已实现，搜索 `TODO` 完成 LB 策略 |
| `mock_vllm.py` | Mock vLLM 后端 — 模拟 OpenAI API，可配置延迟和错误率 |
| `docker-compose.yml` | 本地替代方案 (1 网关 + 3 后端) |
| `k8s-backend.yaml` | GPU 后端 Deployment + Service |
| `k8s-gateway.yaml` | 网关 Deployment + Service |
| `k8s-configmap.yaml` | 网关配置 (LB 策略、限流、后端列表) |
| `k8s-hpa.yaml` | HPA 弹性伸缩 (网关 + 后端) |

## 无 K8s 集群

使用 `docker-compose.yml` 启动全部组件，K8s YAML 通过 `kubectl --dry-run=client` 验证语法即可。
