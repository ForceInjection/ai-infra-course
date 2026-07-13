# 模块 2b：GPU 内存管理

> 15–20 分钟 &nbsp;|&nbsp; 12 页 PPT &nbsp;|&nbsp; 2 个可视化 HTML &nbsp;|&nbsp; 2 个带宽测试脚本

GPU 内存管理附录，从 CPU/GPU 对称性出发，介绍内存层级、DMA 传输、Pinned vs Pageable、碎片化和跨进程共享。

---

## 可视化 HTML

| 可视化                                                                   | 用途                                                    | 教学场景                                    |
| ------------------------------------------------------------------------ | ------------------------------------------------------- | ------------------------------------------- |
| [GPU 内存管理 — 可交互概念图](visuals/gpu-memory-visual.html)            | 6 层交互概念图 (物理拓扑→内存层级→DMA→MMU→碎片→共享)    | 讲解 GPU 内存管理时打开，逐层探索各概念     |
| [DMA 深度剖析 — Pinned vs Pageable 传输原理](visuals/dma-benchmark.html) | DMA 8 步动画: Pinned 直接 DMA vs Pageable Bounce Buffer | 讲解 DMA 带宽时打开，对比两种路径的完整时序 |

## 概念图层

| 图层       | 内容                             | 使用场景            |
| ---------- | -------------------------------- | ------------------- |
| 物理拓扑   | CPU + GPU + NVMe 物理连接        | 建立全局视图        |
| 内存层级   | Register~HBM 金字塔 + CPU 类比   | 理解延迟量级        |
| DMA 传输   | Pinned/Pageable/GDS 三条数据路径 | 理解传输性能差异    |
| MMU/页表   | CPU/GPU 独立 MMU，TLB，大页      | 理解地址翻译开销    |
| 碎片化     | 虚拟地址空间碎片化示例           | 解释 cudaMalloc OOM |
| 跨进程共享 | 磁盘 vs IPC vs UM 三种方案       | 理解 LMCache 设计   |

---

## 配套代码

| 文件                                              | 内容                          | 对应 PPT |
| ------------------------------------------------- | ----------------------------- | -------- |
| [`01_dma_bandwidth.py`](code/01_dma_bandwidth.py) | CPU↔GPU DMA 带宽测试 (Python) | —        |
| [`02_dma_bandwidth.cu`](code/02_dma_bandwidth.cu) | CPU↔GPU DMA 带宽测试 (CUDA C) | —        |

详见 [`code/README.md`](code/README.md)。

---

## 课堂练习

详见 [`hands-on-exercise.md`](hands-on-exercise.md)。

---

## 课后作业

详见 [`homework.md`](homework.md)。实验环境搭建见 [`lab-environment.md`](lab-environment.md)。

---

## 参考资料

- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) — GPU 内存管理基础
