# 模块 8：课程总结与 AI Infra 前沿展望

> 90 分钟 &nbsp;|&nbsp; 40 页 PPT &nbsp;|&nbsp; 3 个大作业方向骨架代码 &nbsp;|&nbsp; 总结+展望型

## 目录结构

```text
08-summary-outlook/
├── README.md                    # 本文件
├── syllabus.md                  # 教学大纲 (90 分钟时间分配)
├── ppt-outline.md               # PPT 大纲 (40 页)
├── course-project.md            # 课程大作业 (3 方向选 1)
└── code/                        # 大作业骨架代码 + 报告模板
    ├── README.md
    ├── REPORT_TEMPLATE.md       #   技术报告模板
    ├── gpu-container-hook/      #   方向 A: 容器+拦截 (3 files)
    ├── k8s-gateway/             #   方向 B: K8s 调度 (6 files)
    └── kvcache-simulator/       #   方向 C: KV Cache (4 files)
```

## 教学流程

| 部分 | 时长 | PPT 页 | 重点内容 |
|------|------|--------|---------|
| 课程回顾串讲 | 30 min | 3–17 | 7+1 模块全景 / 底层基础 (模块 1-3) / 中层调度 (模块 4) / 上层推理 (模块 5-7) / 关键公式 20 条 / 动手实验回顾 |
| 一条请求的旅程 | 15 min | 18–22 | 端到端 8 站动画 / 技术栈 5 层抽象 / 互动问答 7 题 / 知识地图填空 |
| AI Infra 前沿 | 20 min | 23–30 | 模型+硬件演进 / PD 分离标准化 / KV Cache 一等公民 / 云原生 AI 演进 / AI Native 软件工程 |
| Agent Infra + 职业 | 25 min | 31–45 | Agent Infra Stack 4 层 / MCP 协议 / Sandbox / Kagent 案例 / 职业 4 路径 / 课程总结寄语 |

## 课程大作业

三个方向任选，聚焦 **AI 基础设施** (非 AI 应用)，覆盖课程核心模块:

| 方向 | 难度 | 覆盖模块 | 核心体验 |
|------|------|---------|---------|
| A: 容器化 GPU 推理 | ★★★☆ | 1, 3, 5 | LD_PRELOAD CUDA hook + Docker + nano-vllm |
| B: K8s GPU 调度 | ★★★☆ | 1, 4, 7 | GPU 调度全链路追踪 + 网关 + HPA |
| C: KV Cache 显存管理 | ★★★★ | 2, 5, 6 | PagedAttention 碎片模拟 + Prefix Cache LRU |

每个方向提供可运行骨架代码（搜索 `TODO` 完成），零硬件依赖的方向 C 保证所有学生都能完成。

详见 `course-project.md` 和 `code/README.md`。

## 与前 7 讲的关系

- 前半部分 (回顾): 将模块 1-7 串联为一条 "请求→GPU" 完整链路
- 后半部分 (展望): 从课程知识延伸到工业界趋势和职业路径
- 大作业: 让学生综合运用多模块知识，完成一个完整的 Infra 项目

## 参考来源

- 本课程模块 1-7 的全部 syllabus / ppt-outline / code
- AI-fundamentals: `08_agentic_system/agent_infra/`, `11_ai_native_everything/`
- AI-fundamentals: `01_hardware_architecture/superchips/nvidia_gb300.md`
