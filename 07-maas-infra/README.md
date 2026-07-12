# 模块 7：从推理引擎到服务平台

> 90 分钟 &nbsp;|&nbsp; 45 页 PPT &nbsp;|&nbsp; 1 个 Flask 网关 + 1 个 Mock 后端 + 2 个交互式 HTML

## 目录结构

```text
07-maas-infra/
├── README.md                    # 本文件
├── syllabus.md                  # 教学大纲 (90 分钟时间分配)
├── ppt-outline.md               # PPT 大纲 (45 页)
├── hands-on-exercise.md         # 课堂动手题
├── homework.md                  # 课后练习
├── lab-environment.md           # 实验环境搭建说明
├── code/                        # 配套代码
│   ├── README.md                #   使用说明 + 测试步骤
│   ├── ai_gateway.py            #   Flask 简易 AI 网关 (PPT 第 42 页)
│   ├── mock_vllm.py             #   vLLM Mock 后端 (无需 GPU，本地测试用)
│   └── demo.sh                  #   一键启动/停止 (bash demo.sh start|stop)
└── visuals/                        # 可视化 HTML (2 个)
    ├── gateway-pipeline.html       #   基础网关流水线 — 认证·限流·路由·转发
    └── ai-gateway-pipeline.html    #   AI 网关流水线 — Semantic Router · Cache-Aware LB
```

## 可视化 HTML

| 可视化 | 用途 | 教学场景 |
|--------|------|----------|
| [基础网关流水线](visuals/gateway-pipeline.html) | 四段式流水线: 认证 → 令牌桶限流 → 加权路由 → 转发 | 快速理解网关核心流程：发送请求、触发限流 (429)、模拟宕机 (503) |
| [AI 网关推理流水线](visuals/ai-gateway-pipeline.html) | Semantic Router 模型路由 + Cache-Aware LB + 令牌桶 + KV Cache 亲和性 | 深入讲解 vLLM Router：切换 LB 策略对比、请求类型→模型路由、Cache 热度驱动 Worker 选择 |

**AI 网关交互方式**: 下拉选择请求类型 («写代码»/«翻译»/«聊天») → Semantic Router 自动选模型；切换 LB 策略 (Random / Consistent Hash / Cache-Aware) 观察 Worker 选择变化；Worker Cache 热度动态变化 (命中→升温，未命中→降温)。

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
