# 模块 2：GPU 硬件架构与 CUDA 编程入门 — 课后练习

## 题目：CUDA 矩阵乘法优化与 GPU 性能分析

### 目标

在课堂实验的基础上，系统性地优化 CUDA 矩阵乘法，并使用 Nsight Compute 进行性能分析，掌握 GPU Kernel 瓶颈定位和优化的方法论。

### 截止时间

下次课前 (一周)

---

## 基础任务 (必做)

### 任务 1: TILE_SIZE 扫描与 Bank Conflict

1. 测试 TILE_SIZE = 8, 16, 32，记录 2048×2048×2048 矩阵乘法的执行时间和 GFLOPS
2. 对于 TILE=32，实现 padding 技巧 (`__shared__ float As[32][33]`) 消除 bank conflict，对比性能
3. 解释为什么 TILE=32 加了 padding 后可能变快（或变慢？）

**提示**: 用 `ncu --set full` 查看 "shared_memory_bank_conflicts" 指标。

### 任务 2: Nsight Compute 瓶颈分析

对 naive 和 tiled 两个版本分别运行:

```bash
ncu --set full -o matmul_report ./matmul_tiled
```

从报告中提取并解释:

| 指标                         | Naive | Tiled | 解释 (为什么变好/变差?) |
| ---------------------------- | ----- | ----- | ----------------------- |
| Memory Throughput (%)        |       |       |                         |
| Compute (SM) Throughput (%)  |       |       |                         |
| Occupancy (%)                |       |       |                         |
| Shared Memory Bank Conflicts |       |       |                         |

**核心问题**: Naive 版本是 memory-bound 还是 compute-bound？Tiled 版本呢？用数据证明你的判断。

### 任务 3: GPU 硬件参数查询

编写一个 CUDA 程序，使用 `cudaGetDeviceProperties` 查询你的 GPU 的硬件参数:

```c
cudaDeviceProp prop;
cudaGetDeviceProperties(&prop, 0);
printf("GPU: %s\n", prop.name);
printf("Compute Capability: %d.%d\n", prop.major, prop.minor);
printf("SMs: %d\n", prop.multiProcessorCount);
printf("Max Threads per Block: %d\n", prop.maxThreadsPerBlock);
printf("Max Threads per SM: %d\n", prop.maxThreadsPerMultiProcessor);
printf("Shared Memory per Block: %zu KB\n", prop.sharedMemPerBlock/1024);
printf("Global Memory: %.1f GB\n", prop.totalGlobalMem/1024.0/1024.0/1024.0);
printf("Memory Bandwidth: %.1f GB/s\n",
       2.0 * prop.memoryClockRate * (prop.memoryBusWidth/8) / 1.0e6);
printf("Warp Size: %d\n", prop.warpSize);
```

根据你的 GPU 参数，回答:

- 你的 GPU 的理论 FP32 峰值是多少 TFLOPS？(CUDA Cores × 频率 × 2 FMA)
- 你的 GPU 的理论显存带宽是多少 GB/s？
- 根据理论峰值和你的矩阵乘法实测 GFLOPS，你的 kernel 达到了理论峰值的百分之多少？

---

## 进阶任务 (选做)

### 任务 4: 实现 Roofline 分析

1. 绘制你的 GPU 的 Roofline 图:
   - 横轴: Arithmetic Intensity (FLOPs/byte)
   - 纵轴: 可达 GFLOPS (log scale)
   - Ridge Point = 理论峰值 TFLOPS / 理论带宽 TB/s

2. 在图上标出:
   - 向量加法的 AI 和实测 GFLOPS
   - Naive 矩阵乘法的 AI 和实测 GFLOPS
   - Tiled 矩阵乘法的 AI 和实测 GFLOPS
   - 你的 kernel 离理论上限还有多大距离？

### 任务 5: 探索更多优化技巧（选一）

1. **Vectorized Memory Access**: 使用 `float4` 类型，一次加载 4 个 float → 减少指令数
2. **Register Blocking**: 每个线程计算一个 M×N 的小输出 tile (如 4×4)，累加在寄存器中
3. **Double Buffering**: 两组 shared memory，加载下一个 tile 的同时计算当前 tile

---

## 提交要求

1. 提交代码: 包含所有 TILE_SIZE 版本 + bank conflict 优化版本
2. 提交性能分析报告 (≤ 4 页)，包含:
   - TILE_SIZE 扫描的性能对比图和表
   - Bank conflict 优化前后的对比
   - Nsight Compute 关键指标截图和分析
   - GPU 硬件参数查询结果
   - 结论: 你的 kernel 是 memory-bound 还是 compute-bound？
3. (选做) Roofline 分析图或进阶优化代码

---

## 评分标准

| 维度            | 权重 | 要求                                      |
| --------------- | ---- | ----------------------------------------- |
| 任务 1-3 完成度 | 60%  | 完成 TILE 扫描、Nsight 分析、GPU 参数查询 |
| 分析深度        | 20%  | Nsight 指标解读准确、瓶颈判断有数据支撑   |
| 代码质量        | 10%  | 可编译、可复现、有注释                    |
| 进阶任务        | 10%  | 完成至少一项进阶任务                      |

---

## 参考资料

- AI-fundamentals: `01_hardware_architecture/nvidia/understand_gpu_architecture/` — GPU 架构深入
- AI-fundamentals: `01_hardware_architecture/performance/ai_latency_pyramid.md` — 延迟金字塔
- AI-fundamentals: `02_gpu_programming/02_cuda/` — CUDA 编程全套教程
- AI-fundamentals: `02_gpu_programming/04_profiling/01_nvbandwidth_best_practices.md` — GPU 带宽测量
- AI-fundamentals: `02_gpu_programming/04_profiling/06_nsight_compute_cli.md` — Nsight Compute CLI
- AI-fundamentals: `02_gpu_programming/04_profiling/07_nsight_systems_cli.md` — Nsight Systems CLI
- [CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/)
- [CUDA-Learn-Notes](https://github.com/xlite-dev/CUDA-Learn-Notes) — 200+ 优化 kernel 示例
