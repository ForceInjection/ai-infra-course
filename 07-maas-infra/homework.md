# 模块 7：云原生 AI 推理基础设施进阶：构建 MaaS — 课后练习

## 题目：设计一个企业级 MaaS 架构方案

### 目标

综合运用前 7 个模块的知识，设计一个支持 10 万 QPS 的企业级 MaaS 架构方案。

### 截止时间

下次课前 (一周)

---

## 基础任务 (必做)

### 任务 1: 设计 MaaS 架构

假设你需要为一个 AI 创业公司设计推理服务平台，需求如下：

| 维度 | 要求 |
|------|------|
| 目标 QPS | 100,000 (峰值) |
| 模型数量 | 10 个模型 (3 个小模型 0.5-7B, 5 个中模型 13-34B, 2 个大模型 72B+) |
| 可用性 | 99.9% |
| 平均延迟 | TTFT P95 < 500ms |
| 多租户 | 支持 100 个企业客户，每个有独立配额 |
| 安全 | API Key 认证 + 请求日志审计 |
| 成本 | GPU 成本控制在 100 万/月以内 |

完成以下设计：

1. **架构图**: 画出从用户请求到推理引擎的完整架构图，标注每个组件
2. **组件设计**:
   - AI 网关: 选型 (自研/开源/商业)，路由策略，限流方案
   - 推理引擎: vLLM vs SGLang vs TensorRT-LLM 的选型理由
   - 模型部署: 每个模型几副本、用什么 GPU
   - KV Cache: Prefix Caching 策略、是否使用 LMCache
3. **容量规划**:
   - 计算每个模型的 GPU 需求 (假设每个请求平均 500 input + 200 output tokens)
   - GPU 总数和型号
   - 成本估算
4. **高可用设计**: 多副本、跨 Zone、熔断降级策略

### 任务 2: 增强课堂网关

在课堂实现的 AI 网关基础上，添加以下功能：

1. **API Key 管理**: 支持创建/删除/查询 API Key
2. **按模型名路由**: 根据请求的 `model` 字段路由到不同后端
3. **Prometheus Metrics**: 暴露以下指标:
   - `requests_total{model, status}`
   - `request_duration_seconds{model, quantile}`
   - `tokens_total{model, type}`  (type = input/output)
4. **请求日志**: JSON 格式日志，包含 timestamp, api_key, model, latency, tokens, status

---

## 进阶任务 (选做)

### 任务 3: 部署 llm-d 体验

在 K8s 集群中部署 llm-d，体验真正的云原生推理调度：

```bash
git clone https://github.com/ForceInjection/llm-d
# 按照 README 部署
```

对比自研网关 vs llm-d 的功能差异。

### 任务 4: 成本优化分析

使用 AI-fundamentals 中的成本分析材料，完成：
- `09_inference_system/cost_analysis/llm_api_pricing_analysis.md` 的定价模型研究
- 对比自建 MaaS vs 调用商业 API (如 OpenAI/DeepSeek API) 的成本边界

---

## 提交要求

1. 提交 MaaS 架构设计文档 (≤ 5 页)，包含：
   - 架构图 (建议用 draw.io 或 Excalidraw)
   - 组件选型和理由
   - 容量规划计算过程
   - 高可用设计方案
2. 提交增强版网关代码
3. (选做) llm-d 部署体验报告或成本分析报告

---

## 评分标准

| 维度 | 权重 | 要求 |
|------|------|------|
| 架构设计 | 40% | 完整的架构图 + 组件选型有理有据 |
| 网关增强 | 30% | 实现所有要求的功能 |
| 容量/成本分析 | 15% | 计算正确、考虑全面 |
| 进阶任务 | 15% | 完成至少一项进阶任务 |

---

## 参考资料

- AI-fundamentals: `04_cloud_native_ai_platform/k8s/05_llm_d_intro.md`
- AI-fundamentals: `09_inference_system/reference_design/` 全套参考设计文档
- AI-fundamentals: `09_inference_system/cost_analysis/`
- AI-fundamentals: `09_inference_system/vllm/routing/`
