# 模块 3：GPU 虚拟化与容器化实践 — 实验环境说明

## 环境要求

### 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 8 核 | 16 核+ |
| 内存 | 16 GB | 32 GB+ |
| 磁盘 | 100 GB SSD | 200 GB+ |
| GPU | NVIDIA GPU (A100/H100 或 RTX 20 系列+) | A100 或 H100 (用于 MIG 演示) |
| GPU 显存 | 8 GB+ | 16 GB+ |

### 软件要求

| 软件 | 版本 | 用途 |
|------|------|------|
| Docker Engine | ≥ 24.0 | 容器运行时 |
| NVIDIA Driver | ≥ 535 | GPU 驱动 |
| NVIDIA Container Toolkit | ≥ 1.14 | GPU 容器 |
| Kubernetes | ≥ 1.28 (可选) | HAMi 部署 |
| Helm | ≥ 3.12 (可选) | HAMi 安装 |
| HAMi | ≥ 2.4 | GPU 虚拟化管理 |

---

## 环境搭建步骤

### Step 1: 基础环境确认

```bash
# 确认 GPU 可用
nvidia-smi

# 确认 Docker GPU runtime
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# 确认 nvidia-container-toolkit 版本
dpkg -l | grep nvidia-container-toolkit
```

### Step 2: 安装 Kubernetes (可选 — 用于 HAMi 实验)

**使用 Minikube (单机方案)**:

```bash
# 安装 minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 启动
minikube start --driver=docker --cpus=4 --memory=8192

# 或使用 kind
kind create cluster --name gpu-cluster
```

**使用 k3s (轻量方案)**:

```bash
curl -sfL https://get.k3s.io | sh -
sudo k3s kubectl get nodes
```

### Step 3: 安装 HAMi

```bash
# 添加 HAMi Helm 仓库
helm repo add hami-charts https://project-hami.github.io/HAMi/charts
helm repo update

# 安装 HAMi
helm install hami hami-charts/hami \
    --namespace kube-system \
    --set devicePlugin.deviceMemoryScaling=1 \
    --set devicePlugin.deviceSplitCount=10

# 验证安装
kubectl get pods -n kube-system | grep hami
kubectl describe node <your-node> | grep nvidia.com/gpu
```

### Step 4: 拉取实验镜像

```bash
# 基础 CUDA 镜像
docker pull nvidia/cuda:12.4.0-devel-ubuntu22.04
docker pull nvidia/cuda:12.4.0-runtime-ubuntu22.04

# GPU 压力测试工具
docker pull nginx:alpine

# Python + PyTorch 镜像
docker pull pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
```

---

## 环境验证清单

### 基础 GPU 容器验证

```bash
# 1. GPU 容器能正常启动
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# 2. 显存分配测试
docker run --rm --gpus all nvidia/cuda:12.4.0-devel-ubuntu22.04 \
    python3 -c "import torch; print(torch.cuda.memory_summary())"
```

### HAMi 验证 (如果安装了 K8s + HAMi)

```bash
# 创建 GPU 共享测试 Pod
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: gpu-shared-test
spec:
  containers:
  - name: cuda-container
    image: nvidia/cuda:12.4.0-devel-ubuntu22.04
    command: ["sleep", "3600"]
    resources:
      limits:
        nvidia.com/gpu: 1
        nvidia.com/gpumem: 2048
EOF

# 验证
kubectl exec -it gpu-shared-test -- nvidia-smi
kubectl exec -it gpu-shared-test -- nvidia-smi --query-gpu=memory.used --format=csv

# 清理
kubectl delete pod gpu-shared-test
```

---

## 常见问题

### Q: Docker GPU 容器报 "could not select device driver"
```bash
# 确认 runtime 配置
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
cat /etc/docker/daemon.json | grep nvidia
```

### Q: HAMi Pod 看不到 GPU 或显存显示为 0
- 检查 Device Plugin 是否正常运行: `kubectl get pods -n kube-system | grep hami`
- 检查节点资源: `kubectl describe node <node> | grep nvidia`

### Q: Minikube 中 GPU 不可用
- Minikube 的 Docker driver 默认不支持 GPU Passthrough
- 如果只需要体验 CPU 部分，可以跳过 GPU 相关的实验
- 需要 GPU 实验建议使用裸机 K8s 或 k3s
