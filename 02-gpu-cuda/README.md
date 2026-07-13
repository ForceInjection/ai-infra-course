# 模块 2：GPU 硬件架构与 CUDA 编程入门

> 90 分钟 &nbsp;|&nbsp; 53 页 PPT &nbsp;|&nbsp; 4 个 CUDA 程序 &nbsp;|&nbsp; 5 个可视化 HTML

---

## 本章内容

| 阶段          | 时长   | PPT 页 | 动手                                          |
| ------------- | ------ | ------ | --------------------------------------------- |
| GPU 硬件架构  | 25 min | 3-16   | —                                             |
| CUDA 编程模型 | 20 min | 17-29  | —                                             |
| CUDA 编程实战 | 30 min | 30-40  | 第 30 页: 向量加法 / 第 36 页: Tiled 矩阵乘法 |
| 工具链与总结  | 15 min | 41-53  | 第 47 页: Nsight 分析                         |

---

## 可视化 HTML

| 文件                                                                               | 用途                                    | 教学场景                                                          |
| ---------------------------------------------------------------------------------- | --------------------------------------- | ----------------------------------------------------------------- |
| [GPU 逻辑架构全景 — A100/H100](visuals/gpu-architecture.html)                      | GPU 芯片级 - SM 内部两级缩放            | 讲解硬件架构时打开，点击 SM 放大内部结构                          |
| [CUDA 线程层次 — Grid → Block → Warp → Thread](visuals/cuda-thread-hierarchy.html) | Grid - Block - Warp - Thread 四级层级   | 讲解线程层次时打开，切换层级查看                                  |
| [Shared Memory Tiling — 矩阵乘法数据流](visuals/shared-memory-tiling.html)         | 矩阵乘法 tiling 数据流，6 步演示        | 讲解 Shared Memory 优化时打开，逐步演示加载和计算                 |
| [CUDA 线程索引到数据的映射](visuals/thread-index-mapping.html)                     | 线程索引到数据的 1D/2D/3D 映射          | 讲解索引计算时打开，切换维度查看映射关系                          |
| [线程层次映射](visuals/cuda-thread-hardware-mapping.html)                          | 软件配置 → 逻辑层次 → 物理硬件 三列对照 | 讲解 Grid/Block/Warp/Thread 与 SM/Warp Scheduler/CUDA Core 的映射 |

---

## 配套代码

| 文件                                            | 内容                      | 对应 PPT |
| ----------------------------------------------- | ------------------------- | -------- |
| [`01_vec_add.cu`](code/01_vec_add.cu)           | CUDA 向量加法             | 第 30 页 |
| [`02_matmul_naive.cu`](code/02_matmul_naive.cu) | 朴素矩阵乘法              | 第 36 页 |
| [`03_matmul_tiled.cu`](code/03_matmul_tiled.cu) | Shared Memory Tiling 优化 | 第 36 页 |
| [`04_device_query.cu`](code/04_device_query.cu) | GPU 设备信息查询          | 第 47 页 |

详见 [`code/README.md`](code/README.md)。

---

## 课堂练习

详见 [`hands-on-exercise.md`](hands-on-exercise.md)。

---

## 课后作业

详见 [`homework.md`](homework.md)。实验环境搭建见 [`lab-environment.md`](lab-environment.md)。

---

## 参考资料

- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) — GPU 硬件架构、CUDA 编程教程、性能分析
- [CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/) — NVIDIA 官方
