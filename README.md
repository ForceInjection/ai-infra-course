# 云原生 AI 基础设施：原理与实践

一个 Chat 请求从浏览器到 GPU 硬件，穿越 7 层技术栈。8 次课，逐层深入，从 Linux 容器到推理服务平台。

**[交互式课程全景图 →](course-overview.html)** — 点击任意模块，7 层请求链路与课程卡片联动高亮。

---

## 这门课讲什么

每一层做了什么？为什么这么设计？8 个模块，每个回答一个核心问题：

| 模块                 | 核心问题                                    | 你会做什么                                                                                 |
| -------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **1. Linux 容器**    | 怎么把应用和 GPU 驱动打包在一起？           | 手写 Namespace 隔离、看懂 OverlayFS 分层、追踪 `docker run --gpus all` 完整调用链          |
| **2. GPU & CUDA**    | GPU 为什么比 CPU 快 100 倍？                | 从 CUDA 线程层次写到 Shared Memory Tiling，naive vs tiled 矩阵乘法加速 1.8×                |
| **2b. GPU 内存**     | Pinned 和 Pageable 内存差多少？             | 实测 DMA 带宽：pinned 55 GB/s vs pageable 22 GB/s——2.5 倍的工程决策依据                    |
| **3. GPU 虚拟化**    | 一张 A100 怎么分给 10 个人用？              | LD_PRELOAD 拦截 `malloc`，手写显存配额管理器，类比理解 HAMi 的 CUDA API Hook 原理          |
| **4. K8s GPU 调度**  | 100 台 GPU 服务器怎么管？                   | 从 `kubectl apply` 到容器内 `nvidia-smi`——追踪 7 步全链路，配置 HPA 弹性伸缩               |
| **5. vLLM 推理引擎** | 为什么推理要分 Prefill 和 Decode 两阶段？   | nano-vllm 源码走读：Sequence 状态机 → Scheduler 两阶段调度 → BlockManager → PagedAttention |
| **6. KV Cache 优化** | 显存不够怎么办？                            | 手算 Llama-3-70B 的 KV Cache，对比 FP16→INT4 的 4× 压缩，跑 Offloading+LMCache 实验        |
| **7. 推理服务平台**  | 1000 个用户、10 种模型、SLA 99.9%——怎么搭？ | 实现 AI 网关 (Token Bucket + Cache-Aware LB)，DeepSeek V3 32×H20 部署案例                  |
| **8. 总结展望**      | 学完了，然后呢？                            | 7 模块知识串联 + Agent Infra 前沿 + 大作业：三方向选一，提交代码+报告                      |

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

- 模块 1: `strace docker run --gpus all` 追踪系统调用
- 模块 2: `nvcc matmul_tiled.cu`——Shared Memory Tiling 优化矩阵乘法，对比 naive vs tiled 的加速效果
- 模块 3: `LD_PRELOAD=./libmymalloc.so ls`——每次 ls 都看到拦截日志
- 模块 4: `kubectl apply -f gpu-pod.yaml && kubectl logs`——YAML 声明 `nvidia.com/gpu: 1`，自动调度
- 模块 5: `python trace_nanovllm.py`——追踪 Sequence 状态转换和 Block 分配
- 模块 6: `python calculate_qwen3_memory.py --preset qwen2.5-72b`——零依赖算显存
- 模块 7: `python ai_gateway.py`——140 行 Flask 网关，Token Bucket + 故障转移
- 模块 8: 大作业——三个方向选一，交代码+报告

---

## 环境要求

| 模块 | 需要 GPU？ | 说明                                  |
| ---- | ---------- | ------------------------------------- |
| 1    | 否         | 任何 Linux/macOS                      |
| 2    | 是         | CUDA kernel 必须在 GPU 上运行         |
| 2b   | 是         | DMA 带宽测试需要 GPU                  |
| 3    | 否         | LD_PRELOAD 拦截 malloc，不需要 GPU    |
| 4    | 推荐       | minikube/kind 即可，无 GPU 也能学 K8s |
| 5    | 是         | vLLM 推理需要 GPU，≥ 8 GB 显存        |
| 6    | 推荐       | 显存计算脚本纯 CPU；vLLM 实验需要 GPU |
| 7    | 否         | Flask 网关 + Mock 后端；GPU 实验可选  |
| 8    | 否         | 大作业方向 C 零硬件依赖               |

---

## 目录结构

```text
ai-infra-course/
├── README.md
├── 01-linux-containers/         # 模块 1
├── 02-gpu-cuda/                 # 模块 2
├── 02b-gpu-memory/              # 模块 2b
├── 03-gpu-virtualization/       # 模块 3
├── 04-kubernetes-gpu/           # 模块 4
├── 05-vllm-inference/           # 模块 5
├── 06-kvcache-optimization/     # 模块 6
├── 07-maas-infra/               # 模块 7
└── 08-summary-outlook/          # 模块 8
```

每个模块含: `README.md` / `syllabus.md` / `ppt-outline.md` / `code/` / `hands-on-exercise.md` / `homework.md` / `lab-environment.md`。

---

课程材料基于 [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals)、[cloud-native-dev](https://github.com/ForceInjection/cloud-native-dev) 和 [nano-vllm](https://github.com/ForceInjection/nano-vllm)。
