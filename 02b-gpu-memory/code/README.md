# 模块2 高级：GPU 内存管理 — 配套代码

`01_dma_bandwidth.py` 使用 ctypes 直接调用 CUDA Runtime API，测量 pageable vs pinned 内存的 DMA 传输带宽。零依赖（仅需 `libcudart.so`）。

## 环境要求

- NVIDIA GPU (Compute Capability ≥ 7.0)
- CUDA Toolkit ≥ 12.0（需要 `libcudart.so`）
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
 0.5GB  H2D     21.77 GB/s  55.06 GB/s    2.5x  +33.29 GB/s
 0.5GB  D2H     13.56 GB/s  53.56 GB/s    3.9x  +40.00 GB/s
 1.0GB  H2D     21.77 GB/s  55.10 GB/s    2.5x  +33.33 GB/s
 1.0GB  D2H     13.85 GB/s  53.59 GB/s    3.9x  +39.74 GB/s
 2.0GB  H2D     21.75 GB/s  55.11 GB/s    2.5x  +33.36 GB/s
 2.0GB  D2H     13.39 GB/s  52.52 GB/s    3.9x  +39.13 GB/s
 4.0GB  H2D     21.78 GB/s  55.11 GB/s    2.5x  +33.33 GB/s
 4.0GB  D2H     13.67 GB/s  52.13 GB/s    3.8x  +38.46 GB/s

--- Summary (H2D) ---
Pageable:  21.8 GB/s
Pinned:    55.1 GB/s
Ratio:     2.5x

Theoretical (PCIe Gen5 x16): ~64 GB/s
Pinned efficiency:   86%
Pageable efficiency: 34%

--- Summary (D2H) ---
Pageable:  13.6 GB/s            ← D2H pageable 比 H2D 更慢 (CPU 端接收开销)
Pinned:    52.9 GB/s
Ratio:     3.9x
```

## 关键观察

1. **Pageable H2D 不随 PCIe 升级** — 瓶颈在 CPU 页表遍历 (21.8 GB/s)
2. **Pinned H2D 接近 PCIe 理论值** — DMA 引擎直传 (55.1 GB/s, 86% 效率)
3. **D2H pageable 比 H2D 更慢** — 13.6 vs 21.8 GB/s，CPU 端接收开销更大
4. **Gen5 下 H2D pinned/pageable = 2.5×** — PCIe 越快，pinned 优势越大
5. **D2H pageable 开销最大** — ratio 达 3.9×，CPU 接收页表遍历比发送更慢

## 原理

```text
Pageable (malloc):
  用户空间 buffer → 内核遍历页表 → lock 页面 → scatter-gather list → DMA
  每次 cudaMemcpy 都要重复以上步骤

Pinned (cudaMallocHost):
  分配时一次锁定 → DMA 引擎直传 → 无 CPU 开销
  代价: 占用系统 RAM，不能太多
```
