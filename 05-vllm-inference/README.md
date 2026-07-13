# 模块 5：大模型推理框架入门：以 vLLM 为例

> 120 分钟 &nbsp;|&nbsp; 50 页 PPT &nbsp;|&nbsp; 代码走读 nano-vllm (~1400 行 Python) &nbsp;|&nbsp; 推理服务部署实验

本模块回答一个核心问题：**GPU 给推理服务之后，怎么用得更高效？** LLM 推理 = 自回归生成 → KV Cache → 碎片 → PagedAttention → vLLM 架构 → 部署实践。

---

## 本章内容

| 部分                        | 时长   | PPT 页 | 重点内容                                                                               | 动手                                                   |
| --------------------------- | ------ | ------ | -------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| 大模型推理基础              | 15 min | 3–14   | Transformer回顾、自回归生成、KV Cache概念、推理指标、Naive碎片→PagedAttention          | 实验1: KV Cache 估算 (3min)                            |
| vLLM 架构总览               | 20 min | 15–22  | PagedAttention OS虚拟内存类比、四层架构、Continuous Batching、nano-vllm代码导航        | —                                                      |
| nano-vllm Scheduler 走读    | 30 min | 23–34  | Sequence状态机、schedule()两阶段、Chunked Prefill、Preemption、Continuous Batching时序 | —                                                      |
| nano-vllm BlockManager 走读 | 28 min | 35–46  | Block管理、Prefix Cache链式哈希、PagedAttention实现、LLMEngine主循环、CUDA Graph       | —                                                      |
| vLLM 部署与动手             | 27 min | 47–54  | vLLM服务部署压测、nano-vllm实验、对比总结、Q&A                                         | 实验2: vLLM部署 (10min) + 实验3: nano-vllm追踪 (12min) |

---

## 与模块 6 的边界

| 内容                        | 模块 5 (本模块)            | 模块 6 (KV Cache 优化)   |
| --------------------------- | -------------------------- | ------------------------ |
| KV Cache 概念               | ✅ 概念层面 → 引出碎片问题 | 快速回顾                 |
| KV Cache 显存公式           | 简述公式 + 一个实例        | ✅ 深度推导 + 多模型计算 |
| PagedAttention / vLLM       | ✅ 核心内容                | —                        |
| Offloading / 量化 / LMCache | —                          | ✅ 优化策略              |

---

## 配套代码

| 文件                                          | 内容                            | 对应 PPT    |
| --------------------------------------------- | ------------------------------- | ----------- |
| [`trace_nanovllm.py`](code/trace_nanovllm.py) | nano-vllm monkey-patch 追踪脚本 | 第 49–50 页 |

nano-vllm 源码在独立仓库 [ForceInjection/nano-vllm](https://github.com/ForceInjection/nano-vllm)。

详见 [`code/README.md`](code/README.md)。

---

## 课堂练习

详见 [`hands-on-exercise.md`](hands-on-exercise.md)。

---

## 课后作业

详见 [`homework.md`](homework.md)。实验环境搭建见 [`lab-environment.md`](lab-environment.md)。

---

## 参考资料

- nano-vllm: <https://github.com/ForceInjection/nano-vllm>
- vLLM: <https://github.com/vllm-project/vllm>
- vLLM Paper (SOSP 2023): PagedAttention
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/vllm/)
