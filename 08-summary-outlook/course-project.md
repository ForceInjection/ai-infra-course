# 模块 8：课程大作业 — 云原生 AI 推理系统设计与实现

## 一、概述

从以下三个方向中**任选一个**完成大作业。每个方向都聚焦 **AI 基础设施** (而非 AI 应用)，覆盖课程的多个核心模块。

> **实验环境**: 课程结束后一周内提供包含 GPU 服务器和 K8s 集群的实验环境，用于方向 A (LD_PRELOAD CUDA hook) 和方向 B (K8s 调度 + vLLM 推理)。方向 C 零硬件依赖，纯 Python 标准库即可完成。
>
> **骨架代码**: 每个方向在 `code/` 目录下提供了可运行的骨架框架，关键位置标注 `# TODO:`。搜索 `TODO` 即可找到需要完成的代码位置。详见 `code/README.md`。

### 1.1 截止时间

2026年7月31日

### 1.2 提交要求

1. **代码**: GitHub 仓库 (或 zip 包)，含 README (如何运行、环境要求、预期结果)
2. **技术报告**: Markdown/PDF, 3000-5000 字，包含架构图、关键设计决策、实验数据和分析。使用 `code/REPORT_TEMPLATE.md` 模板
3. 打包提交，命名为 `学号_姓名_大作业.zip`
4. 提交地址：<wang.tianqing.cn@outlook.com>

### 1.3 评分标准

| 维度       | 权重 | 要求                                        |
| ---------- | ---- | ------------------------------------------- |
| 技术深度   | 35%  | 正确应用课程知识，设计有依据，代码实现完整  |
| 实验与分析 | 25%  | 有实验数据 (性能/对比/分析)，结论有理有据   |
| 工程完整性 | 20%  | 代码可运行、有 README、有错误处理、结构清晰 |
| 报告质量   | 20%  | 架构图清晰、逻辑连贯、有自己的思考          |

---

## 二、方向 A: GPU 资源拦截 — 从显存到算力

**难度**: ★★★☆ (中等) &nbsp;|&nbsp; **覆盖模块**: 3 &nbsp;|&nbsp; **估计代码量**: ~250 行 (C ~200 + Python ~50)

> **难度说明**: 核心挑战是 LD_PRELOAD 拦截两个 CUDA API。但 `cudaMalloc` 的拦截模式与模块 3 `01_mymalloc.c` 完全相同 (`dlsym` + `__thread` + 配额)，`cudaLaunchKernel` 的令牌桶逻辑与模块 3 `03_token_bucket.py` 完全对应——两样课上都已经手写过，大作业只是把它们搬到 CUDA Runtime API 上。骨架代码已提供完整的函数框架（递归守卫 + 变量声明），学生只需填充配额检查和转发逻辑。

### 2.1 目标

使用 LD_PRELOAD 拦截 CUDA Runtime API，实现对单个进程的**显存配额**和**算力限速**——这正是 HAMi `libvgpu.so` 的核心原理。提供一个统一的 CUDA 测试程序 (`test_hook.cu`) 验证拦截效果，无需运行推理框架。

### 2.2 要求

#### 2.2.1 显存拦截: `cudaMalloc` (模块 3 — malloc hook 模式)

- 编写 `libcuda_hook.so`，使用 LD_PRELOAD 拦截 `cudaMalloc`:
  - 通过环境变量 `CUDA_MEM_QUOTA_MB` 设置显存配额
  - 超配额时返回 `cudaErrorMemoryAllocation` (值为 2)，不调用真正的 `cudaMalloc`
  - 记录每次分配: 请求大小、返回指针、当前已分配总量
- 使用 `dlsym(RTLD_NEXT, ...)` 获取原始函数指针并转发调用
- `__thread` 递归守卫: `fprintf(stderr, ...)` 内部可能触发 `cudaMalloc`，必须防止死循环（与模块 3 `01_mymalloc.c` 完全相同的模式）
- 编译: `gcc -shared -fPIC -o libcuda_hook.so cuda_hook.c -ldl`（无需链接 CUDA 库，符号由目标进程提供）

#### 2.2.2 算力拦截: `cudaLaunchKernel` (模块 3 — 令牌桶模式)

- 在同一个 `libcuda_hook.so` 中拦截 `cudaLaunchKernel`:
  - 用环境变量 `CUDA_CORE_RATE` (每秒可启动的 kernel 数) 和 `CUDA_CORE_CAPACITY` (最大突发数) 配置令牌桶
  - 每次 kernel 启动消耗 1 个令牌，无令牌时返回 `cudaErrorLaunchFailure` (值为 4) 或阻塞等待
  - 记录每次 kernel 启动: Grid 维度 (`gridDim.x/y/z`)、Block 维度 (`blockDim.x/y/z`)
- 令牌桶逻辑直接翻译模块 3 `03_token_bucket.py` 的 `TokenBucket.acquire()`: `_refill()` → 检查 tokens → 扣减或拒绝
- `_refill()` 用 `clock_gettime(CLOCK_MONOTONIC, ...)` 获取高精度时间（骨架代码已提供 `launch_refill()` 函数）
- `cudaLaunchKernel` 的所有参数（`func`, `gridDim`, `blockDim`, `args`, `sharedMem`, `stream`）需原样转发给 `real_cudaLaunchKernel`

#### 2.2.3 测试程序验证

- 使用骨架提供的 `test_hook.cu`（无需修改）验证拦截效果:

  ```bash
  # 编译 hook 和测试程序
  make && make test-gpu

  # 或手动 (注意 --cudart=shared 是必需的):
  nvcc --cudart=shared test_hook.cu -o test_hook
  LD_PRELOAD=./libcuda_hook.so \
    CUDA_MEM_QUOTA_MB=128 \
    CUDA_CORE_RATE=5 \
    CUDA_CORE_CAPACITY=3 \
    ./test_hook
  ```

- 测试程序包含 3 个独立测试:
  - **Test 1**: `cudaMalloc` 配额 — 正常分配成功 + 超配额返回 `cudaErrorMemoryAllocation` (2)
  - **Test 2**: `cudaLaunchKernel` 限速 — 连续启动 10 个 kernel，前几个通过 (burst)，后续被拒绝；等待 1.5s refill 后恢复
  - **Test 3**: Grid/Block 维度记录 — 启动不同维度的 kernel，验证 hook 日志输出正确
- 同时对比: 不加 LD_PRELOAD 跑一次 vs 加 hook 跑一次，观察 stderr 输出的差异

#### 2.2.4 实验与分析

- 解析 `test_hook` 运行产生的 hook 日志，绘制:
  - `cudaMalloc` 分配时间线（x=调用序号，y=分配大小）
  - `cudaLaunchKernel` 通过/拒绝时间线（对比 burst 耗尽 → refill 恢复的令牌数变化）
- 用简单的 Python 脚本解析 stderr 日志（骨架不提供，培养学生自己写分析工具的能力）:
  - 统计总共拦截了多少次 `cudaMalloc` / `cudaLaunchKernel`
  - 计算拦截开销: hook 中 `fprintf` + `clock_gettime` 的额外延迟（可通过对比有无 hook 时的 wall-clock 时间估算）
- 总结: LD_PRELOAD 能否实现有效的 GPU 资源隔离？显存配额 + 算力限速的组合与 HAMi 的方案有何异同？相比 MIG/Time-Slicing 的优劣势？

### 2.3 交付物

- `cuda_hook.c` + `Makefile`: LD_PRELOAD hook 源码 + 编译脚本（基于骨架 `gpu-hook/`）
- `experiments/`: 实验数据目录，含 hook 日志 (文本)、CUDA API 调用统计 (CSV)、显存 + kernel 时间线图表 (PNG)
- `REPORT.md`: 技术报告

---

## 三、方向 B: K8s GPU 调度与推理网关部署

**难度**: ★★★☆ (中等) &nbsp;|&nbsp; **覆盖模块**: 1, 4, 7 &nbsp;|&nbsp; **估计代码量**: ~350 行 &nbsp;|&nbsp; **可 2 人协作** (YAML ~120 + 网关 ~180 + 压测脚本 ~50)

> **难度说明**: K8s YAML 部分较简单 (模块 4 已实践)；网关可直接复用模块 7 `code/ai_gateway.py` 并增强；GPU 调度追踪本质是 `kubectl describe/events` + 画时序图。使用 Qwen2.5-0.5B (~1GB) 等小模型部署 vLLM 实例，同时满足 GPU 调度追踪和网关真实后端的需求，将两条主线串起来。

### 3.1 目标

围绕 K8s GPU 调度全链路和推理网关部署两条主线：深入追踪 GPU Pod 从 YAML 到运行的完整过程，同时将 AI 网关部署到 K8s 并验证弹性伸缩与故障恢复。

> **协作说明**: 本方向最多可由两人协作完成 — 一人负责网关实现 (Flask + LB 策略 + 健康检查)，一人负责 K8s 部署 (YAML + HPA + GPU 调度追踪)。合并后联调压测。提交时需注明分工。

### 3.2 要求

#### 3.2.1 GPU 调度全链路追踪 (模块 4)

- 编写 GPU Pod YAML (声明 `nvidia.com/gpu: 1`)
- 追踪 Pod 从创建到 Running 的完整流程:
  - `kubectl apply` → API Server 接收 → 写入 etcd
  - Scheduler: Filter (哪些节点有 GPU？) → Score (拓扑打分) → Bind
  - 目标节点 kubelet: watch 到 Pod → 调用 Device Plugin `Allocate()` → 返回 GPU UUID
  - NVIDIA CTK: OCI prestart hook → `mknod /dev/nvidia*` → `mount --bind` 驱动库
  - 容器启动 → `nvidia-smi` 可见
- 用 `kubectl describe pod` 和 `kubectl get events` 记录每一步的时序和状态变化
- 画出完整的时序图 (参考模块 4 `visuals/k8s-gpu-flow.html`)

#### 3.2.2 AI 网关的 K8s 部署 (模块 7)

- 编写 K8s YAML，部署一个推理服务的完整拓扑:
  - AI 网关 (Flask/Go): Deployment + Service (ClusterIP)
  - vLLM 后端: Deployment + Service (使用小模型如 Qwen2.5-0.5B, ~1GB 显存)
  - ConfigMap: 网关配置 (LB 策略、限流参数、后端列表)
- 网关需实现: Token Bucket 限流 (已提供) + 实现至少 2 种 LB 策略 (加权轮询 / 一致性哈希 / 最少连接 三选二) + 健康检查 + OpenAI 兼容 API
- K8s YAML 必须通过 `kubectl --dry-run=client` 或 `kubeconform` 验证无语法错误

#### 3.2.3 弹性伸缩与故障恢复 (模块 4)

- 配置 HPA (Horizontal Pod Autoscaler): 基于 CPU/内存或自定义指标
- 验证: 压测网关 → 观察 HPA 触发 → Pod 自动扩容
- 验证故障恢复: 手动删除一个后端 Pod → 观察 K8s 自动重建 → 网关健康检查自动恢复路由
- 配置 PodAntiAffinity: 确保多个副本分布在不同的 K8s 节点 (如果多节点可用) 或至少配置 `requiredDuringScheduling`

#### 3.2.4 实验与分析

- 记录 GPU Pod 从 Pending → ContainerCreating → Running 各阶段的耗时
- 对比: 有无 Device Plugin 时 GPU Pod 的调度行为 (Scheduler Events 的差异)
- 压测网关: 不同并发下的 P50/P99 延迟 + HPA 响应时间
- 分析: 网关本身成为瓶颈的临界并发数在哪里？

### 3.3 交付物

- `app.py`: 网关源码 (基于骨架 `k8s-gateway/app.py`)
- `k8s/`: 部署 YAML 目录，含后端/网关/ConfigMap/HPA 共 4 个文件 + `kubectl --dry-run` 验证输出
- `benchmark/`: 压测脚本 (推荐 locust 或 wrk) + 实验结果 (CSV + 图表) + GPU 调度时序图 (PNG)
- `REPORT.md`: 技术报告

---

## 四、方向 C: KV Cache 显存管理 — 从公式到系统

**难度**: ★★★★ (较难) &nbsp;|&nbsp; **覆盖模块**: 2, 5, 6 &nbsp;|&nbsp; **估计代码量**: ~500 行 Python (计算工具 ~150 + 碎片模拟器 ~200 + Cache 模拟器 ~100 + 可视化 ~50)

> **难度说明**: 三个独立模块，每个都有清晰边界。显存计算工具是模块 6 `calculate_qwen3_memory.py` 的独立重实现，有现成参考；PagedAttention 碎片模拟器是最具挑战的部分 — 需要设计 Block 分配/回收算法和处理请求随机到达的离散事件模拟，但纯 Python 无外部依赖；Prefix Cache LRU 模拟器较简单。每个模块可独立完成和测试。**最大优势**: 零硬件依赖，纯 Python 标准库 + matplotlib，任何笔记本都能完成。

### 4.1 目标

深入理解 KV Cache 显存管理的核心问题: 碎片从何而来？PagedAttention 如何解决？量化能省多少？通过理论计算 + 模拟实验 + (有 GPU 时) 实际测量，形成完整的量化理解。

### 4.2 要求

#### 4.2.1 显存计算工具 (模块 6)

- 编写独立的 Python 脚本，支持:
  - 命令行参数: `--preset` (模型预设) 或 `--L` `--H_kv` `--head-dim` `--params` (手动指定)；`--dtype` `--seq-len` `--batch` 控制计算场景
  - 内置预设: Qwen2.5-0.5B/7B/72B, Llama-3-8B/70B, DeepSeek-V3 (MLA)
  - 计算: 模型权重 + KV Cache 峰值 + 总显存
  - 支持 FP16/FP8/INT8/INT4, 自动比较不同精度的并发容量
  - 支持 GQA 参数，展示 MHA vs GQA vs MLA 的 KV Cache 差异
  - 输出格式化表格 + matplotlib 可视化 (参考模块 6 `code/calculate_qwen3_memory.py`，需独立实现)
- 对于 DeepSeek-V3 (MLA)，需要说明为什么它的 KV Cache 远小于同参数量级的 Dense 模型

#### 4.2.2 PagedAttention 碎片模拟器 (模块 5)

- 模拟 100 个并发请求的生命周期:
  - 每个请求随机 prompt 长度 (100-2000 tokens) + 随机 output 长度 (50-500 tokens)
  - 请求按随机间隔到达、生成完成后释放
- 实现两种 KV Cache 管理方案并对比:
  - **Naive (预分配)**: 请求到达时分配 `max_tokens` 的连续空间
  - **PagedAttention**: Block 大小 16 tokens，Block Table 管理，按需分配，ref_count 复用
- 统计指标: 总显存消耗峰值 / 内部碎片 (未使用的预留) / 外部碎片 (无法分配的空隙) / 显存利用率 / 因显存不足而被拒绝的请求数
- 可视化: 显存时间线 (对比 Naive vs PA 的显存占用随时间变化)

#### 4.2.3 Prefix Caching 命中率模拟 (模块 5 + 6)

- 模拟 200 个请求，分为 4 组，每组 50 个共享不同的 System Prompt (256/512/1024/2048 tokens)
- 实现 LRU Cache 模拟器: Block 容量可配置，冷 Block 淘汰
- 统计: 不同 Cache 容量下的命中率曲线 + 不同 System Prompt 长度下的命中率
- 计算 TTFT 加速比 (假设命中 = 跳过 Prefill, TTFT -90%)

#### 4.2.4 可选: GPU 实测验证

如果有 GPU (4090), 增加以下实验:

- 使用 vLLM 部署 Qwen2.5-0.5B / Qwen3-0.6B
- 用 `nvidia-smi` 和 `torch.cuda.memory_summary()` 测量实际显存，与计算工具对比
- 测试 Prefix Caching (`--enable-prefix-caching`) 的实际加速效果
- 对比 FP16 vs FP8 (`--kv-cache-dtype fp8`) 的并发容量

#### 4.2.5 实验与分析

- 对比至少 3 个模型的 KV Cache 需求 (含 DeepSeek-V3 MLA 的对比)
- 分析碎片率与请求分布 (prompt 长度方差、output 长度方差) 的关系
- 量化三种优化策略的叠加效果: 量化 ×4 + GQA ×8 + Prefix Cache ×2 = 理论 ×64
- 总结: 给定一个 GPU (如 H100 80GB)，最多能并发服务多少个 7B 模型请求？需要哪些优化才能达到？

### 4.3 交付物

- `calculator.py`: 显存计算工具 (基于骨架 `kvcache-simulator/calculator.py`)
- `simulator.py`: PagedAttention 碎片模拟器 (基于骨架 `kvcache-simulator/simulator.py`)
- `lru_cache.py`: Prefix Cache LRU 模拟器 (基于骨架 `kvcache-simulator/lru_cache.py`)
- `visualize.py`: matplotlib 图表生成 (基于骨架 `kvcache-simulator/visualize.py`)，输出 4 张图表 (模型对比 / 精度并发 / 碎片率 / 命中率)
- `gpu_experiments/` (可选): GPU 实测脚本 + 数据
- `REPORT.md`: 技术报告 (含全部图表和分析)

---

## 五、参考资料

- 模块 1: `01-linux-containers/code/` (Namespace/Cgroup/OverlayFS 演示脚本)
- 模块 3: `03-gpu-virtualization/code/01_mymalloc.c` (LD_PRELOAD malloc hook) + `03_token_bucket.py` (令牌桶限流)
- 模块 4: `04-kubernetes-gpu/visuals/k8s-gpu-flow.html` (GPU 调度全链路)
- 模块 5: `05-vllm-inference/code/trace_nanovllm.py` (nano-vllm 追踪脚本)
- 模块 6: `06-kvcache-optimization/code/calculate_qwen3_memory.py` (显存计算脚本)
- nano-vllm: <https://github.com/ForceInjection/nano-vllm>
