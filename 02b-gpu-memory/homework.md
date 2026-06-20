# 模块2 高级：GPU 内存管理 — 课后练习

## 题目：GPU 内存层级与传输优化

### 截止时间

模块 3 课前

---

## 任务 1: 理论分析

阅读参考材料，回答：

1. GPU 的 Shared Memory 和 CPU 的 L1 Cache 有什么本质区别？（提示：程序员管理 vs 硬件透明管理）
2. 为什么 GPU 没有 swap？这对 LLM 推理意味着什么？
3. `nvidia-smi` 显示 `memory.free = 10GB`，但 `cudaMalloc(20GB)` 报 OOM。可能的原因是什么？
4. 解释 `cudaMallocHost` (pinned memory) 比 `malloc` (pageable) 传输快的原因。为什么 PCIe 代际越高，pinned 的优势越大？

## 任务 2: 带宽测试 (选做)

在有 GPU 的环境中运行 `code/01_dma_bandwidth.py`，记录结果并绘制 H2D/D2H 带宽对比柱状图。与理论 PCIe 带宽对比，计算效率百分比。

---

## 评分标准

| 维度           | 权重       |
| -------------- | ---------- |
| 理论分析 (4题) | 80%        |
| 带宽测试       | 20% (选做) |

---

## 参考资料

- AI-infra: `vllm-bench/docs/gpu-memory-management.md`
- `visuals/gpu-memory-visual.html` — 6 层交互概念图
- [CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/)
