# 模块2 高级：GPU 内存管理 — 课堂动手题

## 题目：CPU↔GPU 带宽测试

### 题目描述

使用 `01_dma_bandwidth.py` 测量 pageable (`malloc`) vs pinned (`cudaMallocHost`) 内存的 CPU↔GPU 传输带宽，验证 pinned memory 的加速效果。

### 预计时间

5 分钟

---

## Step 1: 运行带宽测试

```bash
cd code/
python3 01_dma_bandwidth.py
```

## Step 2: 观察输出

```text
实测环境: 8×H100 80GB HBM3, PCIe Gen5 x16

Size (GB) | H2D pageable | H2D pinned |  Ratio  | D2H pageable | D2H pinned |  Ratio
----------|--------------|------------|---------|-------------|------------|--------
    0.5   |   21.8 GB/s  |  55.1 GB/s |  2.5×   |   13.6 GB/s  |  53.6 GB/s |  3.9×
    1.0   |   21.8 GB/s  |  55.1 GB/s |  2.5×   |   13.9 GB/s  |  53.6 GB/s |  3.9×
    2.0   |   21.8 GB/s  |  55.1 GB/s |  2.5×   |   13.4 GB/s  |  52.5 GB/s |  3.9×
    4.0   |   21.8 GB/s  |  55.1 GB/s |  2.5×   |   13.7 GB/s  |  52.1 GB/s |  3.8×
```

> Pageable H2D ~22 GB/s（CPU 瓶颈，不随 PCIe 升级），Pinned ~55 GB/s（DMA 直传）。D2H pageable 比 H2D 更慢 — CPU 端接收数据时页表遍历开销更大。

## Step 3: 分析结果

- Pageable 带宽是否随数据量增大而略微下降？为什么？
- Pinned 带宽是否接近 PCIe 理论带宽的 80%？
- H2D 和 D2H 的带宽是否对称？

---

## 讲解要点

### 1. 为什么 pinned 比 pageable 快？

- Pageable (`malloc`): 每次 `cudaMemcpy` 内核都要遍历页表 + 锁定页面 + 构建 scatter-gather list
- Pinned (`cudaMallocHost`): 页面预先锁定，DMA 引擎直接读取物理地址，无 CPU 开销

### 2. 为什么 pageable 带宽不随 PCIe 升级？

- 瓶颈在 CPU（页表遍历 + 页锁定），不在 PCIe
- PCIe 越快，CPU 开销占比越大 → pinned 优势越大

### 3. Pinned memory 的代价

- 占用系统 RAM，分配太多会拖慢整个系统
- 生产环境建议 pinned 内存不超过总 RAM 的 10-20%
