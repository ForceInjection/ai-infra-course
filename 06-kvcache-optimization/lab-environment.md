# 模块 6：大模型推理加速实践：KV Cache 原理与优化 — 实验环境说明

## 环境要求

### 硬件要求

| 项目 | 最低配置           | 推荐配置                      |
| ---- | ------------------ | ----------------------------- |
| CPU  | 8 核, ≥ 32 GB 内存 | 16 核+, 64 GB+ 内存           |
| 内存 | 32 GB              | 64 GB+ (用于 Offloading 实验) |
| 磁盘 | 100 GB NVMe SSD    | 200 GB+                       |
| GPU  | ≥ 8 GB 显存        | ≥ 16 GB 显存                  |

### 软件要求

| 软件    | 版本    | 用途              |
| ------- | ------- | ----------------- |
| Python  | ≥ 3.10  | 运行推理框架      |
| vLLM    | ≥ 0.6.0 | 推理引擎          |
| LMCache | ≥ 0.1   | KV Cache 分层存储 |

---

## 环境搭建

### Step 1: 基础环境 (同模块 5)

```bash
python3 -m venv kvcache-env
source kvcache-env/bin/activate
pip install vllm
```

### Step 2: 安装 LMCache

```bash
pip install lmcache

# 或从源码安装
# git clone https://github.com/LMCache/LMCache.git
# cd LMCache && pip install -e .
```

### Step 3: 下载显存计算脚本

从 AI-fundamentals 获取计算脚本:

```bash
# 如果已有克隆的 AI-fundamentals 仓库
cp https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/memory_calc/calculate_qwen3_memory.py .
```

---

## 环境验证

```bash
# 1. 验证 vLLM 基本功能
vllm serve Qwen/Qwen2.5-0.5B-Instruct --port 8000 &
sleep 20
curl http://localhost:8000/v1/models
kill %1

# 2. 验证显存计算脚本
python calculate_qwen3_memory.py

# 3. 验证 LMCache
python -c "import lmcache; print('LMCache OK')"
```

---

## KV Cache 显存计算参考

```python
# kv_cache_calc.py — 课堂使用
def calc_kv_cache_gb(
    n_layers: int,
    n_kv_heads: int,
    d_head: int,
    seq_len: int,
    batch_size: int,
    dtype: str = "fp16"
):
    dtype_bytes = {"fp16": 2, "fp8": 1, "fp4": 0.5, "int8": 1}
    bytes_per_elem = dtype_bytes[dtype]
    kv_cache = 2 * n_layers * n_kv_heads * d_head * seq_len * batch_size * bytes_per_elem
    return kv_cache / (1024**3)

# Qwen2.5-7B: L=28, H_kv=4, D=128
# Qwen2.5-72B: L=80, H_kv=8, D=128
models = {
    "Qwen2.5-0.5B": (24, 2, 64),
    "Qwen2.5-7B": (28, 4, 128),
    "Qwen2.5-72B": (80, 8, 128),
}

for name, (L, H_kv, D) in models.items():
    kv = calc_kv_cache_gb(L, H_kv, D, 4096, 32)
    print(f"{name}: KV Cache = {kv:.1f} GB (seq_len=4096, batch=32, fp16)")
```
