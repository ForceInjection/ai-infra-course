# 模块 2：GPU 硬件架构与 CUDA 编程入门

> 90 分钟 &nbsp;|&nbsp; 53 页 PPT &nbsp;|&nbsp; 4 个 CUDA 程序 &nbsp;|&nbsp; 4 个可视化 HTML

## 目录结构

```text
02-gpu-cuda/
├── README.md
├── syllabus.md / ppt-outline.md / hands-on-exercise.md / homework.md / lab-environment.md
├── code/
│   ├── README.md / Makefile / cuda-docker
│   └── 01_vec_add.cu / 02_matmul_naive.cu / 03_matmul_tiled.cu / 04_device_query.cu
└── visuals/
    ├── gpu-architecture.html / cuda-thread-hierarchy.html
    └── shared-memory-tiling.html / thread-index-mapping.html
```

## 可视化 HTML

| 文件                                                                               | 用途                                  | 教学场景                                          |
| ---------------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------- |
| [GPU 逻辑架构全景 — A100/H100](visuals/gpu-architecture.html)                      | GPU 芯片级 - SM 内部两级缩放          | 讲解硬件架构时打开，点击 SM 放大内部结构          |
| [CUDA 线程层次 — Grid → Block → Warp → Thread](visuals/cuda-thread-hierarchy.html) | Grid - Block - Warp - Thread 四级层级 | 讲解线程层次时打开，切换层级查看                  |
| [Shared Memory Tiling — 矩阵乘法数据流](visuals/shared-memory-tiling.html)         | 矩阵乘法 tiling 数据流，6 步演示      | 讲解 Shared Memory 优化时打开，逐步演示加载和计算 |
| [CUDA 线程索引到数据的映射](visuals/thread-index-mapping.html)                     | 线程索引到数据的 1D/2D/3D 映射        | 讲解索引计算时打开，切换维度查看映射关系          |

## 教学流程

| 阶段          | 时长   | PPT 页 | 动手                                          |
| ------------- | ------ | ------ | --------------------------------------------- |
| GPU 硬件架构  | 25 min | 3-16   | —                                             |
| CUDA 编程模型 | 20 min | 17-29  | —                                             |
| CUDA 编程实战 | 30 min | 30-40  | 第 30 页: 向量加法 / 第 36 页: Tiled 矩阵乘法 |
| 工具链与总结  | 15 min | 41-53  | 第 47 页: Nsight 分析                         |

## 实验环境

| 方式      | 说明                                                                     |
| --------- | ------------------------------------------------------------------------ |
| 本地 CUDA | NVIDIA GPU + CUDA Toolkit 12.8, `make all && make run`                   |
| Docker    | `bash cuda-docker all`, 使用 `nvidia/cuda:12.8.0-devel-ubuntu22.04` 镜像 |

详见 `lab-environment.md` 和 `code/README.md`。

## 参考来源

- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) — GPU 硬件架构、CUDA 编程教程、性能分析
- [CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/) — NVIDIA 官方
