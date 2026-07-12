# 模块 6：大模型推理加速实践：KV Cache 原理与优化

> 90 分钟 &nbsp;|&nbsp; 45 页 PPT &nbsp;|&nbsp; 2 个显存计算脚本 &nbsp;|&nbsp; 3 个可视化 HTML

## 目录结构

```text
06-kvcache-optimization/
├── README.md                    # 本文件
├── syllabus.md                  # 教学大纲 (90 分钟时间分配)
├── ppt-outline.md               # PPT 大纲 (45 页)
├── hands-on-exercise.md         # 课堂动手题
├── homework.md                  # 课后练习
├── lab-environment.md           # 实验环境搭建说明
└── code/                        # 配套显存计算脚本 (2 个 + config)
    ├── README.md                #   使用说明 + 预期输出
    ├── calculate_qwen3_memory.py    #   通用 GQA/MHA 模型显存估算 (PPT 第 6–7 页)
    ├── qwen3_06b_config.json        #   Qwen3-0.6B 配置样例
    ├── calculate_deepseek_v4_memory.py  # DeepSeek V4 专用估算 (PPT 第 8 页)
    └── deepseek_v4_pro_config.json      # DeepSeek V4 Pro 配置样例
└── visuals/                                 # 可视化 HTML (3 个)
    ├── kv-cache-formula.html                #   KV Cache 公式参数来源图
    ├── kv-cache-tensor.html                 #   KV Cache 三维张量形状 [L, H_kv, D]
    └── kv-cache-precision.html              #   常见精度对比 — FP16/FP8/INT8/INT4
```

> 显存计算脚本来源: [AI-fundamentals/09_inference_system/memory_calc/](https://github.com/ForceInjection/AI-fundamentals/tree/main/09_inference_system/memory_calc)

## 可视化 HTML

| 可视化                                                              | 用途                                         | 教学场景                                         |
| ------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------ |
| [KV Cache 公式 — 每个参数的物理来源](visuals/kv-cache-formula.html) | 公式 `2×L×H_kv×D×T×B` 逐参数拆解 + 示例计算  | 讲解 KV Cache 显存公式时打开，逐项理解参数来源   |
| [KV Cache 三维张量形状](visuals/kv-cache-tensor.html)               | 一个 token 的 K/V 张量 [L, H_kv, D] + 精度 B | 讲解张量形状时打开，直观理解 L/H_kv/D/B 如何构成 |
| [常见精度对比](visuals/kv-cache-precision.html)                      | FP16/FP8/INT8/INT4 的字节数与 KV Cache 影响  | 讲解量化压缩时打开，对比不同精度下的显存节省        |

## 与模块 5 的边界

| 内容                    | 模块 5                | 模块 6 (本模块)                        |
| ----------------------- | --------------------- | -------------------------------------- |
| KV Cache 概念           | 概念引入 + 动机       | 快速回顾 (3 min)                       |
| KV Cache 显存公式       | 简述 + 一个实例       | **深度推导 + 逐参数讲解 + 多模型手算** |
| PagedAttention / vLLM   | 核心内容              | —                                      |
| Offloading 卸载         | —                     | **GPU↔CPU↔NVMe 存储层次**              |
| KV Cache 量化压缩       | —                     | **FP16→FP8→INT4，精度 vs 显存**        |
| Prefix Caching 收益分析 | 概念 (nano-vllm 实现) | **定量分析: 首 token 延迟降低 80-95%** |
| GQA/MQA/MLA 架构分析    | —                     | **深入: 压缩比 × 精度 trade-off**      |

## 教学流程

| 部分                 | 时长   | PPT 页 | 重点内容                                                                                                 | 动手                     |
| -------------------- | ------ | ------ | -------------------------------------------------------------------------------------------------------- | ------------------------ |
| 回顾与深化           | 25 min | 3–13   | 模块5回顾、显存公式逐参数详解、GQA/MHA/MQA、手算7B/72B、跨模型对比、Prefill vs Decode、显存全景图        | 手算 KV Cache (第6-7页)  |
| Offloading           | 20 min | 14–24  | 存储层次金字塔、vLLM CPU Offloading+权衡、LMCache架构+Waterfall+案例、MoonCake PD分离+RDMA、Tair、决策树 | —                        |
| 量化与Prefix Caching | 20 min | 25–35  | 量化链+Benchmark、Per-Channel/Token量化、MLA深入、Prefix Caching定量、方案对比、前沿方案、ICMS           | —                        |
| 动手计算与总结       | 25 min | 36–45  | 显存规划实战、LMCache加速实验、容量规划、优化全景图、模块5-6闭环、决策框架                               | 运行显存计算脚本 (第9页) |

## 课程简介

本模块回答三个核心问题：

1. **KV Cache 到底占多少显存？** → 公式 `2×L×H_kv×D×T×B` + 逐参数讲解 + 手算
2. **显存不够怎么办？** → Offloading: 搬到 CPU/NVMe/Remote
3. **能不能让 KV Cache 变小？** → 量化压缩 (FP16→INT4) + 架构演进 (MHA→GQA→MLA)

**认知路径** (从公式出发):

```text
KV Cache = 2 × L × H_kv × D × T × B

每个参数对应一条优化方向:
├─ B (dtype_bytes): FP16→FP8→INT4       → 量化压缩 (省 2-4×)
├─ H_kv:            MHA→GQA→MLA          → 架构演进 (省 4-64×)
├─ T (n_tokens):    冷数据搬走            → Offloading (存储层次)
└─ 共享:            相同 Prefix 不重复存   → Prefix Caching
```

## 实验环境

| 软件    | 版本    | 用途                |
| ------- | ------- | ------------------- |
| Python  | ≥ 3.8   | 运行显存计算脚本    |
| vLLM    | ≥ 0.6.0 | LMCache 实验 (可选) |
| LMCache | latest  | 分层存储实验 (可选) |

## 动手实验

| 实验          | 主题                               | 工具                                                                 |
| ------------- | ---------------------------------- | -------------------------------------------------------------------- |
| 手算 KV Cache | 跟着公式计算 Qwen2.5-7B/72B 的显存 | 纸笔 / [`calculate_qwen3_memory.py`](code/calculate_qwen3_memory.py) |
| 显存规划实战  | 为 Qwen2.5-72B + H100×4 规划显存   | `calculate_qwen3_memory.py`                                          |
| LMCache 加速  | 多轮对话场景下观察缓存命中         | vLLM + LMCache                                                       |

详见 `hands-on-exercise.md`。

## 课后作业

详见 `homework.md`。

## 参考来源

- [AI-fundamentals/09_inference_system/kv_cache/](https://github.com/ForceInjection/AI-fundamentals/tree/main/09_inference_system/kv_cache) — KV Cache 全套文档
- [AI-fundamentals/09_inference_system/memory_calc/](https://github.com/ForceInjection/AI-fundamentals/tree/main/09_inference_system/memory_calc) — 显存计算脚本
- vLLM (SOSP 2023): PagedAttention
- LMCache / MoonCake / DeepSeek-V2 (MLA) 论文
