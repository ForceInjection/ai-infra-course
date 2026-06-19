# 模块 4：Kubernetes 入门与 GPU 工作负载调度 — 课堂动手题

## 题目：在 Kubernetes 中部署 GPU 推理服务

### 题目描述

在 Kubernetes 集群中创建一个 Deployment，部署 GPU 推理服务，配置 Service 暴露 API，验证 GPU 资源声明和调度效果。

### 预计时间
20–25 分钟

---

## Step 1: 验证集群与 GPU 资源 (3 min)

```bash
# 1. 确认集群状态
kubectl get nodes
kubectl get pods -n kube-system | grep nvidia

# 2. 查看节点 GPU 资源
kubectl describe node $(kubectl get nodes -o jsonpath='{.items[0].metadata.name}') | grep -A 5 "nvidia.com"
```

预期看到 `nvidia.com/gpu: 1` (或实际 GPU 数量)。

---

## Step 2: 创建 GPU Deployment (8 min)

创建文件 `gpu-inference.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-inference
  labels:
    app: gpu-inference
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
      - name: gpu-app
        image: nvidia/cuda:12.4.0-devel-ubuntu22.04
        command: ["/bin/bash", "-c"]
        args:
          - |
            echo "=== GPU Info ==="
            nvidia-smi
            echo ""
            echo "=== GPU Compute Capability ==="
            /usr/local/cuda/extras/demo_suite/deviceQuery 2>/dev/null | grep -E "Device|CUDA Capability" || echo "deviceQuery not available"
            echo ""
            echo "=== Running simple CUDA test ==="
            cat > /tmp/test.cu << 'CUEOF'
            #include <stdio.h>
            __global__ void add(int *a, int *b, int *c) {
                int i = threadIdx.x;
                c[i] = a[i] + b[i];
            }
            int main() {
                int a[4] = {1,2,3,4}, b[4] = {5,6,7,8}, c[4];
                int *d_a, *d_b, *d_c;
                cudaMalloc(&d_a, 16); cudaMalloc(&d_b, 16); cudaMalloc(&d_c, 16);
                cudaMemcpy(d_a, a, 16, cudaMemcpyHostToDevice);
                cudaMemcpy(d_b, b, 16, cudaMemcpyHostToDevice);
                add<<<1,4>>>(d_a, d_b, d_c);
                cudaMemcpy(c, d_c, 16, cudaMemcpyDeviceToHost);
                printf("GPU Result: %d %d %d %d\\n", c[0], c[1], c[2], c[3]);
                cudaFree(d_a); cudaFree(d_b); cudaFree(d_c);
                return 0;
            }
            CUEOF
            nvcc -o /tmp/test /tmp/test.cu && /tmp/test
            echo ""
            echo "=== Service ready, sleeping ==="
            sleep 3600
        resources:
          limits:
            nvidia.com/gpu: 1
      restartPolicy: Always
```

```bash
# 部署
kubectl apply -f gpu-inference.yaml

# 查看创建过程
kubectl get pods -w

# 查看日志
kubectl logs -l app=gpu-inference
```

### 观察点:
- Pod 从 Pending → ContainerCreating → Running 的状态变化
- `nvidia-smi` 输出确认 GPU 可用
- CUDA 程序运行结果正确

---

## Step 3: 创建 Service 暴露服务 (5 min)

```yaml
# gpu-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: gpu-inference-svc
spec:
  selector:
    app: gpu-inference
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
```

```bash
kubectl apply -f gpu-service.yaml
kubectl get svc gpu-inference-svc
```

> 由于这是一个调试用的 Pod，没有实际监听端口。Service 的验证主要看 endpoints 是否关联到 Pod。

```bash
kubectl get endpoints gpu-inference-svc
```

---

## Step 4: 模拟 GPU 资源争抢 (5 min)

```bash
# 扩容到 3 个副本（如果只有 1 张 GPU，则 2 个会 Pending）
kubectl scale deployment gpu-inference --replicas=3

# 观察 Pod 状态
kubectl get pods -l app=gpu-inference -o wide

# 查看 Pending Pod 的原因
kubectl describe pod $(kubectl get pods -l app=gpu-inference --field-selector=status.phase=Pending -o jsonpath='{.items[0].metadata.name}') | grep -A 10 Events
```

### 观察点:
- 只有 1 个 Pod Running（如果只有 1 张 GPU）
- Pending Pod 的事件显示: `0/1 nodes are available: 1 Insufficient nvidia.com/gpu`
- 这演示了 K8s GPU 资源管理的核心功能

---

## Step 5: 添加 GPU 节点亲和性（进阶，5 min）

```yaml
# 在 Deployment spec.template.spec 中添加
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: nvidia.com/gpu.product
          operator: In
          values:
          - NVIDIA-GeForce-RTX-4090
          - NVIDIA-A100-SXM4-40GB
```

```bash
# 查看节点的 GPU 型号标签
kubectl get nodes -o json | jq '.items[].metadata.labels | with_entries(select(.key | startswith("nvidia.com")))'
```

---

## 讲解要点

### 1. K8s 资源管理机制
- `requests` vs `limits`: requests 用于调度决策，limits 用于运行时限制
- GPU 只能设 limits（不能 oversubscribe）
- 资源不足时，Scheduler 选择其他节点或让 Pod Pending

### 2. Device Plugin 如何工作
- 每个 Node 运行一个 Device Plugin Pod (DaemonSet)
- Device Plugin 通过 NVML 发现 GPU → 上报给 kubelet
- kubelet 在调度时计入 `nvidia.com/gpu` 资源
- 容器启动时，Device Plugin 注入环境变量 + NVIDIA Container Toolkit 注入设备

### 3. 为什么 GPU 不能 Oversubscribe？
- CPU 和内存可以超卖 (实际使用 < 声明上限)
- GPU 显存是硬分配，不能超卖 (会导致 OOM)
- 这就是需要 HAMi 等 GPU 虚拟化方案的原因

### 4. 完整的调度链路
```
用户创建 Pod (声明 GPU)
  → API Server 写入 etcd
  → Scheduler watch 到未调度的 Pod
  → Filter: 节点是否有足够的 nvidia.com/gpu?
  → Score: 哪个节点更合适?
  → Bind: 将 Pod 绑定到选中节点
  → kubelet 创建容器
  → Device Plugin Allocate → 注入 GPU
```

---

## 清理

```bash
kubectl delete deployment gpu-inference
kubectl delete service gpu-inference-svc
```
