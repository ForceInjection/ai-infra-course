# 模块 6：大模型推理加速实践：KV Cache 原理与优化 — 课后练习

## 题目：KV Cache 容量规划与优化方案设计

### 目标

编写一个 KV Cache 显存估算工具，针对给定的业务场景进行容量规划，并设计最优的 KV Cache 分层存储方案。

### 截止时间

下次课前 (一周)

---

## 基础任务 (必做)

### 任务 1: 通用 KV Cache 估算器

编写一个 Python 脚本 `kv_cache_estimator.py`，接收模型配置和业务参数，输出 KV Cache 显存估算：

```python
# kv_cache_estimator.py
def estimate_kv_cache(model_config: dict, seq_len: int, batch_size: int,
                       dtype: str = "fp16") -> dict:
    """
    model_config: {
        "n_layers": int,
        "n_kv_heads": int,
        "d_head": int,
        "model_params_gb": float   # 模型权重大小
    }
    返回: {
        "kv_cache_gb": float,
        "model_gb": float,
        "total_gb": float,
        "kv_ratio": float           # KV Cache 占总显存的比例
    }
    """
    pass
```

**要求**:

- 支持 FP16/FP8/INT8/INT4 四种精度
- 支持 GQA 配置
- 输出格式化表格
- 给出 GPU 推荐 (如: "需要 1×A100-80G" 或 "需要 2×H100 80G")

使用该工具完成 Qwen2.5-7B/14B/72B 和 DeepSeek-V3 的显存估算表。

### 任务 2: 业务场景容量规划

假设你需要在以下三种场景中部署 LLM 推理服务：

| 场景          | 模型        | 平均 Prompt  | 平均输出    | 并发 |
| ------------- | ----------- | ------------ | ----------- | ---- |
| A: 客服系统   | Qwen2.5-7B  | 1500 tokens  | 200 tokens  | 50   |
| B: 代码助手   | Qwen2.5-14B | 8000 tokens  | 500 tokens  | 20   |
| C: 长文档分析 | Qwen2.5-72B | 30000 tokens | 1000 tokens | 5    |

对每个场景:

1. 计算 FP16 下的 KV Cache 显存需求
2. 计算使用 INT8 量化后的显存需求
3. 如果使用 LMCache L1 (HBM) + L2 (CPU) 分层，应如何分配容量？
4. 推荐 GPU 配置和数量

### 任务 3: Prefix Caching 命中率分析

编写脚本模拟 prefix caching 的命中率：

```python
# 假设场景:
# - 系统 Prompt 固定 2000 tokens
# - 用户问题随机 50-200 tokens (每次不同)
# - 100 个并发用户

# 计算:
# 1. 无 Prefix Caching: 每个请求的 Prefill 计算量
# 2. 有 Prefix Caching: 命中系统 Prompt 时的 Prefill 计算量
# 3. 节省的计算量比例
```

---

## 进阶任务 (选做)

### 任务 4: LMCache 部署实验

在实际环境中部署 LMCache + vLLM，完成：

```bash
# 1. 安装并配置 LMCache
pip install lmcache

# 2. 配置多层存储
export LMCACHE_CONFIG='{
  "l1": {"backend": "cpu", "max_size_gb": 32},
  "l2": {"backend": "disk", "path": "/tmp/lmcache", "max_size_gb": 128}
}'

# 3. 启动 vLLM + LMCache 服务
# 4. 运行多轮对话测试，对比:
#    - 无缓存
#    - L1 only (CPU)
#    - L1 + L2 (CPU + Disk)
#    的 TTFT and throughput
```

### 任务 5: 阅读 LMCache 或 KVBM 源码

从 AI-fundamentals 中选择一个 KV Cache 系统源码分析：

- **LMCache** (推荐): `09_inference_system/kv_cache/02_systems/lmcache/`
- **KVBM** (进阶): `09_inference_system/kv_cache/02_systems/kvbm/`

分析存储后端的核心实现逻辑 (如 LocalCPUBackend 的缓存管理)。

---

## 提交要求

1. 提交 `kv_cache_estimator.py` 及运行结果
2. 提交业务场景容量规划报告 (≤ 3 页)，包含：
   - 三个场景的显存估算
   - 分层存储分配方案
   - GPU 配置推荐
3. 提交 Prefix Caching 命中率分析
4. (选做) LMCache 实验数据和源码分析

---

## 评分标准

| 维度            | 权重 | 要求                       |
| --------------- | ---- | -------------------------- |
| 任务 1-3 完成度 | 60%  | 估算器正确、场景分析完整   |
| 分析质量        | 25%  | 推荐方案有依据、有数据支撑 |
| 进阶任务        | 15%  | 完成至少一项进阶任务       |

---

## 参考资料

- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/kv_cache/) 全套 KV Cache 技术文档
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/memory_calc/calculate_qwen3_memory.py) — 显存计算脚本
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/memory_calc/calculate_deepseek_v4_memory.py)
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/kv_cache/01_concepts/capacity_planning/glm5_kv_cache_capacity_planning.md)
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/kv_cache/01_concepts/capacity_planning/kv_cache_roi.md)
- [LMCache GitHub](https://github.com/LMCache/LMCache)
