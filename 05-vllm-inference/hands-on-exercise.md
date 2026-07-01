# 模块 5：大模型推理框架入门：以 vLLM 为例 — 课堂动手题

## 题目：KV Cache 计算 + vLLM 部署 + nano-vllm 源码追踪

### 题目描述

三个递进实验，从理论到实践：

1. **KV Cache 显存估算** — 手算不同模型的 KV Cache 大小，建立直觉
2. **vLLM 部署与压测** — 启动推理服务，压测分析性能
3. **nano-vllm 源码追踪** — 添加日志追踪 Sequence 生命周期与 Block 分配

### 预计时间

25 分钟

---

## 实验 1: KV Cache 显存估算 (3 min)

> 对应 PPT 第 6–7 页

### 题目

给定以下模型配置，计算单个请求在指定 token 数下的 KV Cache 大小：

| 模型        | n_layers | n_kv_heads | head_dim | dtype |
| ----------- | -------- | ---------- | -------- | ----- |
| Llama-3-8B  | 32       | 8          | 128      | FP16  |
| Qwen2.5-7B  | 28       | 4          | 128      | FP16  |
| Llama-3-70B | 80       | 8          | 128      | FP16  |

**KV Cache 公式**: `2 × n_layers × n_kv_heads × head_dim × n_tokens × dtype_bytes`

计算每个模型在以下场景的 KV Cache:

| 场景        | prompt tokens | output tokens | 总 tokens |
| ----------- | ------------- | ------------- | --------- |
| A: 短问答   | 128           | 128           | 256       |
| B: 中等对话 | 512           | 512           | 1024      |
| C: 长文档   | 4096          | 2048          | 6144      |

**问题**:

1. 场景 C 下，Llama-3-8B 的 KV Cache 是多少 MB？
2. 如果并发 100 个场景 B 的请求，Llama-3-8B 需要多少 GB KV Cache？
3. 一张 H100 80GB 最多能并发多少个场景 C 的 Llama-3-8B 请求？（模型参数约 16GB）

---

## 实验 2: vLLM 部署与压测 (10 min)

> 对应 PPT 第 47–48 页 &nbsp;|&nbsp; 部分 5

### Step 1: 启动 vLLM 服务 (3 min)

```bash
source vllm-env/bin/activate
vllm serve Qwen/Qwen2.5-0.5B-Instruct \
    --host 0.0.0.0 --port 8000 \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.8 \
    --max-num-seqs 32 &
```

观察启动日志:

- `# GPU blocks: XXX` — 每个 Block 存 block_size=16 个 token 的 KV Cache
- 为什么是 XXX 个 Block？对应 PPT 第 43 页的 `allocate_kv_cache()` 公式

### Step 2: API 调用 (2 min)

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B-Instruct",
    "messages": [
      {"role": "system", "content": "你是一个有帮助的AI助手"},
      {"role": "user", "content": "用三句话介绍GPU和CPU的区别"}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }' | python3 -m json.tool | head -20
```

### Step 3: 压测 (5 min)

```bash
pip install aiohttp
wget -q https://raw.githubusercontent.com/vllm-project/vllm/main/benchmarks/benchmark_serving.py

python benchmark_serving.py \
    --backend vllm \
    --model Qwen/Qwen2.5-0.5B-Instruct \
    --dataset-name random \
    --random-input-len 128 \
    --random-output-len 128 \
    --num-prompts 100 \
    --request-rate 4 2>&1 | tee benchmark_result.txt
```

记录关键指标: Throughput (tok/s), TTFT P50/P95, TPOT P50/P95。

**对比题**: 将 `--request-rate` 改为 1、8、16、32，观察 TTFT 和 TPOT 如何变化。找到系统饱和点 (Throughput 不再增长的那个 rate)。

---

## 实验 3: nano-vllm 源码追踪 (12 min)

> 对应 PPT 第 49–50 页 &nbsp;|&nbsp; 部分 5

### Step 1: 安装 nano-vllm (2 min)

```bash
pip install git+https://github.com/ForceInjection/nano-vllm.git

# 下载模型
huggingface-cli download --resume-download Qwen/Qwen3-0.6B \
    --local-dir ~/huggingface/Qwen3-0.6B/ \
    --local-dir-use-symlinks False

# 验证
python -c "from nanovllm import LLM; print('nano-vllm OK')"
```

### Step 2: 基础示例运行 (3 min)

```python
from nanovllm import LLM, SamplingParams

llm = LLM(f'{__import__("os").environ["HOME"]}/huggingface/Qwen3-0.6B/',
          enforce_eager=True)
sampling_params = SamplingParams(temperature=0.6, max_tokens=128)

prompts = [
    '你好，请介绍你自己。',
    '什么是GPU?',
]
outputs = llm.generate(prompts, sampling_params)
for i, output in enumerate(outputs):
    print(f'--- Prompt {i+1} ---')
    print(output['text'])
```

### Step 3: 添加追踪日志 — 观察 Sequence 与 Block (7 min)

创建 `trace_nanovllm.py`:

```python
"""nano-vllm 执行追踪 — 观察 Sequence 状态转换和 Block 分配"""
import os
from nanovllm import LLM, SamplingParams

# ====== Monkey-patch 添加日志 ======
from nanovllm.engine import sequence as seq_mod
from nanovllm.engine import block_manager as bm_mod
from nanovllm.engine import scheduler as sch_mod

_orig_sequence_init = seq_mod.Sequence.__init__
def _traced_init(self, token_ids, sampling_params=None):
    _orig_sequence_init(self, token_ids, sampling_params)
    print(f"[SEQ {self.seq_id}] CREATED | status=WAITING | "
          f"num_tokens={self.num_tokens} | num_blocks={self.num_blocks}")
seq_mod.Sequence.__init__ = _traced_init

_orig_allocate = bm_mod.BlockManager.allocate
def _traced_allocate(self, seq, num_cached_blocks):
    _orig_allocate(self, seq, num_cached_blocks)
    print(f"[BLOCK] ALLOCATE seq={seq.seq_id} | "
          f"cached_blocks={num_cached_blocks} | "
          f"new_blocks={seq.num_blocks - num_cached_blocks} | "
          f"block_table={seq.block_table} | "
          f"free_blocks={len(self.free_block_ids)}")
bm_mod.BlockManager.allocate = _traced_allocate

_orig_deallocate = bm_mod.BlockManager.deallocate
def _traced_deallocate(self, seq):
    print(f"[BLOCK] DEALLOCATE seq={seq.seq_id} | "
          f"block_table={seq.block_table}")
    _orig_deallocate(self, seq)
bm_mod.BlockManager.deallocate = _traced_deallocate

_orig_preempt = sch_mod.Scheduler.preempt
def _traced_preempt(self, seq):
    print(f"[SCHED] PREEMPT seq={seq.seq_id} | reason=OOM (no free blocks)")
    _orig_preempt(self, seq)
sch_mod.Scheduler.preempt = _traced_preempt

_orig_postprocess = sch_mod.Scheduler.postprocess
def _traced_postprocess(self, seqs, token_ids, is_prefill):
    for seq, tok_id in zip(seqs, token_ids):
        phase = "PREFILL" if is_prefill else "DECODE"
        status = seq.status.name
        print(f"[SCHED] STEP seq={seq.seq_id} | phase={phase} | "
              f"token={tok_id} | num_tokens={seq.num_tokens} | "
              f"cached={seq.num_cached_tokens} | status→{status}")
    _orig_postprocess(self, seqs, token_ids, is_prefill)
sch_mod.Scheduler.postprocess = _traced_postprocess

# ====== 运行推理 ======
print("=" * 60)
print("nano-vllm 执行追踪开始")
print("=" * 60)

llm = LLM(
    f"{os.environ['HOME']}/huggingface/Qwen3-0.6B/",
    enforce_eager=True,
    gpu_memory_utilization=0.6,
)
sampling_params = SamplingParams(temperature=0.6, max_tokens=64)

prompts = [
    "你好，请介绍你自己。",
    "什么是GPU? 请详细解释。",
]
outputs = llm.generate(prompts, sampling_params)

print("\n" + "=" * 60)
print("输出结果:")
for i, output in enumerate(outputs):
    print(f"\n--- Prompt {i+1} ---")
    print(output['text'][:200])
```

运行:

```bash
python trace_nanovllm.py 2>&1 | head -80
```

**观察要点**:

1. Sequence 何时创建 (WAITING 状态)
2. Block 分配: 每个 Sequence 分配了多少 Block？有 Prefix Cache 命中吗？
3. Prefill vs Decode 的交替 (观察 `phase=` 日志)
4. Sequence 何时 FINISHED？Block 何时回收？
5. 两个请求的调度顺序 — Continuous Batching 如何交错

---

## 清理

```bash
# 停止 vLLM 服务
kill %1
```

---

## 讲解要点

### 1. KV Cache 显存是第一性原理

- 公式: `2 × L × H_kv × D × T × B`
- 不是模型参数 (固定) → 是动态增长的 → 这才是推理服务的瓶颈
- 「理解了 KV Cache 的大小，就理解了为什么 PagedAttention 是必需的」

### 2. vLLM 四层架构在 nano-vllm 中的对应

- Scheduler → `engine/scheduler.py` (93 行)
- Block Manager → `engine/block_manager.py` (121 行)
- Model Runner → `engine/model_runner.py` (~230 行)
- API Server → vLLM 有但 nano-vllm 无 (nano-vllm 是离线推理)

### 3. PagedAttention = OS 虚拟内存

- Block = Page, Block Table = Page Table
- `block_table[i]` → 物理 Block ID → 间接寻址 → 物理不连续但逻辑连续
- Prefix Cache = 共享 Page (ref_count > 1)
- 「vLLM 的创新是工程系统创新，不是算法创新」

### 4. Continuous Batching 的真谛

- Static: batch 等最长的 → GPU 利用率随完成而下降
- Continuous: 随时加入、随时退出 → GPU 利用率始终接近 100%
- Chunked Prefill: 长 Prompt 不阻塞 Decode → 保护用户体验

### 5. 日志中追踪 Preemption

- 当 free blocks 不足 → Scheduler 从 running 尾部 preempt
- 被 preempt 的序列: deallocate 所有 Block → 重回 WAITING → 下次重新 allocate
- 这是显存压力下的 fallback——设计优雅但代价高昂 (已生成的 token 丢弃)

---

## 实验检查点

完成后应能回答:

- [ ] Qwen2.5-7B, 4096 tokens, FP16 的 KV Cache 是多大? (公式 + 结果)
- [ ] nano-vllm 的 `block_table` 是什么数据结构？它的长度由什么决定？
- [ ] Prefill 和 Decode 在 `schedule()` 中是如何区分的？
- [ ] Prefix Cache 命中的条件是什么？在 `can_allocate()` 中如何检查？
- [ ] 什么情况下 Scheduler 会触发 Preemption？
- [ ] vLLM 压测中，TTFT P99 在什么 request rate 下开始突变？这说明了什么？
