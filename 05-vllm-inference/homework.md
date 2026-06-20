# 模块 5：大模型推理框架入门：以 vLLM 为例 — 课后练习

## 题目：vLLM 推理性能分析 + nano-vllm 源码深度阅读

### 目标

通过系统压测 vLLM 理解推理性能，同时深度阅读 nano-vllm 的 1400 行源码，掌握推理引擎的核心实现。

### 截止时间

下次课前 (一周)

---

## 基础任务 (必做)

### 任务 1: KV Cache 显存计算与分析

使用 KV Cache 公式 `2 × L × H_kv × D × T × B`，完成以下计算：

1. 计算 Qwen2.5-7B (L=28, H_kv=4, D=128, FP16) 在以下场景的 KV Cache 大小：
   - 1 个请求, 4096 tokens
   - 1 个请求, 32768 tokens (长上下文)
   - 100 个并发请求, 各 2048 tokens
2. 一张 A100 80GB 最多能并发服务多少个 Llama-3-8B 的请求 (模型参数 ~16GB, 每个请求 2048 tokens)?
3. 如果将 KV Cache 从 FP16 量化到 FP8，同样的显存能服务多少倍的请求？INT8 呢？
4. 为什么 GQA (Grouped Query Attention, H_kv < H_q) 能减少 KV Cache？以 Llama-3-70B (H_q=64, H_kv=8) 为例，GQA 相比 MHA (H_kv=64) 节省了多少倍 KV Cache？

### 任务 2: vLLM 系统化性能评测

使用 vLLM benchmark 工具，完成评测矩阵：

| 变量     | 取值                                  |
| -------- | ------------------------------------- |
| 模型     | Qwen2.5-0.5B, (Qwen2.5-7B 如显存允许) |
| 输入长度 | 128, 512, 1024                        |
| 输出长度 | 128, 256                              |
| 请求速率 | 1, 4, 8, 16, 32                       |

绘制三张曲线图并分析:

1. Throughput vs Request Rate — 找到系统饱和点
2. TTFT P50/P95/P99 vs Request Rate — 分析延迟增长
3. TPOT vs Input Length — 验证 TPOT 是否独立于 input length

### 任务 3: nano-vllm Sequence 生命周期分析

阅读 `nanovllm/engine/sequence.py` (84 行)，回答:

1. `SequenceStatus` 有哪些状态？画出状态转换图
2. `block_table` 是什么类型？它的长度由 `num_blocks` 属性决定，写出 `num_blocks` 的计算公式
3. `is_prefill` 标志在何时设为 True / False？
4. `num_cached_tokens` 和 `num_scheduled_tokens` 的区别是什么？
5. `last_block_num_tokens` 如何计算？在 `model_runner.py:prepare_decode()` 中如何被使用？

### 任务 4: nano-vllm Scheduler 调度逻辑分析

阅读 `nanovllm/engine/scheduler.py` (93 行)，回答:

1. `schedule()` 方法中，Prefill 阶段和 Decode 阶段如何区分？（代码中的 if/else 分支条件）
2. Chunked Prefill 在代码中的哪一行实现？什么条件触发 Chunked Prefill？
3. Preemption 的逻辑是什么？从 `running` 队列的哪一端 pop？为什么要 `appendleft` 到 `waiting`？
4. `postprocess()` 中，`hash_blocks()` 调用在 `append_token()` 之前还是之后？为什么？
5. 如果一个 Sequence 的 `num_completion_tokens == max_tokens`，它会进入什么状态？它的 Block 会被立即回收吗？

### 任务 5: nano-vllm BlockManager 分析

阅读 `nanovllm/engine/block_manager.py` (121 行)，回答:

1. `compute_hash()` 的 `prefix` 参数有什么作用？为什么需要链式哈希？
2. `can_allocate()` 返回值 -1 表示什么？返回值 ≥ 0 表示什么？
3. `allocate()` 中，已缓存的 Block 和新增 Block 的处理逻辑有何不同？
4. `ref_count` 如何支持 Copy-on-Write？当两个 Sequence 共享一个 Block 时，ref_count 的变化过程是怎样的？
5. `hash_blocks()` 为什么只 hash `num_cached_tokens` 到 `num_cached_tokens + num_scheduled_tokens` 范围？

---

## 进阶任务 (选做)

### 任务 6: nano-vllm PagedAttention 实现

阅读 `nanovllm/layers/attention.py` + `engine/model_runner.py::prepare_prefill/ prepare_decode`，完成:

1. 画出 Prefill 阶段 `slot_mapping` 的构建过程（以 2 个 Sequence, block_size=256 为例）
2. Decode 阶段每个 Sequence 的 `slot_mapping` 只有一个值 — 为什么？它的计算公式是什么？
3. `block_tables` 的 shape 是 `[num_seqs, max_blocks_per_seq]` — 为什么需要 padding 到相同长度？
4. 在 `attention.py` 中，Prefill 使用 `flash_attn_varlen_func`，Decode 使用 `flash_attn_with_kvcache` — 两个函数的区别是什么？（查看 flash_attn 文档）
5. `store_kvcache_kernel` (Triton kernel) 中 `slot == -1` 的判断有什么作用？

### 任务 7: nano-vllm 主循环与 CUDA Graph

阅读 `nanovllm/engine/llm_engine.py` + `engine/model_runner.py::capture_cudagraph`，完成:

1. `LLMEngine.step()` 的三步流程是什么？画出数据流图 (schedule → run → postprocess)
2. `generate()` 如何知道所有序列都已完成？`is_finished()` 的判断条件是什么？
3. CUDA Graph 为什么只用于 Decode 阶段？Prefill 为什么不能用？
4. `graph_bs = [1, 2, 4, 8, 16, 32, ...]` — 为什么需要多个不同 batch size 的 graph？
5. 当 `enforce_eager=True` 时，CUDA Graph 是否生效？

---

## 任务 8 (选做): 扩展 nano-vllm

为 nano-vllm 添加一个新功能 (任选一):

1. **优先级调度**: 为 Sequence 添加 `priority` 字段，Scheduler 优先调度高优先级序列
2. **统计信息**: 在 `generate()` 返回前，打印每个 Sequence 的 TTFT / TPOT / total tokens
3. **多轮对话支持**: 实现 `add_request()` 的多轮对话 API，自动携带历史 KV Cache

---

## 提交要求

1. 提交 KV Cache 计算结果和分析
2. 提交性能评测脚本和结果数据 (含图表)
3. 提交 nano-vllm 源码分析报告 (≤ 5 页)，包含：
   - 任务 3-5 的所有问题的回答
   - 关键代码片段的注释和分析
   - (选做) 任务 6-8 的分析和代码
4. 回答：
   - nano-vllm 的 1400 行代码中，你认为哪个模块最核心？为什么？
   - 如果将 nano-vllm 改造成在线推理服务（类似 vLLM API Server），需要增加哪些组件？

---

## 评分标准

| 维度                   | 权重 | 要求                       |
| ---------------------- | ---- | -------------------------- |
| 任务 1 (KV Cache 计算) | 15%  | 公式正确、计算准确、有分析 |
| 任务 2 (压测)          | 20%  | 有完整的评测数据和图表分析 |
| 任务 3-5 (源码分析)    | 35%  | 正确回答所有问题，分析深入 |
| 文档质量               | 15%  | 代码注释清晰、报告结构完整 |
| 进阶任务 (任务 6-8)    | 15%  | 完成至少一项进阶任务       |

---

## 参考资料

- **nano-vllm 仓库**: https://github.com/ForceInjection/nano-vllm (本地路径: `~/Project/study/nano-vllm/`)
- **nano-vllm 8 课在线课程**: https://forceinjection.github.io/nano-vllm/
  - 01: LLM generate 和 step
  - 02: Sequence 生命周期
  - 03: Scheduler 队列与 Preemption
  - 04: Block Manager 与 Prefix Cache
  - 05: Prefill 批处理与上下文准备
  - 06: Decode 与 Block Tables
  - 07: Attention KV Cache 与分支 (PagedAttention 实现)
  - 08: 优化全景图 (CUDA Graph, Tensor Parallel, Prefix Caching)
- AI-fundamentals: `09_inference_system/vllm/` 全套 vLLM 分析
- vLLM Paper: "Efficient Memory Management for Large Language Model Serving with PagedAttention" (SOSP 2023)
