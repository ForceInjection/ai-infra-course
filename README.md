# 云原生 AI 基础设施：原理与实践 — 课程设计

> **面向对象**: 高年级本科生
> **课时安排**: 8 次课 × 90 分钟 = 12 学时
> **课程材料来源**: [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) | [cloud-native-dev](https://github.com/ForceInjection/cloud-native-dev)

---

## 课程简介

本课程系统介绍云原生人工智能基础设施（AI Infra）的核心技术体系。从 Linux 基础与底层容器技术起步，依次覆盖 GPU 硬件架构与 CUDA 编程、GPU 虚拟化与标准化容器化实践、从 Device Plugin 到 DRA 的 Kubernetes 调度演进，以及以 vLLM 为代表的高吞吐推理框架和 KV Cache 加速优化策略。最后延展至 MaaS 场景下的 AI 网关等关键组件，并探讨 AI Infra 与 Agent Infra 融合的前沿趋势。

**教学策略**: 硬件架构 → 编程模型（全程对比 CPU 编程）→ 动手验证 → 工具链。每个动手环节 1 页引导 PPT + 学生在终端操作，不把实验堆积在最后。

## 课程目录

| 模块 | 主题                                    | 状态     | 核心内容                                       |
| ---- | --------------------------------------- | -------- | ---------------------------------------------- |
| 1    | Linux 基础与容器技术入门                | ✔ 已评审 | Namespace/Cgroup/OverlayFS、Docker 分层        |
| 2    | GPU 硬件架构与 CUDA 编程入门            | ✔ 已评审 | SM/Tensor Core/HBM/NVLink、CUDA Kernel、Tiling |
| 3    | GPU 虚拟化与容器化实践                  | 待评审   | HAMi、NVIDIA Container Toolkit                 |
| 4    | Kubernetes 入门与 GPU 工作负载调度      | 待评审   | Device Plugin、DRA、Kueue                      |
| 5    | 大模型推理框架入门：以 vLLM 为例        | 待评审   | PagedAttention、Continuous Batching            |
| 6    | 大模型推理加速实践：KV Cache 原理与优化 | 待评审   | KV Cache、LMCache、量化压缩                    |
| 7    | 云原生 AI 推理基础设施进阶：构建 MaaS   | 待评审   | AI 网关、路由、弹性伸缩                        |
| 8    | 课程总结与 AI Infra 前沿展望            | 待评审   | Agent Infra、AI Native                         |

## 目录结构

```text
ai-infra-course/
├── README.md                         # 本文件
├── outline.md                        # 原始课程大纲
├── .gitignore                        # 排除 syllabus.md / ppt-outline.md / *.pptx / 编译产物
├── 01-linux-containers/              # 模块 1
│   ├── code/                         #   配套 Bash 脚本 (4个)
│   │   ├── README.md                 #     编译运行说明 + 预期输出
│   │   ├── 01_namespace_demo.sh
│   │   ├── 02_cgroup_demo.sh
│   │   ├── 03_overlayfs_demo.sh
│   │   └── 04_docker_layer_demo.sh
│   ├── README.md                    #   模块说明
│   ├── visuals/                     #   可视化 HTML (4个)
│   │   ├── overlayfs-demo.html      #     OverlayFS + COW
│   │   ├── pid-namespace-demo.html  #     PID Namespace 双视角
│   │   ├── docker-run-gpus-all.html #     docker run 全链路
│   │   └── containerd-architecture.html # containerd 架构
│   ├── hands-on-exercise.md         #   课堂动手题
│   ├── homework.md                  #   课后练习
│   ├── lab-environment.md           #   实验环境说明
│   ├── syllabus.md                  #   教学大纲 (gitignored)
│   └── ppt-outline.md               #   PPT 大纲 (gitignored)
├── 02-gpu-cuda/                      # 模块 2
│   ├── code/                         #   配套 CUDA 源码 (4个)
│   │   ├── README.md                 #     编译运行说明 + 预期输出
│   │   ├── Makefile                  #     一键编译
│   │   ├── cuda-docker               #     Docker 编译运行脚本
│   │   ├── 01_vec_add.cu
│   │   ├── 02_matmul_naive.cu
│   │   ├── 03_matmul_tiled.cu
│   │   └── 04_device_query.cu
│   ├── visuals/                     #   可视化 HTML (4个)
│   │   ├── gpu-architecture.html    #     GPU 逻辑架构全景
│   │   ├── cuda-thread-hierarchy.html #   Grid→Block→Warp→Thread
│   │   ├── shared-memory-tiling.html  #   Shared Memory Tiling
│   │   └── thread-index-mapping.html  #   线程索引映射 (1D/2D/3D)
│   ├── hands-on-exercise.md
│   ├── homework.md
│   ├── lab-environment.md
│   ├── syllabus.md                  #   (gitignored)
│   └── ppt-outline.md               #   (gitignored)
├── 03-gpu-virtualization/
├── 04-kubernetes-gpu/
├── 05-vllm-inference/
├── 06-kvcache-optimization/
├── 07-maas-infra/
└── 08-summary-outlook/
```

## 每节课包含

| 文件                   | 说明                                        | 是否提交 |
| ---------------------- | ------------------------------------------- | -------- |
| `code/`                | 配套代码和脚本，含 README                   | ✔        |
| `visuals/`             | 可视化 HTML，课堂演示用                     | ✔        |
| `hands-on-exercise.md` | 课堂动手题：题目、步骤、讲解要点            | ✔        |
| `homework.md`          | 课后练习：题目、要求、评分标准              | ✔        |
| `lab-environment.md`   | 实验环境说明：硬件/软件要求、搭建步骤       | ✔        |
| `syllabus.md`          | 教学大纲：知识点、90 分钟时间分配、教学目标 | — (本地) |
| `ppt-outline.md`       | PPT 大纲：50+ 页，每页内容、排版建议        | — (本地) |
| `*.pptx`               | 生成的课件 PPT                              | — (本地) |

## 实验环境

| 模块          | 运行方式                                                                                            |
| ------------- | --------------------------------------------------------------------------------------------------- |
| 模块 1 (Bash) | 直接执行 `.sh` 脚本，需要 `sudo`                                                                    |
| 模块 2 (CUDA) | 本地 `make all && make run`，或使用 `bash cuda-docker all`（Docker 镜像需包含 CUDA Toolkit + nvcc） |

## 材料来源

- **AI-fundamentals**: [github.com/ForceInjection/AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals)
- **cloud-native-dev**: [github.com/ForceInjection/cloud-native-dev](https://github.com/ForceInjection/cloud-native-dev)
- **nano-vllm**: [github.com/GeeeekExplorer/nano-vllm](https://github.com/GeeeekExplorer/nano-vllm)
