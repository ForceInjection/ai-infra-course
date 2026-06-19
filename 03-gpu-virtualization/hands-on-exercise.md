# 模块 3：GPU 虚拟化与容器化实践 — 课堂动手题

## 题目：使用 HAMi 部署 GPU 共享环境

### 题目描述

在 Kubernetes 集群中安装 HAMi，配置 GPU 显存和算力隔离，然后在同一张 GPU 上启动两个容器，验证资源隔离效果。

### 预计时间
20–25 分钟

---

## Part 1: HAMi 环境准备 (5 min)

### Step 1: 确认 HAMi 已安装

```bash
# 查看 HAMi 组件
kubectl get pods -n kube-system | grep hami

# 查看节点 GPU 资源
kubectl describe node <your-node> | grep -A 10 "nvidia.com"
```

预期看到节点上报了 `nvidia.com/gpu`、`nvidia.com/gpumem`、`nvidia.com/gpucores` 等资源。

### Step 2: 确认节点 GPU 信息

```bash
# 查看物理 GPU
kubectl exec -n kube-system $(kubectl get pod -n kube-system -l app=hami-device-plugin -o jsonpath='{.items[0].metadata.name}') -- nvidia-smi
```

---

## Part 2: GPU 共享实验 (15 min)

### Step 1: 创建两个共享 GPU 的 Pod

**Pod A — 申请 2GB 显存 + 30% 算力**:

```yaml
# pod-a.yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod-a
spec:
  containers:
  - name: cuda-app
    image: nvidia/cuda:12.4.0-devel-ubuntu22.04
    command: ["/bin/bash", "-c"]
    args:
      - |
        echo "=== Pod A: GPU Info ==="
        nvidia-smi
        echo ""
        echo "=== Running GPU memory test ==="
        apt-get update -qq && apt-get install -y -qq python3-pip > /dev/null 2>&1
        pip install torch -q
        python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU name: {torch.cuda.get_device_name(0)}')
print(f'Total memory reported: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB')
# Try allocating 1.5 GB
try:
    t = torch.zeros(1500 * 1024 * 1024 // 4, device='cuda')
    print('Allocated 1.5 GB ✓')
except Exception as e:
    print(f'Allocation failed: {e}')
"
        echo "Pod A done. Sleeping..."
        sleep 3600
    resources:
      limits:
        nvidia.com/gpu: 1
        nvidia.com/gpumem: 2048     # 2 GB 显存
        nvidia.com/gpucores: 30     # 30% 算力
```

**Pod B — 申请 2GB 显存 + 30% 算力**:

```yaml
# pod-b.yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod-b
spec:
  containers:
  - name: cuda-app
    image: nvidia/cuda:12.4.0-devel-ubuntu22.04
    command: ["/bin/bash", "-c"]
    args:
      - |
        echo "=== Pod B: GPU Info ==="
        nvidia-smi
        echo ""
        echo "=== Running GPU memory test ==="
        apt-get update -qq && apt-get install -y -qq python3-pip > /dev/null 2>&1
        pip install torch -q
        python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
# Try allocating 3 GB (should fail - exceeds 2 GB limit)
try:
    t = torch.zeros(3000 * 1024 * 1024 // 4, device='cuda')
    print('Allocated 3 GB (unexpected - isolation failed!)')
except Exception as e:
    print(f'Allocation correctly failed: {e}')
print('Memory isolation test passed!')
"
        echo "Pod B done. Sleeping..."
        sleep 3600
    resources:
      limits:
        nvidia.com/gpu: 1
        nvidia.com/gpumem: 2048
        nvidia.com/gpucores: 30
```

### Step 2: 部署并观察

```bash
# 部署两个 Pod
kubectl apply -f pod-a.yaml
kubectl apply -f pod-b.yaml

# 查看 Pod 状态
kubectl get pods -w

# 查看 Pod A 的日志
kubectl logs gpu-pod-a

# 查看 Pod B 的日志
kubectl logs gpu-pod-b
```

### Step 3: 验证显存隔离

```bash
# 在每个 Pod 中查看 nvidia-smi 输出
kubectl exec -it gpu-pod-a -- nvidia-smi
kubectl exec -it gpu-pod-b -- nvidia-smi

# 关键观察: 
# - 两个 Pod 中的 nvidia-smi 显示的显存使用量是否符合配额
# - Pod B 尝试分配 3GB 是否正确失败
```

---

## Part 3: 不使用 HAMi 的对比实验 (可选，5 min)

如果你的 K8s 节点没有安装 HAMi，可以使用 Docker 直接演示 GPU 隔离效果：

```bash
# 容器 A — 不限制
docker run --rm --gpus all nvidia/cuda:12.4.0-devel-ubuntu22.04 \
    python3 -c "import torch; print(torch.cuda.memory_summary())"

# 容器 B — 同时运行，观察显存竞争
docker run --rm --gpus all nvidia/cuda:12.4.0-devel-ubuntu22.04 \
    python3 -c "import torch; t = torch.zeros(5000000000, device='cuda'); print('Allocated 5 GB')"
```

---

## 讲解要点

### 1. HAMi 如何实现显存隔离？
- `LD_PRELOAD` 注入 `libvgpu.so`，hook `cuMemAlloc`
- 每次显存分配请求过来，检查累加用量是否超过配额
- 超过配额 → 返回 `OUT_OF_MEMORY`
- 进程退出 → 释放配额

### 2. 算力限制的令牌桶算法
- 令牌以配额速率生成 (如 30% → 每秒产生 0.3×max_tokens)
- Kernel 启动前需获取令牌，令牌不足则阻塞
- 反馈控制: 监控实际利用率，动态调整令牌速率

### 3. 为什么 nvidia-smi 在容器内可能显示全部显存？
- HAMi 的显存隔离是 CUDA API 层面的，`nvidia-smi` 查询的是硬件层面
- HAMi 最新版本已支持 `nvidia-smi` 输出修正
- 这是「用户态隔离」与「硬件隔离」的本质区别

### 4. 三种共享模式的适用场景
- **HAMi-core (默认)**: 灵活切分，适合大多数场景
- **MIG**: 需要硬件级隔离的生产环境
- **MPS**: 大量小任务高并发，追求最大吞吐量

---

## 清理

```bash
kubectl delete pod gpu-pod-a gpu-pod-b
```
