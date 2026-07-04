# 模块 3：GPU 虚拟化与容器化实践 — 实验环境说明

## 环境要求

### 硬件要求

| 项目     | 最低配置                               | 推荐配置                     |
| -------- | -------------------------------------- | ---------------------------- |
| CPU      | 8 核                                   | 16 核+                       |
| 内存     | 16 GB                                  | 32 GB+                       |
| 磁盘     | 100 GB SSD                             | 200 GB+                      |
| GPU      | NVIDIA GPU (A100/H100 或 RTX 20 系列+) | A100 或 H100 (用于 MIG 演示) |
| GPU 显存 | 8 GB+                                  | 16 GB+                       |

### 软件要求

**必选** (课堂核心实验: LD_PRELOAD hook + GPU 容器):

| 软件                     | 版本   | 用途             |
| ------------------------ | ------ | ---------------- |
| Docker Engine            | ≥ 24.0 | 容器运行时       |
| NVIDIA Driver            | ≥ 570  | GPU 驱动 (CUDA 12.8 需要) |
| NVIDIA Container Toolkit | ≥ 1.14 | GPU 容器支持     |
| GCC                      | 任意   | 编译 malloc hook |

> 核心实验 `LD_PRELOAD=./libmymalloc.so ls` 不需要 GPU，任何 Linux 环境均可完成。

**可选** (HAMi 多容器 GPU 共享实验):

| 软件       | 版本          | 用途      |
| ---------- | ------------- | --------- |
| Kubernetes | ≥ 1.28        | HAMi 部署 |
| Helm       | ≥ 3.12        | HAMi 安装 |
| HAMi       | ≥ 2.4         | GPU 虚拟化管理 |

---

## 环境搭建步骤

### 必选: 核心实验环境

```bash
# 确认 GPU 可用
nvidia-smi

# 确认 Docker GPU runtime
docker run --rm --gpus all nvidia/cuda:12.8.0-runtime-ubuntu22.04 nvidia-smi

# 编译 malloc hook (不需要 GPU)
cd code/ && gcc -shared -fPIC 01_mymalloc.c -o libmymalloc.so -ldl
LD_PRELOAD=./libmymalloc.so ls /tmp
```

### 可选: HAMi 多容器 GPU 共享 (需要 K8s 集群)

```bash
# 1. 安装 Kubernetes (三选一)
minikube start --driver=docker --cpus=4 --memory=8192     # Minikube
curl -sfL https://get.k3s.io | sh -                       # k3s
kind create cluster --name gpu-cluster                     # Kind

# 2. 安装 HAMi
helm repo add hami-charts https://project-hami.github.io/HAMi/charts
helm repo update
helm install hami hami-charts/hami \
    --namespace kube-system \
    --set devicePlugin.deviceMemoryScaling=1 \
    --set devicePlugin.deviceSplitCount=10

# 3. 验证
kubectl get pods -n kube-system | grep hami
kubectl describe node <your-node> | grep nvidia.com/gpu
```

---

## 环境验证清单

### 必选: 核心实验

```bash
# 1. LD_PRELOAD hook 正常工作 (不需要 GPU)
gcc -shared -fPIC 01_mymalloc.c -o libmymalloc.so -ldl
LD_PRELOAD=./libmymalloc.so ls /tmp 2>&1 | grep HOOK
gcc 02_test_malloc.c -o test_malloc
LD_PRELOAD=./libmymalloc.so ./test_malloc

# 2. GPU 容器可用 (需要 GPU)
docker run --rm --gpus all nvidia/cuda:12.8.0-runtime-ubuntu22.04 nvidia-smi
```

### 可选: HAMi GPU 共享

```bash
kubectl get pods -n kube-system | grep hami
kubectl describe node <your-node> | grep nvidia.com/gpu
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
