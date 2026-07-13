# 模块 8：课程总结与 AI Infra 前沿展望

> 90 分钟 &nbsp;|&nbsp; 40 页 PPT &nbsp;|&nbsp; 课程大作业 (2026 统一版 + 完整三方向版) &nbsp;|&nbsp; 总结+展望型

## 本章内容

| 部分               | 时长   | PPT 页 | 重点内容                                                                                                     |
| ------------------ | ------ | ------ | ------------------------------------------------------------------------------------------------------------ |
| 课程回顾串讲       | 30 min | 3–17   | 7+1 模块全景 / 底层基础 (模块 1-3) / 中层调度 (模块 4) / 上层推理 (模块 5-7) / 关键公式 20 条 / 动手实验回顾 |
| 一条请求的旅程     | 15 min | 18–22  | 端到端 8 站动画 / 技术栈 5 层抽象 / 互动问答 7 题 / 知识地图填空                                             |
| AI Infra 前沿      | 20 min | 23–30  | 模型+硬件演进 / PD 分离标准化 / KV Cache 一等公民 / 云原生 AI 演进 / AI Native 软件工程                      |
| Agent Infra + 职业 | 25 min | 31–45  | Agent Infra Stack 4 层 / MCP 协议 / Sandbox / Kagent 案例 / 职业 4 路径 / 课程总结寄语                       |

## 与前 7 讲的关系

- 前半部分 (回顾): 将模块 1-7 串联为一条 "请求→GPU" 完整链路
- 后半部分 (展望): 从课程知识延伸到工业界趋势和职业路径
- 大作业: 让学生综合运用多模块知识，完成一个完整的 Infra 项目

## 课程大作业

**2026 年统一版**：所有学生完成同一方向 — [GPU 资源拦截：从显存到算力](course-project-2026.md) ([HTML 版](course-project-2026.html))。基于 LD_PRELOAD 拦截 CUDA Runtime API，实现显存配额 + 算力令牌桶限速。覆盖模块 3。

**完整三方向版** ([`course-project.md`](course-project.md)) 保留作为参考，方向为：

| 方向                 | 难度 | 覆盖模块 | 核心体验                                   |
| -------------------- | ---- | -------- | ------------------------------------------ |
| A: GPU 资源拦截      | ★★★☆ | 3        | LD_PRELOAD CUDA hook — 显存配额 + 算力限速 |
| B: K8s GPU 调度      | ★★★☆ | 1, 4, 7  | GPU 调度全链路追踪 + 网关 + HPA            |
| C: KV Cache 显存管理 | ★★★★ | 2, 5, 6  | PagedAttention 碎片模拟 + Prefix Cache LRU |

骨架代码在 `code/` 目录下，详见 [`code/README.md`](code/README.md)。

---

## 参考来源

- [AI-fundamentals/08_agentic_system/agent_infra](https://github.com/ForceInjection/AI-fundamentals/tree/main/08_agentic_system/agent_infra) — Agent Infra 四层技术栈、MCP 协议、Sandbox 沙箱
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals)
- [HAMi-core](https://github.com/Project-HAMi/HAMi-core) — GPU 虚拟化参考实现
