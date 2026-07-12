# 云原生 AI 基础设施：原理与实践

一个 Chat 请求从浏览器到 GPU 硬件，穿越 7 层技术栈。8 次课，逐层深入，从 Linux 容器到推理服务平台。

**[交互式课程全景图 →](course-overview.html)** — 点击任意模块，7 层请求链路与课程卡片联动高亮。

---

## 这门课讲什么

适合高年级本科生或初级 Infra 工程师。需要：Linux 命令行基本使用、Python 编程基础。不需要提前会 CUDA/K8s/vLLM——每个模块从零讲起。

每一层做了什么？为什么这么设计？8 个模块，每个回答一个核心问题：

| 模块                                                      | 核心问题                                    | 你会做什么                                                                                             |
| --------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| [**1. Linux 容器**](01-linux-containers/README.md)        | 怎么把应用和 GPU 驱动打包在一起？           | 手写 Namespace 隔离、看懂 OverlayFS 分层、追踪 `docker run --gpus all` 完整调用链                      |
| [**2. GPU & CUDA**](02-gpu-cuda/README.md)                | GPU 为什么比 CPU 快 100 倍？                | 从 CUDA 线程层次写到 Shared Memory Tiling，naive vs tiled 矩阵乘法加速 1.8×                            |
| [**2b. GPU 内存**](02b-gpu-memory/README.md)              | Pinned 和 Pageable 内存差多少？             | 实测 DMA 带宽：pinned 55 GB/s vs pageable 22 GB/s——2.5 倍的工程决策依据                                |
| [**3. GPU 虚拟化**](03-gpu-virtualization/README.md)      | 一张 A100 怎么分给 10 个人用？              | LD_PRELOAD 拦截 `cudaMalloc`，手写显存配额管理器 + 令牌桶限流，类比理解 HAMi 的 CUDA API Hook 原理     |
| [**4. K8s GPU 调度**](04-kubernetes-gpu/README.md)        | 100 台 GPU 服务器怎么管？                   | 从 `kubectl apply` 到容器内 `nvidia-smi`——追踪 Device Plugin 7 步 gRPC 全链路，配置 HPA 弹性伸缩       |
| [**5. vLLM 推理引擎**](05-vllm-inference/README.md)       | 为什么推理要分 Prefill 和 Decode 两阶段？   | nano-vllm 源码走读：Sequence 状态机 → Scheduler 两阶段调度 → BlockManager → PagedAttention             |
| [**6. KV Cache 优化**](06-kvcache-optimization/README.md) | 显存不够怎么办？                            | 手算 Qwen2.5-7B 的 KV Cache（`2×L×H_kv×D×T×B`），对比 FP16→INT4 的 4× 压缩，跑 Offloading+LMCache 实验 |
| [**7. 推理服务平台**](07-maas-infra/README.md)            | 1000 个用户、10 种模型、SLA 99.9%——怎么搭？ | 实现 AI 网关 (Token Bucket + Cache-Aware LB)，DeepSeek V3 32×H20 部署案例                              |
| [**8. 总结展望**](08-summary-outlook/README.md)           | 学完了，然后呢？                            | 7+1 模块知识串联 + Agent Infra 前沿 + 大作业：三方向选一，提交代码+报告                                |

---

## 一个请求的完整旅程

```text
用户浏览器
  → [模块 7] AI 网关: 认证 → 限流 → Semantic Router 选模型 → Cache-Aware LB 选 Worker
  → [模块 4] K8s: API Server → Scheduler Filter/Score/Bind → kubelet → Device Plugin Allocate
  → [模块 5] vLLM: PagedAttention Block Table 映射 → Continuous Batching
  → [模块 6] KV Cache: FP8 量化 → Prefix Caching 命中 → 跳过 Prefill
  → [模块 3] GPU 虚拟化: HAMi LD_PRELOAD 拦截 CUDA API → 显存配额准入
  → [模块 2] CUDA: Kernel 在 SM Tensor Core 上执行 → HBM 带宽 3.35 TB/s
  → [模块 1] Linux 容器: Namespace 隔离 → NVIDIA CTK mknod + mount 注入 GPU 设备
  → GPU 硬件
```

---

## 动手，从第一行代码开始

不是 `pip install` 然后 `import`。每个模块从底层原理出发，亲手写关键代码：

- **模块 1**: `bash 01_namespace_demo.sh` — 亲手创建 PID/UTS/Mount Namespace，感受容器隔离的本质
- **模块 2**: `nvcc 03_matmul_tiled.cu -o matmul_tiled && ./matmul_tiled` — Shared Memory Tiling 优化矩阵乘法，对比 naive vs tiled
- **模块 2b**: `python3 01_dma_bandwidth.py` — 实测 Pinned (55 GB/s) vs Pageable (22 GB/s) DMA 带宽，2.5× 差距来自哪里
- **模块 3**: `gcc -shared -fPIC 01_mymalloc.c -o libmymalloc.so -ldl && LD_PRELOAD=./libmymalloc.so ls` — 60 行 C 代码理解 HAMi Hook 原理
- **模块 4**: `kubectl apply -f 02_gpu_pod.yaml && kubectl logs` — 声明 `nvidia.com/gpu: 1`，K8s 自动调度到 GPU 节点
- **模块 5**: `python3 trace_nanovllm.py` — Monkey-patch 追踪 Sequence 状态转换、Block 分配和 Prefill/Decode 两阶段调度
- **模块 6**: `python3 calculate_qwen3_memory.py --preset qwen2.5-72b` — 零依赖手算 KV Cache 显存
- **模块 7**: `python3 ai_gateway.py` — 140 行 Flask 网关，Token Bucket 限流 + 加权路由 + 故障转移
- **模块 8**: 大作业三方向选一 (容器化 Hook / K8s 调度 / KV Cache 模拟器)，搜索 `TODO` 即开始

---

## 环境要求

| 模块 | 需要 GPU？ | 说明                                                            |
| ---- | ---------- | --------------------------------------------------------------- |
| 1    | 否         | 任何 Linux/macOS，`bash` + `strace`                             |
| 2    | **是**     | NVIDIA GPU + CUDA Toolkit 12.8，`nvcc` 编译 `.cu` 文件          |
| 2b   | **是**     | DMA 带宽测试需要 GPU + CUDA Driver                              |
| 3    | 否         | LD_PRELOAD 拦截 `malloc`，纯 Linux 用户态，不需要 GPU           |
| 4    | 推荐       | minikube/kind/k3s 即可，无 GPU 也能学 K8s 核心对象 + 调度流程   |
| 5    | **是**     | NVIDIA GPU ≥ 8 GB 显存，PyTorch 2.6.0+cu124，flash-attn 2.7.4   |
| 6    | 推荐       | 显存计算脚本纯 CPU 零依赖；vLLM Offloading 实验需要 GPU         |
| 7    | 否         | Flask 网关 + Mock 后端 (`pip install flask requests`)；GPU 可选 |
| 8    | 否         | 方向 C (KV Cache 模拟器) 零硬件依赖；方向 A/B 需 GPU/K8s        |

> **可视化 HTML** 在所有模块中通用——浏览器直接打开，无需任何服务器或 GPU。

---

## 目录结构

```text
ai-infra-course/
├── README.md
├── CLAUDE.md                       # 本项目开发指南
├── course-overview.html            # 交互式课程全景图
├── 01-linux-containers/            # 模块 1
├── 02-gpu-cuda/                    # 模块 2
├── 02b-gpu-memory/                 # 模块 2b (附录)
├── 03-gpu-virtualization/          # 模块 3
├── 04-kubernetes-gpu/              # 模块 4
├── 05-vllm-inference/              # 模块 5
├── 06-kvcache-optimization/        # 模块 6
├── 07-maas-infra/                  # 模块 7
└── 08-summary-outlook/             # 模块 8
```

每个模块内含: `README.md` / `syllabus.md` / `ppt-outline.md` / `hands-on-exercise.md` / `homework.md` / `code/` / `visuals/`。模块 5、7、8 结构略有不同，详见各自 README。

---

课程材料基于 [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals)、[cloud-native-dev](https://github.com/ForceInjection/cloud-native-dev) 和 [nano-vllm](https://github.com/ForceInjection/nano-vllm)。
