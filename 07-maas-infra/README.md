# 模块 7：从推理引擎到服务平台

> 90 分钟 &nbsp;|&nbsp; 45 页 PPT &nbsp;|&nbsp; 1 个 Flask 网关 (Random + Consistent Hash) + 1 个 Mock 后端 + 6 个交互式 HTML

## 可视化 HTML

| 可视化 | 用途 | 教学场景 |
|--------|------|----------|
| [基础网关流水线](visuals/gateway-pipeline.html) | 四段式流水线: 认证 → 令牌桶限流 → 加权路由 → 转发 | 快速理解网关核心流程：发送请求、触发限流 (429)、模拟宕机 (503) |
| [AI 网关推理流水线](visuals/ai-gateway-pipeline.html) | Semantic Router 模型路由 + Cache-Aware LB + 令牌桶 + KV Cache 亲和性 | 深入讲解 vLLM Router：切换 LB 策略对比、请求类型→模型路由、Cache 热度驱动 Worker 选择 |
| [Consistent Hash](visuals/consistent-hash.html) | Hash Ring + 虚拟节点 + 节点增删时的 key 重映射 | 辅助可视化 (简化版)，配合下方文字说明使用 |
| [Semantic Router](visuals/semantic-router.html) | Shannon 两层模型: 信号提取 (信息论) → 布尔决策 (开关电路) | 讲解 Semantic Router 时打开：输入查询，观察信号提取和模型选择决策 |
| [OpenAI API 格式](visuals/openai-api-format.html) | 请求/响应 JSON 结构 + 流式 SSE 格式 + 网关字段映射 | 讲解 OpenAI 兼容协议时打开：逐字段标注用途，理解网关如何利用每个字段 |
| [PD 分离](visuals/pd-separation.html) | Prefill→H100 池, Decode→H200 池, KV Cache 跨池传输 | 讲解 PD 分离路由时打开：对比 compute-bound vs memory-bound, H100 vs H200 硬件匹配 |

**AI 网关交互方式**: 下拉选择请求类型 («写代码»/«翻译»/«聊天») → Semantic Router 自动选模型；切换 LB 策略 (Random / Consistent Hash / Cache-Aware) 观察 Worker 选择变化；Worker Cache 热度动态变化 (命中→升温，未命中→降温)。

### Consistent Hash 在 AI 网关中的作用

**是什么？**

Consistent Hash 是一种特殊的哈希算法，它将 Worker 节点和请求 Key 都映射到同一个 Hash Ring（0 → 2³²-1 的环）上。请求到来时，从 Key 的 hash 位置**顺时针**找到第一个 Worker，由该 Worker 处理请求。

**解决什么问题？**

在 AI 推理网关中，同一个用户的连续请求如果每次打到不同的 Worker，KV Cache 无法复用——每次都要重新 Prefill，TTFT 暴增。

Consistent Hash 保证了：**同一个 Key → 永远路由到同一个 Worker**。Key 可以是 `Session-ID` 或 `API-Key`。用户 Alice 的 10 轮对话全部打到 Worker #2 → Worker #2 的 KV Cache 里始终有 Alice 的对话历史 → 第 2 到第 10 轮的 Prefill 被跳过 → TTFT 降低 80-95%。

**比简单取模 hash%N 好在哪里？**

当 Worker 数量变化时（扩容或宕机），简单取模 `hash(key) % N` 会导致**几乎所有 key 的映射都改变**——4→5 个 Worker 时 80% 的 key 重新映射，所有 KV Cache 作废。

Consistent Hash 下只有 **~1/N 的 key 需要重新映射**（4→5 时只有 ~20%），因为每个 Worker 只影响环上相邻一段。大部分 key 的 KV Cache 仍然有效。

**vLLM Router 中的实现**

vLLM Router 的 Consistent Hash 基于 `X-Session-ID` header：相同 Session → 相同 Worker → Prefix Cache 持续命中。配合 Cache-Aware LB（查询 Worker 的实际 Cache 命中率），可以进一步提升到 85% 命中率。

---

## 教学流程

| 部分             | 时长   | PPT 页 | 重点内容                                                                                                                  | 动手                                |
| ---------------- | ------ | ------ | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| 架构总览         | 15 min | 3–9    | 四阶段演进、四层架构、vLLM Router Rust/PyO3 剖析、K8s 原生集成、HTTP+gRPC+OpenAI 三协议                                   | —                                   |
| AI 网关深入      | 30 min | 10–20  | 6 种 LB 策略、Consistent Hash、Cache-Aware、Semantic Router (NeurIPS 2025)、Token Bucket 三级限流、RBAC 认证、PD 分离路由 | —                                   |
| 部署实战         | 25 min | 21–33  | DeepSeek V3 on 32×H20: EP/TP/PP 权衡、显存规划、弹性伸缩 (HPA+KPA+Spot)、冷启动、金丝雀发布、LoRA 多租户                  | —                                   |
| 可观测性与高可用 | 20 min | 34–45  | TTFT/TPOT/ITL 指标体系、DCGM GPU 指标、多副本反亲和+跨Zone、熔断降级、FinOps 成本治理、模块 4→7 技术链路                  | 第 42 页: Flask AI 网关 (15–20 min) |

## 课程简介

本模块是推理技术栈的"最后一公里"——将模块 4/5/6 学到的所有技术打包成一个可规模化、可运维的服务平台。

**核心问题**: 模块 5 你学会了 `vllm serve` 一行命令启动推理服务。但如果要服务 1000 个用户、10 种模型、SLA 99.9%——还差什么？

**四个答案**:

1. **AI 网关**: 路由/限流/认证 — 请求该发给谁？配额够不够？你是谁？
2. **部署策略**: EP/TP/PP — DeepSeek V3 671B 怎么在 32×H20 上跑满？
3. **弹性伸缩**: HPA + KPA + Spot — 早高峰自动扩容，凌晨自动缩
4. **可观测性 + 高可用**: Prometheus + 熔断 + 多副本 — 知道服务在健康运行，挂了自动恢复

**与前序模块的关系**:

- 模块 4 (K8s GPU 调度): GPU 怎么分配给容器？→ 本模块的调度层基础
- 模块 5 (vLLM 推理引擎): GPU 怎么用高效？→ 本模块的引擎层基础
- 模块 6 (KV Cache 优化): KV Cache 怎么省？→ 本模块的显存规划直接应用

**四个模块串成一条线**: 模块 4 (谁用GPU) → 模块 5+6 (怎么用高效+怎么省) → 模块 7 (怎么打包成服务)

## 实验环境

| 软件        | 版本    | 用途                                    |
| ----------- | ------- | --------------------------------------- |
| Python      | ≥ 3.10  | 网关实现                                |
| Flask       | latest  | Web 框架 (`pip install flask requests`) |
| vLLM        | ≥ 0.6.0 | 推理后端 (需 GPU)                       |
| vLLM Router | latest  | 生产级网关 (选做)                       |

## 动手实验

课堂实现 Flask AI 网关 (~140 行)，体验核心机制:

- Token Bucket 限流 (5 req/s, burst 10)
- 加权随机路由 + 健康检查
- 故障转移 (后端挂掉自动切换)

详见 [`hands-on-exercise.md`](hands-on-exercise.md)，代码 [`code/ai_gateway.py`](code/ai_gateway.py)。

## 课后作业

设计企业级推理服务平台 (10 万 QPS, 10 种模型, SLA 99.9%) + 增强网关 (API Key 管理、按模型路由、Prometheus Metrics)。详见 [`homework.md`](homework.md)。

## 参考来源

- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/vllm/routing/router.md) — vLLM Router 架构分析
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/vllm/routing/semantic_router_deep_dive.md) — Semantic Router 深度剖析
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/deployment/deepseek_v3_moe_vllm_h20_deployment.md) — DeepSeek V3 H20 部署方案
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/reference_design/06-推理服务架构设计.md) — 推理服务架构设计
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/reference_design/05-性能评估指标体系.md) — 性能指标体系
- vLLM Router / Semantic Router Paper (NeurIPS 2025 MLForSys Workshop)
