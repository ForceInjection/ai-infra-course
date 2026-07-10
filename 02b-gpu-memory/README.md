# 模块2 高级：GPU 内存管理

> 15–20 分钟 &nbsp;|&nbsp; 12 页 PPT &nbsp;|&nbsp; 2 个可视化 HTML &nbsp;|&nbsp; 2 个带宽测试脚本

GPU 内存管理附录，从 CPU/GPU 对称性出发，介绍内存层级、DMA 传输、Pinned vs Pageable、碎片化和跨进程共享。

## 目录结构

```text
02b-gpu-memory/
├── README.md                          # 本文件
├── syllabus.md                        # 教学大纲
├── ppt-outline.md                     # PPT 大纲 (12 页)
├── hands-on-exercise.md               # 课堂动手题
├── homework.md                        # 课后练习
├── lab-environment.md                 # 实验环境说明
├── code/
│   ├── README.md                      #   运行说明 + 预期输出
│   ├── 01_dma_bandwidth.py              #   CPU↔GPU 带宽测试 (Python ctypes)
│   └── 02_dma_bandwidth.cu              #   CPU↔GPU 带宽测试 (CUDA C)
└── visuals/
    ├── gpu-memory-visual.html         # 6 层交互概念图
    └── dma-benchmark.html            # DMA 深度剖析 — Pinned vs Pageable
```

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

## 参考来源

- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) — GPU 内存管理基础
