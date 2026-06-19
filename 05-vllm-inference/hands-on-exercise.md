# 模块 5：大模型推理框架入门：以 vLLM 为例 — 课堂动手题

## 题目：vLLM 服务部署 + nano-vllm 源码追踪

### 题目描述

第一部分：使用 vLLM 部署推理服务并压测。
第二部分：安装 nano-vllm，通过添加日志追踪 Sequence 生命周期和 Block 分配过程，深入理解推理引擎内部机制。

### 预计时间
25 分钟 (Part 1: 10 min + Part 2: 15 min)

---

## Part 1: vLLM 部署与压测 (10 min)

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
- `# GPU blocks: XXX` — 每个 Block 存放 block_size 个 token 的 KV Cache
- 计算最大可支持的 context: `GPU_blocks × block_size` (vLLM 默认 block_size=16)

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

记录: Throughput (tok/s), TTFT P50/P95, TPOT

---

## Part 2: nano-vllm 源码追踪实验 (15 min)

### Step 1: 安装 nano-vllm (2 min)

```bash
pip install git+https://github.com/GeeeekExplorer/nano-vllm.git

# 下载模型
huggingface-cli download --resume-download Qwen/Qwen3-0.6B \
    --local-dir ~/huggingface/Qwen3-0.6B/ \
    --local-dir-use-symlinks False

# 验证
python -c "from nanovllm import LLM; print('nano-vllm OK')"
```

### Step 2: 运行基础示例并观察 (5 min)

```bash
# 复制 example.py 作为起点
python -c "
from nanovllm import LLM, SamplingParams

llm = LLM('$HOME/huggingface/Qwen3-0.6B/', enforce_eager=True)
sampling_params = SamplingParams(temperature=0.6, max_tokens=128)

prompts = [
    '你好，请介绍你自己。',
    '什么是GPU?',
]
outputs = llm.generate(prompts, sampling_params)
for i, output in enumerate(outputs):
    print(f'--- Prompt {i+1} ---')
    print(output['text'])
    print()
"
```

### Step 3: 添加追踪日志 — 理解 Sequence 生命周期 (8 min)

创建追踪脚本 `trace_nanovllm.py`:

```python
"""nano-vllm 执行追踪 — 观察 Sequence 状态转换和 Block 分配"""
import sys
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

运行并观察:
```bash
python trace_nanovllm.py 2>&1 | head -80
```

**观察要点**:
1. Sequence 创建时间 (WAITING 状态)
2. Block 分配: 每个 Sequence 分配了多少 Block？有 Prefix Cache 命中吗？
3. 调度阶段: Prefill vs Decode 的交替
4. Sequence 何时 FINISHED？Block 何时回收？
5. 两个请求的调度顺序 (先 Prefill → 然后 Decode 与第二个 Prefill 交替)

---

## 讲解要点

### 1. vLLM 架构与 nano-vllm 源码对照
- vLLM 四层架构在 nano-vllm 中的对应:
  - Scheduler → `engine/scheduler.py` (93 行)
  - Block Manager → `engine/block_manager.py` (121 行)
  - Model Runner → `engine/model_runner.py` (258 行)
  - API Server → vLLM 有但 nano-vllm 无 (nano-vllm 是离线推理)

### 2. Sequence 是推理引擎的「一等公民」
- 所有调度、显存管理都围绕 Sequence 展开
- `block_table` 是 Sequence 与 Block Manager 的纽带
- `num_cached_tokens` 和 `num_scheduled_tokens` 驱动分步执行

### 3. Block Manager 的三个核心操作
- `allocate`: 先查 Prefix Cache (hash 匹配) → 再分配新 Block
- `deallocate`: 引用计数递减 → ref_count=0 时回收
- `hash_blocks`: 计算新 Block 的 hash → 注册到 Prefix Cache

### 4. Scheduler 的两种执行模式
- Prefill: batch 多个序列，可能 Chunked (长 prompt 分裂)
- Decode: 逐个 token 生成，需要 `can_append()` 检查
- 切换条件: `is_prefill` 标志 + `num_cached_tokens == num_tokens`

### 5. 日志中追踪 Preemption
- 当 free blocks 不足时 → Scheduler 从 running 尾部 preempt
- 被 preempt 的序列: deallocate 所有 Block → 重回 WAITING 队列 → 下次重新 allocate
- 这是连续批处理在显存压力下的 fallback

---

## 实验检查点

完成后应能回答:
- [ ] nano-vllm 的 `block_table` 是什么数据结构？它的长度由什么决定？
- [ ] Prefill 和 Decode 在 `schedule()` 中是如何区分的？
- [ ] Prefix Cache 命中的条件是什么？在 `can_allocate()` 中如何检查？
- [ ] 什么情况下 Scheduler 会触发 Preemption？
