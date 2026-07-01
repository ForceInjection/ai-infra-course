# 模块 2：GPU 硬件架构与 CUDA 编程入门

> 90 分钟 &nbsp;|&nbsp; 53 页 PPT &nbsp;|&nbsp; 4 个 CUDA 程序 &nbsp;|&nbsp; 4 个可视化 HTML

## 目录结构

```text
02-gpu-cuda/
├── README.md                          # 本文件
├── syllabus.md                        # 教学大纲 (90 分钟时间分配)
├── ppt-outline.md                     # PPT 大纲 (53 页)
├── hands-on-exercise.md               # 课堂动手题 (3 个实验)
├── homework.md                        # 课后练习
├── lab-environment.md                 # 实验环境搭建说明
├── GPU 硬件架构与 CUDA 编程入门.pptx   # 课件
├── code/                              # 配套 CUDA 源码 (4 个)
│   ├── README.md                      #   编译运行说明 + 预期输出
│   ├── Makefile                       #   一键编译
│   ├── cuda-docker                    #   Docker 编译运行脚本
│   ├── 01_vec_add.cu                  #   向量加法 (PPT §3, 第30-31页)
│   ├── 02_matmul_naive.cu             #   Naive 矩阵乘法 (PPT §3, 第33-34页)
│   ├── 03_matmul_tiled.cu             #   Tiled 矩阵乘法 (PPT §3, 第36页)
│   └── 04_device_query.cu             #   GPU 设备查询
└── visuals/                           # 可视化 HTML (4 个)
    ├── gpu-architecture.html          #   GPU 逻辑架构全景 (PPT 第4-5页)
    ├── cuda-thread-hierarchy.html     #   Grid→Block→Warp→Thread (PPT 第20-21页)
    ├── shared-memory-tiling.html      #   Shared Memory Tiling (PPT 第35-36页)
    └── thread-index-mapping.html      #   线程索引映射 1D/2D/3D (PPT 第28页)
```

## 可视化 HTML

| 文件                         | 用途                                  | 教学场景                                          |
| ---------------------------- | ------------------------------------- | ------------------------------------------------- |
| `gpu-architecture.html`      | GPU 芯片级 → SM 内部两级缩放          | 讲解硬件架构时打开，点击 SM 放大内部结构          |
| `cuda-thread-hierarchy.html` | Grid → Block → Warp → Thread 四级层级 | 讲解线程层次时打开，切换层级查看                  |
| `shared-memory-tiling.html`  | 矩阵乘法 tiling 数据流，6 步演示      | 讲解 Shared Memory 优化时打开，逐步演示加载和计算 |
| `thread-index-mapping.html`  | 线程索引到数据的 1D/2D/3D 映射        | 讲解索引计算时打开，切换维度查看映射关系          |

## 教学流程

| 阶段          | 时长   | PPT 页 | 动手                                      |
| ------------- | ------ | ------ | ----------------------------------------- |
| GPU 硬件架构  | 25 min | 3–16   | —                                         |
| CUDA 编程模型 | 20 min | 17–29  | —                                         |
| CUDA 编程实战 | 30 min | 30–40  | 第30页：向量加法 / 第36页：Tiled 矩阵乘法 |
| 工具链与总结  | 15 min | 41–53  | 第47页：Nsight 分析                       |

## 实验环境

| 方式      | 说明                                                   |
| --------- | ------------------------------------------------------ |
| 本地 CUDA | 需要 NVIDIA GPU + CUDA Toolkit，`make all && make run` |
| Docker    | 使用 `cuda-docker` 脚本，需要包含 nvcc 的 CUDA 镜像    |

## 参考来源

- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) — GPU 硬件架构、CUDA 编程教程、性能分析
- [nano-vllm](https://github.com/ForceInjection/nano-vllm) — 精简版 vLLM 实现
- [CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/) — NVIDIA 官方
