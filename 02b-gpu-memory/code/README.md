# 模块2 高级：GPU 内存管理 — 配套代码

两个版本的带宽测试程序，功能相同，测量 pageable vs pinned 内存的 DMA 传输带宽：

| 文件                  | 语言            | 运行方式                                                           |
| --------------------- | --------------- | ------------------------------------------------------------------ |
| `01_dma_bandwidth.py` | Python (ctypes) | `python3 01_dma_bandwidth.py`，零依赖 (仅需 libcudart.so)          |
| `02_dma_bandwidth.cu` | CUDA C          | `nvcc -O2 02_dma_bandwidth.cu -o dma_bandwidth && ./dma_bandwidth` |

## 环境要求

- NVIDIA GPU (Compute Capability ≥ 7.0)
- CUDA Toolkit ≥ 12.8（需要 `libcudart.so`）
- Python ≥ 3.8

## 运行方法

```bash
# 默认测试 0.5GB, 1GB, 2GB
python3 01_dma_bandwidth.py

# 自定义测试大小
python3 01_dma_bandwidth.py --sizes 0.1 0.5 1 2 4

# 调整迭代次数
python3 01_dma_bandwidth.py --iters 20 --warmup 5
```

## 预期输出

### PCIe Gen5 x16 环境 (H100 实测)

```text
==============================================================
CPU↔GPU DMA Bandwidth Test (ctypes + libcudart)
GPU:  NVIDIA H100 80GB HBM3
Link: PCIe Gen5 x16
==============================================================

 Size   Dir    Pageable      Pinned     Ratio    Pin-page
------------------------------------------------------------------
 0.5GB  H2D     16.95 GB/s  54.72 GB/s    3.2x  +37.78 GB/s
 0.5GB  D2H     14.60 GB/s  46.75 GB/s    3.2x  +32.15 GB/s
 1.0GB  H2D     21.34 GB/s  54.78 GB/s    2.6x  +33.44 GB/s
 1.0GB  D2H     16.74 GB/s  46.97 GB/s    2.8x  +30.23 GB/s
 2.0GB  H2D     21.37 GB/s  54.83 GB/s    2.6x  +33.46 GB/s
 2.0GB  D2H     16.75 GB/s  47.26 GB/s    2.8x  +30.51 GB/s
 4.0GB  H2D     21.37 GB/s  54.87 GB/s    2.6x  +33.50 GB/s
 4.0GB  D2H     16.72 GB/s  48.01 GB/s    2.9x  +31.29 GB/s

--- Summary (H2D) ---
Pageable:  20.3 GB/s
Pinned:    54.8 GB/s
Ratio:     2.7x

Theoretical (PCIe Gen5 x16): ~64 GB/s
Pinned efficiency:   86%
Pageable efficiency: 32%

--- Summary (D2H) ---
Pageable:  16.2 GB/s            ← D2H pageable 比 H2D 更慢
Pinned:    47.2 GB/s
Ratio:     2.9x
```

## 关键观察

1. **Pageable H2D 不随 PCIe 升级** — 瓶颈在 CPU 页表遍历 (~21 GB/s)
2. **Pinned H2D 接近 PCIe 理论值** — DMA 引擎直传 (~55 GB/s, 86% 效率)
3. **D2H pageable 比 H2D 更慢** — ~16 vs ~21 GB/s，CPU 端接收开销更大
4. **Gen5 下 H2D pinned/pageable ≈ 2.7×** — PCIe 越快，pinned 优势越大

## 原理

```text
Pageable (malloc):
  用户空间 buffer → 内核遍历页表 → lock 页面 → scatter-gather list → DMA
  每次 cudaMemcpy 都要重复以上步骤

Pinned (cudaMallocHost):
  分配时一次锁定 → DMA 引擎直传 → 无 CPU 开销
  代价: 占用系统 RAM，不能太多
```
