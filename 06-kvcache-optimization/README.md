# 模块 6：大模型推理加速实践：KV Cache 原理与优化

> 90 分钟 &nbsp;|&nbsp; 45 页 PPT &nbsp;|&nbsp; 2 个显存计算脚本 &nbsp;|&nbsp; 4 个可视化 HTML

本模块回答三个核心问题：

1. **KV Cache 到底占多少显存？** → 公式 `2×L×H_kv×D×T×B` + 逐参数讲解 + 手算
2. **显存不够怎么办？** → Offloading: 搬到 CPU/NVMe/Remote
3. **能不能让 KV Cache 变小？** → 量化压缩 + 架构演进 (MHA→GQA→MLA)

---

## 本章内容

| 部分                 | 时长   | PPT 页 | 重点内容                                                                                   | 动手             |
| -------------------- | ------ | ------ | ------------------------------------------------------------------------------------------ | ---------------- |
| 回顾与深化           | 25 min | 3–13   | 模块5回顾、显存公式逐参数详解、GQA/MHA/MQA、手算7B/72B、Prefill vs Decode                  | 手算 KV Cache    |
| Offloading           | 20 min | 14–24  | 存储层次金字塔、vLLM CPU Offloading+权衡、LMCache架构+Waterfall+案例、MoonCake PD分离+RDMA | —                |
| 量化与Prefix Caching | 20 min | 25–35  | 量化链+Benchmark、Per-Channel/Token量化、MLA深入、Prefix Caching定量、方案对比             | —                |
| 动手计算与总结       | 25 min | 36–45  | 显存规划实战、LMCache加速实验、容量规划、优化全景图、模块5-6闭环                           | 运行显存计算脚本 |

---

## 可视化 HTML

| 可视化                                                  | 用途                                              | 教学场景                     |
| ------------------------------------------------------- | ------------------------------------------------- | ---------------------------- |
| [KV Cache 公式](visuals/kv-cache-formula.html)          | 公式 `2×L×H_kv×D×T×B` 逐参数拆解 + 示例计算       | 讲解 KV Cache 显存公式时打开 |
| [KV Cache 三维张量形状](visuals/kv-cache-tensor.html)   | 一个 token 的 K/V 张量 [L, H_kv, D] + 精度 B      | 讲解张量形状时打开           |
| [常见精度对比](visuals/kv-cache-precision.html)         | FP16/FP8/INT8/INT4 的字节数与 KV Cache 影响       | 讲解量化压缩时打开           |
| [KV Cache Offloading](visuals/kv-cache-offloading.html) | preempt 驱动的 GPU↔CPU swap (基于 nano-vllm 实现) | 讲解 Offloading 时打开       |

---

## 配套代码

| 文件                                                                      | 内容                      | 对应 PPT  |
| ------------------------------------------------------------------------- | ------------------------- | --------- |
| [`calculate_qwen3_memory.py`](code/calculate_qwen3_memory.py)             | 通用 GQA/MHA 模型显存估算 | 第 6–7 页 |
| [`calculate_deepseek_v4_memory.py`](code/calculate_deepseek_v4_memory.py) | DeepSeek V4 专用估算      | 第 8 页   |

> 显存计算脚本来源: [AI-fundamentals/09_inference_system/memory_calc/](https://github.com/ForceInjection/AI-fundamentals/tree/main/09_inference_system/memory_calc)

详见 [`code/README.md`](code/README.md)。

---

## 课堂练习

详见 [`hands-on-exercise.md`](hands-on-exercise.md)。

---

## 课后作业

详见 [`homework.md`](homework.md)。实验环境搭建见 [`lab-environment.md`](lab-environment.md)。

---

## 参考资料

- [AI-fundamentals/09_inference_system/kv_cache/](https://github.com/ForceInjection/AI-fundamentals/tree/main/09_inference_system/kv_cache)
- [AI-fundamentals/09_inference_system/memory_calc/](https://github.com/ForceInjection/AI-fundamentals/tree/main/09_inference_system/memory_calc)
- vLLM (SOSP 2023): PagedAttention
- LMCache / MoonCake / DeepSeek-V2 (MLA) 论文
