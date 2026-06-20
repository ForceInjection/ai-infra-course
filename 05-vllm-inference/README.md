# 模块 5：大模型推理框架入门：以 vLLM 为例

> 120 分钟 &nbsp;|&nbsp; 50 页 PPT &nbsp;|&nbsp; 代码走读 nano-vllm (~1400 行 Python) &nbsp;|&nbsp; 推理服务部署实验

## 与模块 6 的边界

本模块和模块 6 共同覆盖 KV Cache 技术栈，明确分工：

| 内容                                   | 模块 5 (本模块)            | 模块 6 (KV Cache 优化)   |
| -------------------------------------- | -------------------------- | ------------------------ |
| KV Cache 是什么、为什么需要            | ✅ 概念层面 → 引出碎片问题 | 快速回顾                 |
| KV Cache 显存公式详解 + 多模型手算     | 简述公式 + 一个实例        | ✅ 深度推导 + 多模型计算 |
| Naive 碎片 → PagedAttention            | ✅ 核心内容                | —                        |
| vLLM 架构 + nano-vllm 源码             | ✅ 核心内容                | —                        |
| Offloading / 量化 / LMCache / MoonCake | —                          | ✅ 优化策略              |
| GQA 对 KV Cache 的影响                 | —                          | ✅ 深入分析              |

## 目录结构

```text
05-vllm-inference/
├── README.md                    # 本文件
├── syllabus.md                  # 教学大纲 (120 分钟时间分配)
├── ppt-outline.md               # PPT 大纲 (54 页)
├── hands-on-exercise.md         # 课堂动手题 (3 个实验)
├── homework.md                  # 课后练习 (8 个任务)
├── lab-environment.md           # 实验环境搭建说明
└── code/                        # 配套代码
    ├── README.md                #   使用说明 + 预期输出
    └── trace_nanovllm.py        #   nano-vllm 执行追踪脚本 (PPT 第 49–50 页)
```

> nano-vllm 源码在独立仓库 [ForceInjection/nano-vllm](https://github.com/ForceInjection/nano-vllm)，通过 `pip install` 安装，无需复制。

## 教学流程

| 部分                        | 时长   | PPT 页 | 重点内容                                                                                              | 动手                                                   |
| --------------------------- | ------ | ------ | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| 大模型推理基础              | 15 min | 3–14   | Transformer回顾、自回归生成、KV Cache概念+简述公式(详见模块6)、推理指标、Naive碎片→引出PagedAttention | 实验1: KV Cache 估算 (3min)                            |
| vLLM 架构总览               | 20 min | 15–22  | PagedAttention OS虚拟内存类比、四层架构、Continuous Batching、Chunked Prefill、nano-vllm代码导航      | —                                                      |
| nano-vllm Scheduler 走读    | 30 min | 23–34  | Sequence状态机、schedule()两阶段、Chunked Prefill、Preemption、Continuous Batching时序                | —                                                      |
| nano-vllm BlockManager 走读 | 28 min | 35–46  | Block管理、Prefix Cache链式哈希、PagedAttention实现、LLMEngine主循环、CUDA Graph                      | —                                                      |
| vLLM 部署与动手             | 27 min | 47–54  | vLLM服务部署压测、nano-vllm实验、对比总结、Q&A                                                        | 实验2: vLLM部署 (10min) + 实验3: nano-vllm追踪 (12min) |

## 课程简介

本模块回答一个核心问题：**GPU 给推理服务之后，怎么用得更高效？**

**认知路径**:

1. LLM 推理 = 自回归生成 → KV Cache 是必需的 → KV Cache 随 token 线性增长 → 显存是瓶颈
2. Naive 预分配连续显存 → 碎片 → 利用率 20-40% → 需要"虚拟化"
3. PagedAttention = OS 虚拟内存搬到 GPU → Block + Block Table → 碎片率 <4%
4. nano-vllm 1400 行 Python = vLLM 核心骨架
5. vLLM 部署实践

## 实验环境

详见 `lab-environment.md`。

## 动手实验

| 实验                  | 时长   | 主题                                         |
| --------------------- | ------ | -------------------------------------------- |
| 实验1: KV Cache 估算  | 3 min  | 手算显存 (简述公式，深度计算在模块6)         |
| 实验2: vLLM 部署压测  | 10 min | vLLM serve → benchmark → 分析 TTFT/TPOT      |
| 实验3: nano-vllm 追踪 | 12 min | Monkey-patch → 观察 Sequence/Block/Scheduler |

## 课后作业

详见 `homework.md` (8 个任务覆盖 KV Cache 计算、vLLM 压测、nano-vllm 源码分析)。

## 参考来源

- nano-vllm: https://github.com/ForceInjection/nano-vllm
- nano-vllm 在线课程: https://forceinjection.github.io/nano-vllm/
- vLLM: https://github.com/vllm-project/vllm
- vLLM Paper (SOSP 2023)
- AI-fundamentals: `09_inference_system/vllm/`
