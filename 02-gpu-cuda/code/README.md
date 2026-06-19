# 模块 2 配套代码 — GPU 硬件架构与 CUDA 编程入门

本目录包含 4 个 CUDA 程序，对应 PPT 中的课堂动手实验。

## 环境要求

- NVIDIA GPU (Compute Capability ≥ 7.0)
- CUDA Toolkit ≥ 12.0 (nvcc)
- Docker (可选，使用 `cuda-docker` 脚本)

## 文件说明

| 文件                 | 对应 PPT             | 内容                                                        | 实验时长 |
| -------------------- | -------------------- | ----------------------------------------------------------- | -------- |
| `01_vec_add.cu`      | 第 30-31 页 [动手 1] | 向量加法: CPU 串行 vs GPU 并行，对比 TH2D/Kernel/D2H 时间   | ~8 min   |
| `02_matmul_naive.cu` | 第 33-34 页 [动手 2] | 矩阵乘法 naive 版本: Global Memory 访问瓶颈分析             | ~7 min   |
| `03_matmul_tiled.cu` | 第 36 页 [动手 2]    | 矩阵乘法 tiled 版本: Shared Memory 优化，Bank Conflict 分析 | ~10 min  |
| `04_device_query.cu` | —                    | GPU 设备查询: 硬件参数、理论 TFLOPS/带宽                    | ~2 min   |
| `Makefile`           | —                    | 一键编译所有程序                                            | —        |
| `cuda-docker`        | —                    | 通过 Docker 容器编译运行（无需本地 CUDA Toolkit）           | —        |

## 运行方法

### 方法 1: 本地 CUDA Toolkit

```bash
# 编译
make all

# 运行全部
make run

# 运行单个程序
./device_query
./vec_add
./matmul_naive
./matmul_tiled

# 性能分析 (需要 Nsight Compute)
make profile

# 清理
make clean
```

### 方法 2: Docker (无需本地 nvcc)

可用镜像示例: `lmcache/vllm-openai:v0.4.7-cu129` (包含 CUDA 12.9 + nvcc)

```bash
# 编译所有
bash cuda-docker make

# 运行所有
bash cuda-docker all

# 运行单个
bash cuda-docker run device_query
bash cuda-docker run vec_add
bash cuda-docker run matmul_tiled

# 进入容器调试
bash cuda-docker shell
```

> 使用其他 CUDA 镜像: 编辑 `cuda-docker` 脚本中的 `IMAGE` 变量即可。

---

## 实验 1: 向量加法 — 第一个 CUDA 程序

**运行**: `./vec_add` (本地) 或 `bash cuda-docker run vec_add` (Docker)

**预期输出** (以 A100 为例):

```text
=========================================
  实验 1: 向量加法 — CPU vs GPU
  N = 16777216 (16.8 M 元素)
=========================================

[CPU] 串行计算...
[CPU] 耗时: 44.407 ms

[GPU] 并行计算...
[GPU] H2D 传输:  8.547 ms     ← Host→Device 拷贝时间
[GPU] Kernel 执行: 0.175 ms    ← GPU 实际计算时间 (极快!)
[GPU] D2H 传输:  35.555 ms     ← Device→Host 拷贝时间
[GPU] 总耗时:    44.295 ms
[GPU] 加速比:    1.0× (vs CPU) ← 被 PCIe 传输拖慢

正确性验证: 0 / 16777216 errors
有效带宽: 1147.9 GB/s
```

**关键观察**:

- Kernel 本身只有 0.175ms（是 CPU 44ms 的 250 倍快）
- 但 H2D + D2H 花了 44ms → **GPU 总时间 ≈ CPU 时间**
- 结论: 简单计算时 PCIe 传输是瓶颈，N 越大 GPU 优势越明显
- 思考: 如果 N=1024，GPU 还快吗？（不，传输开销占比更大）

---

## 实验 2: 矩阵乘法 — Naive 版本

**运行**: `./matmul_naive` 或 `bash cuda-docker run matmul_naive`

**预期输出** (1024×1024×1024, A100):

```text
=========================================
  实验 2: 矩阵乘法 — Naive (Global Memory)
  M=1024, N=1024, K=1024
=========================================

[Naive] 耗时:           0.986 ms
[Naive] 性能:           2178.4 GFLOPS       ← 约 5.6% FP32 峰值利用率
[Naive] Arithmetic Intensity: 170.7 FLOPs/byte
[Naive] 每个元素从 Global Memory 被读取次数: ~1024 次

瓶颈分析:
  → 向量加法 AI = 0.083 → 带宽瓶颈
  → 矩阵乘法 naive AI = 170.7 → Compute-bound
  → 虽然 AI 高，但 Global Memory 访问次数多，有效带宽浪费
```

**关键观察**:

- 每个 A 元素被读取 N=1024 次 → 带宽浪费 1024×
- Arithmetic Intensity = FLOPs ÷ Bytes = 170.7 → 理论上是 compute-bound
- 但 Global Memory 的重复读取导致有效带宽远低于理论峰值

---

## 实验 3: 矩阵乘法 — Tiled 版本

**运行**: `./matmul_tiled` 或 `bash cuda-docker run matmul_tiled`

**预期输出** (1024×1024×1024, TILE_SIZE=16, A100):

```text
=========================================
  实验 3: 矩阵乘法 — Tiled (Shared Memory)
  M=1024, N=1024, K=1024, TILE_SIZE=16
=========================================

版本                 耗时(ms)          GFLOPS Global Memory 访问
----------------------------------------------------------------------
Naive (Global Mem)      0.997          2154.3     每元素 ~K 次
Tiled (Shared Mem)      0.595          3610.1     每元素 ~K/16 次

加速比: 1.7×
正确性验证: 0 / 1048576 errors

Bank Conflict 分析:
  TILE=16: Bs 的列访问 stride = 64 bytes → 16-way bank conflict
  解决方案: __shared__ float Bs[TILE_SIZE][TILE_SIZE+1]
```

**关键观察**:

- Tiled 版本比 Naive 快 1.7×（A100 上；在消费级 GPU 上差距更大）
- 加速原因: 每个元素从 Global Memory 只读 1 次（进 Shared Memory），之后从 Shared Memory 读 K/16 次
- Shared Memory ~20 cycles vs Global Memory ~600 cycles → 差 30 倍
- TILE_SIZE=32 时 bank conflict 严重，加 padding 可消除

---

## 实验 4: GPU 设备查询

**运行**: `./device_query` 或 `bash cuda-docker run device_query`

**预期输出** (A100 服务器):

```text
=========================================
  GPU 设备查询
  检测到 8 个 CUDA 设备
=========================================

=== GPU 0: NVIDIA A100-SXM4-80GB ===
  SM 数量:          108
  Warp Size:        32
  Max Threads/Block: 1024
  Max Threads/SM:   2048
  Global Memory:    79.2 GB
  Shared Memory/Block: 48 KB
  Memory Bus Width: 5120-bit
  理论带宽:         2039.0 GB/s
  GPU Clock:        1410 MHz
  理论 FP32 峰值:   39.0 TFLOPS
  理论带宽/峰值比:  19.12 (FLOPs/byte — Roofline Ridge Point)
```

**用途**: 根据你的 GPU 理论峰值，判断你的 kernel 性能利用率。

---

## 修改 TILE_SIZE 实验

```bash
# 测试不同 TILE_SIZE
sed -i 's/#define TILE_SIZE 16/#define TILE_SIZE 8/' 03_matmul_tiled.cu
make matmul_tiled && ./matmul_tiled

sed -i 's/#define TILE_SIZE 8/#define TILE_SIZE 32/' 03_matmul_tiled.cu
make matmul_tiled && ./matmul_tiled
```

预期: TILE=32 可能比 TILE=16 **慢**（因为 bank conflict）。添加 padding 后恢复。

---

## 清理

```bash
make clean        # 删除编译产物
docker system prune -f  # 清理 Docker 缓存 (如果用了 cuda-docker)
```
