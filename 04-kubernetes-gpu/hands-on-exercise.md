# 模块 4：Kubernetes 入门与 GPU 工作负载调度 — 课堂动手题

## 题目：K8s 初体验 + GPU Pod 部署 + 资源争抢观察

### 题目描述

三个递进实验，从 K8s 基础操作到 GPU 调度实战：

1. **K8s 初体验** — 部署 Nginx，理解 Pod/Deployment/Service
2. **GPU Pod 部署** — 声明 GPU 资源，验证 GPU 可用
3. **资源争抢观察** — 超量声明 GPU，观察 K8s 调度行为

### 预计时间

20 分钟

---

## 实验 1: K8s 初体验 — 部署 Nginx (5 min)

> 对应 PPT 第 16 页 &nbsp;|&nbsp; 配套 YAML: `code/01_nginx_demo.yaml`

**两种方式任选**: 下面演示命令式操作 (`kubectl create`/`expose`/`scale`)，也可以直接用声明式 `kubectl apply -f code/01_nginx_demo.yaml`。

### Step 1: 部署应用

```bash
# 创建 Deployment
kubectl create deployment nginx-demo --image=nginx:alpine

# 查看 Pod 状态
kubectl get pods -w

# 暴露为 Service
kubectl expose deployment nginx-demo --port=80 --type=NodePort

# 查看 Service
kubectl get svc nginx-demo
```

### Step 2: 伸缩与访问

```bash
# 扩容到 3 个副本
kubectl scale deployment nginx-demo --replicas=3
kubectl get pods

# 端口转发 (本地访问)
kubectl port-forward deployment/nginx-demo 8080:80
# 浏览器打开 http://localhost:8080
```

### Step 3: 查看日志与进入容器

```bash
# 查看日志
kubectl logs deployment/nginx-demo

# 进入容器
kubectl exec -it deployment/nginx-demo -- /bin/sh
# 容器内: env | grep KUBERNETES
```

---

## 实验 2: GPU Pod 部署 (8 min)

> 对应 PPT 第 45 页 &nbsp;|&nbsp; 配套 YAML: `code/02_gpu_pod.yaml`、`code/03_gpu_deploy.yaml`

### Step 1: 编写 GPU Pod YAML

```yaml
# gpu-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-test
spec:
  restartPolicy: Never
  containers:
    - name: cuda
      image: nvidia/cuda:12.4.0-base-ubuntu22.04
      command: ["nvidia-smi"]
      resources:
        limits:
          nvidia.com/gpu: 1
```

### Step 2: 部署并验证

```bash
kubectl apply -f gpu-pod.yaml
kubectl get pods -w
kubectl logs gpu-test
```

预期看到 nvidia-smi 输出 + GPU 信息。如果 Pod 一直 Pending，用 `kubectl describe pod gpu-test` 查看 Events。

### Step 3: 创建 Deployment 版本

```yaml
# gpu-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-inference
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gpu-inference
  template:
    metadata:
      labels:
        app: gpu-inference
    spec:
      containers:
        - name: cuda
          image: nvidia/cuda:12.4.0-base-ubuntu22.04
          command: ["/bin/bash", "-c"]
          args:
            - |
              nvidia-smi
              echo "GPU is ready."
              sleep 3600
          resources:
            limits:
              nvidia.com/gpu: 1
```

```bash
kubectl apply -f gpu-deploy.yaml
kubectl get pods -l app=gpu-inference
kubectl logs -l app=gpu-inference
```

---

## 实验 3: GPU 资源争抢观察 (7 min)

> 对应 PPT 第 46 页

```bash
# 假设节点只有 1 张 GPU，扩容到 3 个副本
kubectl scale deployment gpu-inference --replicas=3

# 观察 Pod 状态
kubectl get pods -l app=gpu-inference -o wide

# 查看 Pending Pod 的原因
kubectl describe pod $(kubectl get pods -l app=gpu-inference \
    --field-selector=status.phase=Pending \
    -o jsonpath='{.items[0].metadata.name}') | grep -A 10 Events
```

预期看到：

```text
Events:
  Type     Reason            Age   From               Message
  ----     ------            ----  ----               -------
  Warning  FailedScheduling  10s   default-scheduler  0/1 nodes are available:
          1 Insufficient nvidia.com/gpu
```

**关键理解**: K8s Scheduler 发现所有节点的 GPU 都已被占用 → 多余的 Pod 进入 Pending 状态等待 → GPU 释放后自动调度。这就是 K8s 资源管理的核心。

---

## 清理

```bash
kubectl delete deployment nginx-demo gpu-inference
kubectl delete service nginx-demo
kubectl delete pod gpu-test
```

---

## 讲解要点

### 1. K8s 声明式 vs Docker 命令式

- Docker: `docker run -d --gpus all nvidia/cuda:... nvidia-smi` — 手动指定一切
- K8s: 写一个 YAML，声明 "我要 1 张 GPU"，K8s 自动调度
- 「Docker 是你说每一步做什么，K8s 是你说最终长什么样」

### 2. GPU 成为可调度资源

- `nvidia.com/gpu: 1` 在 YAML 里跟 `cpu: 1` 一样自然
- 背后是 Device Plugin + Scheduler + NVIDIA CTK 的完整链条

### 3. Pending Pod 的设计哲学

- GPU 不够时不是崩溃，是**排队等待** — K8s 的核心设计
- Pending Pod 的 Events 告诉你为什么不能调度
- 可以配合 Kueue 做更智能的排队管理

### 4. Deployment 的 GPU 管理

- Deployment 管理 GPU Pod 的副本数
- 滚动更新: 新版本 Pod 启动 → 旧版本 Pod 停止 → GPU 平滑交接
- 结合 HPA (Horizontal Pod Autoscaler) 可以按 GPU 利用率自动扩缩容
