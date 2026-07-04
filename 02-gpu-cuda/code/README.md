# 模块 2 配套代码 — GPU 硬件架构与 CUDA 编程入门

本目录包含 4 个 CUDA 程序，对应 PPT 中的课堂动手实验。

## 环境要求

- NVIDIA GPU (Compute Capability ≥ 7.0)
- CUDA Toolkit ≥ 12.8 (nvcc)
- Docker (可选，使用 `cuda-docker` 脚本)

## 文件说明

| 文件                    | 对应 PPT             | 内容                                                     | 实验时长 |
| ----------------------- | -------------------- | -------------------------------------------------------- | -------- |
| `01_vec_add.cu`         | 第 30-31 页 [动手 1] | 向量加法: CPU 串行 vs GPU 并行，对比 H2D/Kernel/D2H 时间 | ~8 min   |
| `02_matmul_naive.cu`    | 第 33-34 页 [动手 2] | 矩阵乘法 naive: Global Memory 访问瓶颈分析               | ~7 min   |
| `03_matmul_tiled.cu`    | 第 36 页 [动手 2]    | 矩阵乘法 tiled: Shared Memory 优化，Bank Conflict 分析   | ~10 min  |
| `04_device_query.cu`    | —                    | GPU 设备查询: 硬件参数、理论 TFLOPS/带宽                 | ~2 min   |
| `Makefile`              | —                    | 一键编译 (自动检测 GPU 架构，也可 `make SM=90`)          | —        |
| `cuda-docker`           | —                    | Docker 编译运行 (无需本地 CUDA Toolkit)                  | —        |
| `h100_verification.txt` | —                    | 8×H100 完整运行输出 (参考)                               | —        |

## 运行方法

### 方法 1: 本地 CUDA Toolkit

```bash
# 编译 (自动检测 GPU 架构)
make all

# 手动指定架构 (如 H100: sm_90, RTX 4090: sm_89)
make SM=90 all

# 运行全部
make run

# 运行单个
./device_query
./vec_add
./matmul_naive
./matmul_tiled

# 清理
make clean
```

### 方法 2: Docker (无需本地 nvcc)

使用 `nvidia/cuda:12.8.0-devel-ubuntu22.04` 镜像。

```bash
bash cuda-docker all          # 编译并运行全部
bash cuda-docker make         # 仅编译
bash cuda-docker run vec_add  # 运行单个
bash cuda-docker shell        # 进入容器
```

---

## 实验 1: 向量加法 — 第一个 CUDA 程序

**运行**: `./vec_add`

**预期输出** (8×H100 实测):

```text
=========================================
  实验 1: 向量加法 - CPU vs GPU
  N = 16777216 (16.8M), 数据量 = 201 MB
=========================================

[CPU] 串行计算 (for 循环) ...
[CPU] 耗时: 34.51 ms

[GPU] 并行计算 ...
[GPU] 配置: 65536 blocks x 256 threads = 16777216 线程

  H2D (CPU->GPU):      13.563 ms  ( 27.3%)
  Kernel (GPU):         0.154 ms  (  0.3%)
  D2H (GPU->CPU):      35.871 ms  ( 72.3%)
  --------------------------------
  总计:                49.601 ms

  Kernel 有效带宽: 1303.7 GB/s
  加速比 (GPU/CPU): 0.7x

  正确性验证: 通过 (0 / 16777216 errors)
```

**关键观察**:

- Kernel 本身 0.15ms，但 H2D+D2H 花了 49.4ms
- GPU 总时间比 CPU 还慢 (0.7×) — 数据传输主导
- 线程索引公式: `tid = blockIdx.x * blockDim.x + threadIdx.x`
- 对应 PPT 第 22 页: PCIe Gen5 x16 = 128 GB/s vs HBM3 = 3.35 TB/s

---

## 实验 2: 矩阵乘法 — Naive 版本

**运行**: `./matmul_naive`

**预期输出** (1024×1024×1024, H100):

```text
=========================================
  实验 2: 矩阵乘法 — Naive (Global Memory)
  M=1024, N=1024, K=1024
=========================================

[Naive] 耗时:           0.497 ms
[Naive] 性能:           4319.6 GFLOPS
[Naive] Arithmetic Intensity: 170.7 FLOPs/byte
[Naive] 每个元素从 Global Memory 被读取次数: ~1024 次

瓶颈分析:
  向量加法的 AI: 0.083 FLOPs/byte → 带宽瓶颈
  矩阵乘法 naive 的 AI: 170.7 FLOPs/byte
  → 如果 AI < GPU 峰值 FLOPs/Bandwidth，则是带宽瓶颈
```

**关键观察**:

- 每个 A 元素被 1024 个线程各读一次 → 带宽浪费
- AI = FLOPs / Bytes，比较 AI 与 GPU 峰值 FLOPs/Bandwidth 判断瓶颈
- H100 Roofline Ridge Point: 19.96 FLOPs/byte (来自 device_query)

---

## 实验 3: 矩阵乘法 — Tiled 版本

**运行**: `./matmul_tiled`

**预期输出** (1024×1024×1024, TILE_SIZE=16, H100):

```text
===========================================================
  实验 3: 矩阵乘法 - Naive vs Tiled (Shared Memory)
  M=1024, N=1024, K=1024, TILE_SIZE=16
===========================================================

[1] Naive 版本 (仅 Global Memory)
  耗时: 0.549 ms, 性能: 3913.3 GFLOPS

[2] Tiled 版本 (Shared Memory, TILE=16)
  耗时: 0.302 ms, 性能: 7122.6 GFLOPS

--- 性能对比 ---
  Naive (Global Mem):     0.549 ms,   3913.3 GFLOPS
  Tiled (Shared Mem):     0.302 ms,   7122.6 GFLOPS
  加速比: 1.8x

  正确性验证: 通过

--- Bank Conflict ---
  TILE=16: Bs 列访问 stride=64 bytes -> 16-way conflict
  解决方案: __shared__ float Bs[TILE_SIZE][TILE_SIZE+1] (+1 列 padding)
```

**关键观察**:

- Tiled 版每个元素从 Global Memory 仅读取 1 次 (协作加载到 Shared Memory)
- Shared Memory ~20 cycles vs HBM ~600 cycles (PPT 第 12 页延迟金字塔)
- 两个 `__syncthreads()` 的作用: 第一次等加载完成，第二次等计算完成
- TILE_SIZE=32 时 bank conflict 更严重，加 padding 可消除

---

## 实验 4: GPU 设备查询

**运行**: `./device_query`

**预期输出** (8×H100, 仅 GPU 0):

```text
=== GPU 0: NVIDIA H100 80GB HBM3 ===
  计算能力:         9.0
  SM 数量:          132
  CUDA Cores (估算): 16896
  Max Threads/Block: 1024
  Global Memory:    79.2 GB
  Shared Memory/Block: 48 KB
  L2 Cache:         50.0 MB
  理论带宽:         3352.3 GB/s
  GPU Clock:        1980 MHz
  理论 FP32 峰值:   66.9 TFLOPS
  理论带宽/峰值比:  19.96 (FLOPs/byte — Roofline Ridge Point)
```

完整输出见 `h100_verification.txt`。

---

## 修改 TILE_SIZE 实验

修改 `03_matmul_tiled.cu` 第 16 行的 `#define TILE_SIZE 16`，重新编译运行，对比性能:

```bash
# TILE=8
sed -i '' 's/#define TILE_SIZE 16/#define TILE_SIZE 8/' 03_matmul_tiled.cu
make matmul_tiled && ./matmul_tiled

# TILE=32
sed -i '' 's/#define TILE_SIZE 8/#define TILE_SIZE 32/' 03_matmul_tiled.cu
make matmul_tiled && ./matmul_tiled

# 恢复
sed -i '' 's/#define TILE_SIZE 32/#define TILE_SIZE 16/' 03_matmul_tiled.cu
```

预期: TILE=8 的 Shared Memory 使用太少，TILE=32 的 bank conflict 加剧 (32-way)，TILE=16 是平衡点。

---

## 清理

```bash
make clean
```
