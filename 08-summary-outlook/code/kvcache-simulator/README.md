# 方向 C: KV Cache 显存管理 — 从公式到系统

**难度**: ★★★★ &nbsp;|&nbsp; **覆盖模块**: 2 (GPU 内存), 5 (PagedAttention), 6 (KV Cache)

**零硬件依赖** — 纯 Python 标准库 + matplotlib，任何笔记本都能完成。

## 快速开始

```bash
# 1. 显存计算
python calculator.py --preset qwen2.5-7b --dtype fp16

# 2. 碎片模拟
python simulator.py --requests 100 --gpu-mem-gb 40

# 3. Prefix Cache 命中率
python lru_cache.py --requests 200 --capacity 1000

# 4. 生成图表 (需要 matplotlib)
pip install matplotlib
python visualize.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `calculator.py` | KV Cache 显存计算器 — 搜索 `TODO` 完成公式和表格 |
| `simulator.py` | PagedAttention 碎片模拟器 — Naive vs PA 两种管理器 |
| `lru_cache.py` | Prefix Cache LRU 模拟 — 链式哈希 + 淘汰策略 |
| `visualize.py` | matplotlib 图表生成 — 4 张图直接用于报告 |

## 推荐完成顺序

1. `calculator.py` — 最简单，检验公式理解
2. `visualize.py` — 用计算结果生成图表
3. `lru_cache.py` — LRU 逻辑，中等难度
4. `simulator.py` — 最复杂，离散事件模拟 + 两种内存管理算法
