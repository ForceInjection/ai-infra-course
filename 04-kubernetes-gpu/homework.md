# 模块 4：Kubernetes 入门与 GPU 工作负载调度 — 课后练习

## 题目：K8s GPU 调度实战与分析

### 截止时间

模块 5 课前

---

## 任务 1: K8s 基础练习 (必做)

在本地 minikube/k3s/kind 集群上完成以下操作，截图记录每一步：

1. 创建 Namespace `gpu-homework`
2. 在该 Namespace 中创建一个 Deployment（镜像 `nginx:alpine`，3 副本）
3. 创建一个 Service（类型 ClusterIP）暴露该 Deployment
4. 扩容到 5 副本 → 缩容到 2 副本
5. 执行一次滚动更新（改镜像 tag 为 `nginx:1.25-alpine`）
6. 用 `kubectl describe` 查看 Deployment 的 Events，解释你看到了什么

提交: 每一步的 kubectl 命令 + 关键输出截图。

## 任务 2: K8s GPU 设备管理机制分析 (必做)

阅读 [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/04_cloud_native_ai_platform/k8s/02_nvidia_k8s_device_plugin_analysis.md)，回答：

1. Device Plugin 的 `ListAndWatch` 和 `Allocate` 接口各自做什么？画出它们的调用时序图。
2. 如果某个节点的 GPU 被所有 Pod 占满，新来的 Pod 声明 `nvidia.com/gpu: 1` 会发生什么？结合调度器流程解释。
3. DRA 相比 Device Plugin 的核心改进是什么？从**分配时机**和**拓扑感知**两个维度分析。
4. 为什么说 ResourceClaim 之于 GPU 类似于 PVC 之于存储？找到共同点和差异点。

## 任务 3: GPU 调度策略设计 (必做)

假设你有以下 GPU 集群:

- 4 个节点，每个节点 8 张 A100
- 节点 1-2 的 GPU 通过 NVSwitch 全互联 (同一域)
- 节点 3-4 的 GPU 通过 NVSwitch 全互联 (另一域)
- 跨节点的 GPU 通过 InfiniBand 互联

你需要运行以下工作负载:

- **Job A**: 分布式训练 (8 卡，TP=8，必须在同一 NVSwitch 域)
- **Job B**: 推理服务 (2 卡，无特殊拓扑要求)
- **Job C**: 推理服务 (2 卡，无特殊拓扑要求)

请回答:

1. 为 Job A/B/C 设计调度方案，说明每个 Job 应该调度到哪些节点、为什么。
2. 如果使用 Kueue，如何配置 ResourceFlavor 和 ClusterQueue 来区分两个 NVSwitch 域？
3. 如果 Job A 还在运行，Job B 和 C 先后到达，K8s 默认调度器会怎么放置它们？如果使用 Binpack 策略呢？

---

## 进阶任务 (选做)

### 任务 4: 部署 Kueue 并测试

在 K8s 集群中部署 Kueue，创建:

- 一个 ResourceFlavor (你的 GPU 节点组)
- 一个 ClusterQueue (配额: 2 GPU)
- 提交 3 个 Job (每个声明 1 GPU)，观察第 3 个 Job 的排队行为

### 任务 5: DRA 实验

如果 K8s 版本 ≥ 1.31，尝试创建 ResourceClaim 并部署引用 Claim 的 Pod。记录 Claim 的状态变化过程。

---

## 提交要求

1. 任务 1: 命令 + 截图
2. 任务 2: 分析回答 (≤ 2 页)
3. 任务 3: 调度方案设计 (≤ 1 页)
4. (选做) 任务 4 或 5

---

## 评分标准

| 维度              | 权重 | 要求                      |
| ----------------- | ---- | ------------------------- |
| 任务 1 (K8s 基础) | 30%  | 6 步操作正确完成          |
| 任务 2 (机制分析) | 30%  | 4 题回答准确 + 时序图正确 |
| 任务 3 (调度设计) | 25%  | 方案合理有依据            |
| 文档质量          | 10%  | 截图清晰、描述完整        |
| 进阶任务          | 5%   | 完成至少一项              |

---

## 参考资料

- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/04_cloud_native_ai_platform/k8s/) 全部文件
- [Kubernetes DRA Documentation](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
- [Kueue Documentation](https://kueue.sigs.k8s.io/docs/)
