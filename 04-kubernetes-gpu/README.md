# 模块 4：Kubernetes 入门与 GPU 工作负载调度

> 120 分钟 &nbsp;|&nbsp; 52 页 PPT &nbsp;|&nbsp; 3 个 YAML 文件 &nbsp;|&nbsp; 1 个可视化 HTML

## 目录结构

```text
04-kubernetes-gpu/
├── README.md                    # 本文件
├── syllabus.md                  # 教学大纲 (120 分钟时间分配)
├── ppt-outline.md               # PPT 大纲 (52 页)
├── hands-on-exercise.md         # 课堂动手题 (3 个实验)
├── homework.md                  # 课后练习 (3 个任务)
├── lab-environment.md           # 实验环境搭建说明
├── code/                        # 配套 YAML 文件 (3 个)
│   ├── README.md                #   使用说明 + 运行命令
│   ├── 01_nginx_demo.yaml       #   Nginx Deployment + Service (PPT 第 16 页 [动手])
│   ├── 02_gpu_pod.yaml          #   GPU Pod — nvidia-smi 测试 (PPT 第 45 页 [动手 1])
│   └── 03_gpu_deploy.yaml       #   GPU Deployment — 生产级工作负载 (PPT 第 45-46 页 [动手 1+2])
└── visuals/                     # 可视化 HTML (1 个)
    └── k8s-gpu-flow.html        #   K8s GPU 调度全链路: 7 步交互动画 (PPT 第 48 页)
```

## 可视化 HTML

| 文件                | 用途                                | 教学场景                                                                                                                 |
| ------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| [`k8s-gpu-flow.html`](visuals/k8s-gpu-flow.html) | K8s GPU 调度全链路 — 7 步可交互动画 | 第 48 页全链路回顾时打开，逐步骤讲解: kubectl → API Server → Scheduler → kubelet → Device Plugin → NVIDIA CTK → 容器启动 |

**交互方式**: 点击「下一步」逐步查看每个组件的职责和日志；点击「自动」7 步自动播放 (每步 1.2s)。右侧面板显示每步的详细解释。

## 教学流程

| 部分                   | 时长   | PPT 页 | 重点内容                                          | 动手                                                      |
| ---------------------- | ------ | ------ | ------------------------------------------------- | --------------------------------------------------------- |
| K8s 入门               | 35 min | 3–18   | Pod/Deployment/Service、声明式、控制循环          | 第 16 页: K8s 初体验 — 部署 Nginx (5min)                  |
| Device Plugin 机制     | 25 min | 19–28  | ListAndWatch/Allocate、NVIDIA DP 时序、CDI 演进   | —                                                         |
| DRA — 动态资源分配     | 30 min | 29–40  | ResourceClaim/ResourceClass、拓扑感知、Kueue 队列 | 第 47 页: DRA Claim 概念演示 (可选, 8min)                 |
| GPU 调度策略与动手实践 | 30 min | 41–52  | Filter/Score/Bind、GPU 拓扑调度、全链路回顾       | 第 45 页: 部署 GPU Pod (5min) + 第 46 页: 资源争抢 (7min) |

## 课程简介

本模块是课程的转折点 —— 从单机 GPU 操作走向集群级 GPU 编排。

**核心问题**: 「你有 100 台 GPU 服务器，怎么管理 1000 个 GPU 应用？」

**解答路线**:

1. **K8s 入门** (第一部分): 从零讲起 Pod/Deployment/Service，建立声明式思维
2. **Device Plugin** (第二部分): K8s 如何发现和管理 GPU？gRPC 接口 + 设备注入全流程
3. **DRA + Kueue** (第三部分): 下一代设备管理 — 拓扑感知、多设备组合、作业排队
4. **GPU 调度实战** (第四部分): 亲手部署 GPU Pod、观察资源争抢、回顾全链路

**与前序模块的关系**:

- 模块 1 (Linux 容器): 容器基础 → 本模块的容器运行时基础
- 模块 2 (GPU/CUDA): GPU 硬件理解 → 本模块的 GPU 拓扑调度基础
- 模块 3 (GPU 虚拟化): HAMi LD_PRELOAD 机制 → 本模块 HAMi Device Plugin 调度

**与后续模块的关系**:

- 模块 5 (vLLM 推理): GPU 调度管的是"GPU 给谁用"，vLLM 管的是"GPU 怎么用更高效"

## 实验环境

| 方式        | 说明                              |
| ----------- | --------------------------------- |
| Minikube    | 单机 K8s 体验 (不支持 GPU)        |
| k3s         | 轻量级 K8s，支持 GPU              |
| Kind        | Docker 中运行 K8s (部分 GPU 支持) |
| 可视化 HTML | 浏览器直接打开，无需服务器        |

详见 [`lab-environment.md`](lab-environment.md)。

## 所需软件

| 软件                 | 版本         | 用途                              |
| -------------------- | ------------ | --------------------------------- |
| Kubernetes           | ≥ 1.28       | 容器编排平台                      |
| kubectl              | ≥ 1.28       | K8s 命令行工具                    |
| Helm                 | ≥ 3.12       | 包管理 (安装 Device Plugin/Kueue) |
| NVIDIA Device Plugin | latest       | GPU 设备发现与管理                |
| Kueue                | ≥ 0.6 (可选) | 作业级队列管理                    |
| HAMi                 | ≥ 2.4 (可选) | GPU 虚拟化 (配合模块 3)           |

## 动手实验

| 实验                 | 时长  | 主题               | 核心体验                                                 |
| -------------------- | ----- | ------------------ | -------------------------------------------------------- |
| 实验 1: K8s 初体验   | 5 min | Nginx 部署         | 体验 kubectl + Pod/Deployment/Service 三个核心对象       |
| 实验 2: GPU Pod 部署 | 5 min | GPU 声明式调度     | 写 `nvidia.com/gpu: 1` → 自动找 GPU 节点 → 验证 GPU 可见 |
| 实验 3: GPU 资源争抢 | 7 min | 资源不足时调度行为 | 超量声明 GPU → 观察 Pending → 读 Events 理解排队机制     |

## 课后作业

| 作业                 | 难度 | 主题                                                   |
| -------------------- | ---- | ------------------------------------------------------ |
| 作业 1: K8s 实践     | ★★☆  | 部署 Nginx + GPU 应用全流程                            |
| 作业 2: 机制分析     | ★★★  | 阅读 NVIDIA Device Plugin 源码，画出 Allocate 调用时序 |
| 作业 3: 调度方案设计 | ★★★★ | 设计支持 GPU 拓扑感知的调度方案                        |

详见 [`homework.md`](homework.md)。

## 参考来源

- [Kubernetes 官方文档](https://kubernetes.io/docs/concepts/) — Pod/Deployment/Service 等核心概念
- [NVIDIA k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin) — NVIDIA Device Plugin 源码
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) — GPU 容器注入机制
- [Kueue](https://kueue.sigs.k8s.io/) — 作业级队列管理
- [DRA KEP](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/3063-dynamic-resource-allocation) — Dynamic Resource Allocation 设计提案
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) — K8s 系列分析文章
