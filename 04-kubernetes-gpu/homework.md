# 模块 4：Kubernetes 入门与 GPU 工作负载调度 — 课后练习

## 题目：K8s GPU 作业队列与多卡调度

### 目标

在 K8s 集群中配置 Kueue 作业队列，实现 GPU 资源的排队和优先级调度。然后设计一个多 GPU 的调度场景，理解拓扑感知调度的价值。

### 截止时间

下次课前 (一周)

---

## 基础任务 (必做)

### 任务 1: 配置 Kueue 作业队列

安装 Kueue 并配置 GPU 资源的作业队列：

```yaml
# resource-flavor.yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata:
  name: default-gpu-flavor
---
# cluster-queue.yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: gpu-cluster-queue
spec:
  namespaceSelector: {}
  resourceGroups:
  - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
    flavors:
    - name: default-gpu-flavor
      resources:
      - name: "cpu"
        nominalQuota: 16
      - name: "memory"
        nominalQuota: 32Gi
      - name: "nvidia.com/gpu"
        nominalQuota: 1    # 只有 1 张 GPU 的配额
---
# local-queue.yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata:
  name: gpu-queue
  namespace: default
spec:
  clusterQueue: gpu-cluster-queue
```

创建两个 GPU Job，观察排队行为：

```yaml
# job-1.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: gpu-job-1
  labels:
    kueue.x-k8s.io/queue-name: gpu-queue
spec:
  suspend: true  # Kueue 会接管调度
  parallelism: 1
  template:
    spec:
      containers:
      - name: job
        image: nvidia/cuda:12.4.0-base-ubuntu22.04
        command: ["nvidia-smi"]
        resources:
          limits:
            nvidia.com/gpu: 1
      restartPolicy: Never
```

```bash
# 提交两个 Job
kubectl apply -f job-1.yaml
# 复制 job-1.yaml → job-2.yaml，改名为 gpu-job-2
kubectl apply -f job-2.yaml

# 观察状态 (一个 Running，一个 Suspended/Pending)
kubectl get jobs
kubectl get workload -o wide  # Kueue 的 Workload 对象
```

记录实验过程: 哪个 Job 先运行、为什么、队列中的等待时间。

### 任务 2: 探索 GPU 拓扑感知

在有多张 GPU 的节点上运行：

```bash
# 查看 GPU 拓扑
nvidia-smi topo -m

# 记录输出，回答:
# 1. 哪些 GPU 对之间是 PIX (同 PCIe Switch)?
# 2. 哪些 GPU 对之间是 SYS (跨 NUMA Node)?
# 3. 如果要运行一个 2 卡训练任务，应该选哪两张 GPU?
```

如果只有单 GPU 节点，使用以下命令模拟理解：

```bash
# 查看 PCIe 拓扑
lspci -t -v | grep -i nvidia

# 查看 NUMA 拓扑
numactl --hardware
```

---

## 进阶任务 (选做)

### 任务 3: 实现弹性 GPU 调度

使用 KEDA (Kubernetes Event-Driven Autoscaling) 或 HPA，基于 GPU 利用率自动扩缩容推理服务：

```bash
# 安装 KEDA
kubectl apply --server-side -f https://github.com/kedacore/keda/releases/latest/download/keda.yaml

# 配置基于 Prometheus GPU 指标的 ScaledObject
```

设计目标: 当 GPU 利用率 > 70% 时扩容，< 30% 时缩容。

### 任务 4: DRA 实验

如果 K8s 版本 ≥ 1.31，尝试 DRA 的 GPU 动态分配：

```yaml
apiVersion: resource.k8s.io/v1alpha3
kind: ResourceClaim
metadata:
  name: gpu-claim
spec:
  devices:
    requests:
    - name: gpu
      deviceClassName: nvidia-gpu
      count: 1
```

---

## 提交要求

1. 提交 Kueue 配置文件和实验过程截图
2. 提交 GPU 拓扑分析报告 (含 `nvidia-smi topo -m` 输出解读)
3. 回答以下问题 (≤ 1 页):
   - Device Plugin 和 DRA 的本质区别是什么？
   - 为什么 GPU 资源不能像 CPU 一样 oversubscribe？
   - Gang Scheduling 在分布式训练中为什么重要？
   - (选做) KEDA 自动扩缩容的实现思路

---

## 评分标准

| 维度 | 权重 | 要求 |
|------|------|------|
| 任务 1-2 完成度 | 60% | 成功配置 Kueue 并观察排队行为，完成拓扑分析 |
| 分析深度 | 20% | 问题回答有深度、有依据 |
| 文档质量 | 10% | 截图清晰、描述完整 |
| 进阶任务 | 10% | 完成至少一项进阶任务 |

---

## 参考资料

- AI-fundamentals: `04_cloud_native_ai_platform/k8s/02_nvidia_k8s_device_plugin_analysis.md`
- AI-fundamentals: `04_cloud_native_ai_platform/k8s/03_kueue_hami_integration.md`
- AI-fundamentals: `04_cloud_native_ai_platform/k8s/04_lws_intro.md`
- [Kueue Documentation](https://kueue.sigs.k8s.io/docs/)
- [NVIDIA Device Plugin](https://github.com/NVIDIA/k8s-device-plugin)
