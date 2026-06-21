# 云原生 AI 基础设施：原理与实践 — 课程设计

> **面向对象**: 高年级本科生
> **课时安排**: 8 次课 × 90 分钟 (模块 4/5 扩展至 120 分钟) ≈ 13 学时
> **课程材料来源**: [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) | [cloud-native-dev](https://github.com/ForceInjection/cloud-native-dev)

---

## 课程简介

本课程系统介绍云原生人工智能基础设施（AI Infra）的核心技术体系。从 Linux 基础与底层容器技术起步，依次覆盖 GPU 硬件架构与 CUDA 编程、GPU 虚拟化与标准化容器化实践、从 Device Plugin 到 DRA 的 Kubernetes 调度演进，以及以 vLLM 为代表的高吞吐推理框架和 KV Cache 加速优化策略。最后从 vLLM Router 到 DeepSeek 生产部署，构建完整的推理服务平台，并探讨 AI Infra 与 Agent Infra 融合的前沿趋势。

**教学策略**: 硬件架构 → 编程模型（全程对比 CPU 编程）→ 动手验证 → 工具链。每个动手环节 1 页引导 PPT + 学生在终端操作，不把实验堆积在最后。

## 课程目录

| 模块 | 主题                                     | 状态     | 核心内容                                                              |
| ---- | ---------------------------------------- | -------- | --------------------------------------------------------------------- |
| 1    | Linux 基础与容器技术入门                 | ✔ 已评审 | Namespace/Cgroup/OverlayFS、Docker 分层                               |
| 2    | GPU 硬件架构与 CUDA 编程入门             | ✔ 已评审 | SM/Tensor Core/HBM/NVLink、CUDA Kernel、Tiling                        |
| 2b   | GPU 内存管理 (高级)                      | ✔ 已评审 | Pinned/Pageable DMA、显存碎片化、跨进程共享                           |
| 3    | GPU 虚拟化与容器化实践                   | ✔ 已评审 | MIG/Time-Slicing/HAMi、LD_PRELOAD CUDA 拦截、NVIDIA CTK               |
| 4    | Kubernetes 入门与 GPU 工作负载调度       | ✔ 已评审 | 120min/52页, K8s基础+Device Plugin+DRA+Kueue+GPU调度实战              |
| 5    | 大模型推理框架入门：以 vLLM 为例         | ✔ 已评审 | 120min/54页, PagedAttention+nano-vllm源码+Continuous Batching         |
| 6    | 大模型推理加速实践：KV Cache 原理与优化  | ✔ 已评审 | 90min/45页, KV Cache公式+Offloading+量化+LMCache+MoonCake             |
| 7    | 云原生 AI 推理基础设施进阶：从引擎到平台 | ✔ 已评审 | 90min/45页, AI网关(vLLM Router+Semantic Router)+EP/TP/PP部署+可观测性 |
| 8    | 课程总结与 AI Infra 前沿展望             | ✔ 已评审 | 90min/40页, 7模块回顾串联+前沿趋势+Agent Infra+大作业(3方向选1)       |

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
├── 02b-gpu-memory/                   # 模块 2b: GPU 内存管理 (高级)
│   ├── README.md
│   ├── code/
│   │   ├── README.md
│   │   └── 01_dma_bandwidth.py
│   └── visuals/
│       └── gpu-memory-visual.html
├── 03-gpu-virtualization/              # 模块 3
│   ├── README.md
│   ├── code/
│   │   ├── README.md
│   │   ├── 01_mymalloc.c              #   LD_PRELOAD malloc hook
│   │   └── 02_test_malloc.c           #   配额测试程序
│   ├── visuals/
│   │   └── ld-preload-flow.html       #   LD_PRELOAD 拦截流程
│   ├── hands-on-exercise.md
│   ├── homework.md
│   ├── lab-environment.md
│   ├── syllabus.md                  #   (gitignored)
│   └── ppt-outline.md               #   (gitignored)
├── 04-kubernetes-gpu/                   # 模块 4: K8s 入门与 GPU 调度
│   ├── README.md
│   ├── code/
│   │   ├── README.md
│   │   ├── 01_nginx_demo.yaml           #   Nginx Deployment + Service
│   │   ├── 02_gpu_pod.yaml              #   GPU Pod — nvidia-smi 测试
│   │   └── 03_gpu_deploy.yaml           #   GPU Deployment — 生产级工作负载
│   ├── visuals/
│   │   └── k8s-gpu-flow.html            #   GPU 调度全链路 7 步交互动画
│   ├── hands-on-exercise.md
│   ├── homework.md
│   ├── lab-environment.md
│   ├── syllabus.md                      #   (gitignored)
│   └── ppt-outline.md                   #   (gitignored)
├── 05-vllm-inference/                   # 模块 5: vLLM 推理框架
│   ├── README.md
│   ├── code/
│   │   ├── README.md
│   │   └── trace_nanovllm.py            #   nano-vllm 执行追踪脚本
│   ├── hands-on-exercise.md
│   ├── homework.md
│   ├── lab-environment.md
│   ├── syllabus.md                      #   (gitignored)
│   └── ppt-outline.md                   #   (gitignored)
├── 06-kvcache-optimization/             # 模块 6: KV Cache 优化
│   ├── README.md
│   ├── code/
│   │   ├── README.md
│   │   ├── calculate_qwen3_memory.py    #   通用 GQA/MHA 显存估算
│   │   ├── calculate_deepseek_v4_memory.py  # DeepSeek V4 专用估算
│   │   ├── qwen3_06b_config.json
│   │   └── deepseek_v4_pro_config.json
│   ├── hands-on-exercise.md
│   ├── homework.md
│   ├── lab-environment.md
│   ├── syllabus.md                      #   (gitignored)
│   └── ppt-outline.md                   #   (gitignored)
├── 07-maas-infra/                        # 模块 7: 从推理引擎到服务平台
│   ├── README.md
│   ├── code/
│   │   ├── README.md
│   │   └── ai_gateway.py                #   Flask 简易 AI 网关 (~140行)
│   ├── hands-on-exercise.md
│   ├── homework.md
│   ├── lab-environment.md
│   ├── syllabus.md                      #   (gitignored)
│   └── ppt-outline.md                   #   (gitignored)
└── 08-summary-outlook/                    # 模块 8: 课程总结与展望
    ├── README.md
    ├── syllabus.md                      #   (gitignored)
    ├── ppt-outline.md                   #   (gitignored)
    ├── course-project.md                #   课程大作业 (3方向选1)
    └── code/                            #   大作业骨架代码 + 报告模板
        ├── README.md
        ├── REPORT_TEMPLATE.md
        ├── gpu-container-hook/          #     方向 A: 容器+拦截
        ├── k8s-gateway/                 #     方向 B: K8s 调度
        └── kvcache-simulator/           #     方向 C: KV Cache
```

## 每节课包含

| 文件                   | 说明                                  |
| ---------------------- | ------------------------------------- |
| `code/`                | 配套代码和脚本，含 README             |
| `visuals/`             | 可视化 HTML，课堂演示用               |
| `hands-on-exercise.md` | 课堂动手题：题目、步骤、讲解要点      |
| `homework.md`          | 课后练习：题目、要求、评分标准        |
| `lab-environment.md`   | 实验环境说明：硬件/软件要求、搭建步骤 |

## 实验环境

| 模块                  | 运行方式                                                                                            |
| --------------------- | --------------------------------------------------------------------------------------------------- |
| 模块 1 (Bash)         | 直接执行 `.sh` 脚本，需要 `sudo`                                                                    |
| 模块 2 (CUDA)         | 本地 `make all && make run`，或使用 `bash cuda-docker all`（Docker 镜像需包含 CUDA Toolkit + nvcc） |
| 模块 3 (C/LD_PRELOAD) | `gcc -shared -fPIC -o libmymalloc.so 01_mymalloc.c -ldl`，`LD_PRELOAD=./libmymalloc.so <cmd>`       |
| 模块 4 (K8s)          | minikube / k3s / kind 任选，`kubectl apply -f code/*.yaml`，GPU 实验需 NVIDIA Device Plugin         |
| 模块 5 (vLLM)         | nano-vllm: `pip install git+https://github.com/ForceInjection/nano-vllm.git`；vLLM: 需 GPU          |
| 模块 6 (KV Cache)     | 显存计算脚本：Python 3.8+，零依赖，无需 GPU；LMCache 实验：需 vLLM + GPU                            |
| 模块 7 (AI 网关)      | Flask 网关：`pip install flask requests` + `python ai_gateway.py`；后端需 vLLM + GPU                |

## 材料来源

- **AI-fundamentals**: [github.com/ForceInjection/AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals)
- **cloud-native-dev**: [github.com/ForceInjection/cloud-native-dev](https://github.com/ForceInjection/cloud-native-dev)
- **nano-vllm**: [github.com/ForceInjection/nano-vllm](https://github.com/ForceInjection/nano-vllm)
