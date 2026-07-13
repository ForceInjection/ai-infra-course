# 模块 3：GPU 虚拟化与容器化实践

> 90 分钟 &nbsp;|&nbsp; 42 页 PPT &nbsp;|&nbsp; 2 个 C 程序 + 1 个 Python 脚本 &nbsp;|&nbsp; 3 个可视化 HTML

## 可视化 HTML

| 可视化                                                                 | 用途                               | 教学场景                                             |
| ---------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------- |
| [LD_PRELOAD 拦截原理可视化](visuals/ld-preload-flow.html)              | LD_PRELOAD 拦截流程 6 步动画       | 讲解 HAMi CUDA 拦截机制时打开，点击逐步查看拦截原理  |
| [CUDA 软件栈 — 一次 cudaMalloc 调用穿越 5 层](visuals/cuda-stack.html) | CUDA 软件栈 5 层架构 + HAMi 拦截点 | 讲解 CUDA 分层架构时打开，追踪一次 cudaMalloc 全路径 |
| [GPU 虚拟化方案对比](visuals/gpu-sharing-comparison.html)               | 四种方案 — MIG·Time-Slicing·HAMi·MPS | 讲解 GPU 虚拟化方案选型时打开，对比隔离级别与灵活性 |

## 教学流程

| 阶段               | 时长   | PPT 页 | 动手                                                  |
| ------------------ | ------ | ------ | ----------------------------------------------------- |
| GPU 虚拟化方案概览 | 20 min | 3-10   | —                                                     |
| HAMi CUDA 拦截机制 | 30 min | 11-26  | 第 12 页: LD_PRELOAD malloc hook / 第 33 页: 配额测试 |
| GPU 容器化 Runtime | 20 min | 27-35  | —                                                     |
| 动手实验与总结     | 20 min | 36-42  | —                                                     |

## 核心实验

**LD_PRELOAD malloc hook** — 用 60 行 C 代码演示 HAMi 的核心原理：

```bash
gcc -shared -fPIC 01_mymalloc.c -o libmymalloc.so -ldl
LD_PRELOAD=./libmymalloc.so ls       # 每次 malloc 都会被拦截
LD_PRELOAD=./libmymalloc.so ./test_malloc  # 配额=100MB，超限拒绝
```

## 参考来源

- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) — GPU 虚拟化与 HAMi 源码分析
