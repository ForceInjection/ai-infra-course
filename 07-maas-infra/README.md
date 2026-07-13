# 模块 7：从推理引擎到服务平台

> 90 分钟 &nbsp;|&nbsp; 45 页 PPT &nbsp;|&nbsp; 1 个 Flask 网关 (Random + Consistent Hash) + 1 个 Mock 后端 + 6 个交互式 HTML

本模块是推理技术栈的「最后一公里」— 将模块 4/5/6 学到的所有技术打包成一个可规模化、可运维的服务平台。

核心问题：模块 5 你学会了 `vllm serve` 一行命令启动推理服务。但如果要服务 1000 个用户、10 种模型、SLA 99.9% — 还差什么？

---

## 本章内容

| 部分 | 时长 | PPT 页 | 重点内容 | 动手 |
|------|------|--------|----------|------|
| 架构总览 | 15 min | 3–9 | 四阶段演进、四层架构、vLLM Router Rust/PyO3 剖析、K8s 原生集成 | — |
| AI 网关深入 | 30 min | 10–20 | 6 种 LB 策略、Consistent Hash、Cache-Aware、Semantic Router、Token Bucket 三级限流、RBAC 认证、PD 分离路由 | — |
| 部署实战 | 25 min | 21–33 | DeepSeek V3 on 32×H20: EP/TP/PP 权衡、显存规划、弹性伸缩 (HPA+KPA+Spot)、冷启动、金丝雀发布、LoRA 多租户 | — |
| 可观测性与高可用 | 20 min | 34–45 | TTFT/TPOT/ITL 指标体系、DCGM GPU 指标、多副本反亲和+跨Zone、熔断降级、FinOps 成本治理 | 第 42 页: Flask AI 网关 |

---

## 可视化 HTML

| 可视化 | 用途 | 教学场景 |
|--------|------|----------|
| [基础网关流水线](visuals/gateway-pipeline.html) | 四段式流水线: 认证 → 令牌桶限流 → 加权路由 → 转发 | 快速理解网关核心流程：发送请求、触发限流 (429)、模拟宕机 (503) |
| [AI 网关推理流水线](visuals/ai-gateway-pipeline.html) | Semantic Router 模型路由 + Cache-Aware LB + 令牌桶 + KV Cache 亲和性 | 深入讲解 vLLM Router：切换 LB 策略对比、Cache 热度驱动 Worker 选择 |
| [Consistent Hash](visuals/consistent-hash.html) | Hash Ring + 虚拟节点交互演示 | 辅助可视化，配合下方文字说明使用 |
| [Semantic Router](visuals/semantic-router.html) | Shannon 两层模型: 信号提取 → 布尔决策 | 讲解 Semantic Router 时打开：输入查询，观察信号提取和模型选择 |
| [OpenAI API 格式](visuals/openai-api-format.html) | 请求/响应 JSON 结构 + 流式 SSE 格式 + 网关字段映射 | 讲解 OpenAI 兼容协议时打开：逐字段标注用途 |
| [PD 分离](visuals/pd-separation.html) | Prefill→H100 池, Decode→H200 池, KV Cache 跨池传输 | 讲解 PD 分离路由时打开：对比 compute-bound vs memory-bound |

---

## 配套代码

| 文件 | 内容 | 对应 PPT |
|------|------|----------|
| [`ai_gateway.py`](code/ai_gateway.py) | Flask AI 网关 — Random/Consistent Hash LB + Token Bucket + 健康检查 | 第 42 页 |
| [`mock_vllm.py`](code/mock_vllm.py) | vLLM Mock 后端 — 无需 GPU，本地测试网关用 | — |
| [`demo.sh`](code/demo.sh) | 一键启动/停止 | — |

详见 [`code/README.md`](code/README.md)。

---

## 课堂练习

详见 [`hands-on-exercise.md`](hands-on-exercise.md)。

---

## 课后作业

详见 [`homework.md`](homework.md)。实验环境搭建见 [`lab-environment.md`](lab-environment.md)。

---

## 参考资料

- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/vllm/routing/router.md) — vLLM Router 架构分析
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/vllm/routing/semantic_router_deep_dive.md) — Semantic Router 深度剖析
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/09_inference_system/deployment/deepseek_v3_moe_vllm_h20_deployment.md) — DeepSeek V3 H20 部署方案
- vLLM Router / Semantic Router Paper (NeurIPS 2025 MLForSys Workshop)
