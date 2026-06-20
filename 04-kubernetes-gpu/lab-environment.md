# 模块 4：Kubernetes 入门与 GPU 工作负载调度 — 实验环境说明

## 环境要求

### 硬件要求

| 项目 | 最低配置             | 推荐配置                           |
| ---- | -------------------- | ---------------------------------- |
| CPU  | 8 核                 | 16 核+                             |
| 内存 | 16 GB                | 32 GB+                             |
| 磁盘 | 100 GB SSD           | 200 GB+                            |
| GPU  | NVIDIA GPU ×1 (可选) | 多卡 NVIDIA GPU (用于多卡调度实验) |

### 软件要求

| 软件                 | 版本         | 用途         |
| -------------------- | ------------ | ------------ |
| Kubernetes           | ≥ 1.28       | 容器编排     |
| kubectl              | ≥ 1.28       | K8s CLI      |
| Helm                 | ≥ 3.12       | 包管理       |
| NVIDIA Device Plugin | latest       | GPU 设备管理 |
| HAMi                 | ≥ 2.4 (可选) | GPU 虚拟化   |

---

## K8s 集群搭建

### 方案 A: Minikube (单机测试，推荐)

```bash
# 安装 minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 启动 (需要 Docker)
minikube start --driver=docker --cpus=4 --memory=8192

# 验证
kubectl cluster-info
kubectl get nodes
```

> 注意: Minikube 的 Docker driver 不支持 GPU。GPU 实验需使用 k3s 或裸机 K8s。

### 方案 B: k3s (轻量级，支持 GPU)

```bash
# 安装 k3s
curl -sfL https://get.k3s.io | sh -

# 配置 kubectl
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config

# 验证
kubectl get nodes
```

### 方案 C: Kind (Docker 中运行 K8s)

```bash
# 安装 kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind

# 创建集群
kind create cluster --name gpu-lab

# 验证
kubectl get nodes
```

---

## NVIDIA Device Plugin 安装

```bash
# 使用 Helm 安装
helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm repo update
helm install nvidia-device-plugin nvdp/nvidia-device-plugin \
    --namespace kube-system \
    --create-namespace \
    --set failOnInitError=false

# 验证
kubectl get pods -n kube-system | grep nvidia-device-plugin
kubectl describe node <your-node> | grep nvidia.com/gpu
```

预期看到节点资源中有 `nvidia.com/gpu: 1` (或实际 GPU 数量)。

---

## Kueue 安装 (可选)

```bash
# 安装 Kueue
kubectl apply --server-side -f \
    https://github.com/kubernetes-sigs/kueue/releases/latest/download/manifests.yaml

# 验证
kubectl get pods -n kueue-system
```

---

## 环境验证清单

```bash
# 1. K8s 集群正常
kubectl cluster-info
kubectl get nodes -o wide

# 2. 创建测试 Pod
kubectl run test-pod --image=nginx:alpine --restart=Never
kubectl get pod test-pod
kubectl delete pod test-pod

# 3. GPU Device Plugin 正常
kubectl get pods -n kube-system -l app=nvidia-device-plugin
kubectl describe node <your-node> | grep nvidia.com

# 4. GPU Pod 能正常调度
cat << EOF | kubectl apply -f -
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
EOF

kubectl logs gpu-test
kubectl delete pod gpu-test
```

---

## 常见问题

### Q: GPU Pod 一直 Pending

```bash
# 查看调度事件
kubectl describe pod <pod-name> | grep -A 5 Events

# 常见原因:
# - 节点没有 GPU 资源 (kubectl describe node 查看)
# - Device Plugin 未正常运行
# - GPU 已被其他 Pod 占用
```

### Q: 容器内看不到 GPU

```bash
# 检查环境变量
kubectl exec <pod> -- env | grep NVIDIA

# 检查是否有 --gpus 等效配置
kubectl exec <pod> -- nvidia-smi
```

### Q: k3s 节点 GPU 未上报

```bash
# 确认 NVIDIA Container Toolkit 已安装
sudo apt install -y nvidia-container-toolkit

# 配置 containerd (k3s 默认使用 containerd)
sudo nvidia-ctk runtime configure --runtime=containerd
sudo systemctl restart k3s
```
