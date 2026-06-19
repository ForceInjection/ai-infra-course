# 模块 8：课程总结与 AI Infra 前沿展望 — 课后练习

## 题目：AI Infra 技术博客 + 课程学习总结

### 目标

通过撰写技术博客，巩固整个课程的学习成果，并表达对 AI Infra 未来发展方向的独立思考。

### 截止时间

课程结束后一周

---

## 任务 1: 技术博客 (必做)

写一篇 2000-3000 字的技术博客，主题二选一：

### 选项 A: AI Infra 技术栈总结

以本课程为基础，梳理从底层硬件到上层推理平台的完整技术栈。要求：

1. **画出你的 AI Infra 知识地图**: 用 Mermaid/Excalidraw/Draw.io 画出你理解的 AI Infra 全景图
2. **选择 2-3 个技术点深入分析**: 不要面面俱到，选你最有感触的技术点深入写
3. **结合实验经验**: 课程中你遇到的最大困难是什么？如何解决的？
4. **给出学习建议**: 如果明年有学弟学妹选这门课，你会给他们什么建议？

### 选项 B: AI Infra 前沿趋势分析

选择以下任一前沿方向，写一篇深入的技术分析：

1. **Agent Infra 的崛起**: Agent 对基础设施提出了哪些新需求？现有的 AI Infra 能否满足？
2. **PD 分离架构**: Prefill-Decode 分离是否会成为推理系统的标配？技术挑战在哪里？
3. **KV Cache 的未来**: KV Cache 会从「缓存」演化为「存储基础设施」吗？分析 NVIDIA ICMS / LMCache / MoonCake 等方案
4. **开源推理引擎对比**: vLLM vs SGLang vs TensorRT-LLM，各自的设计哲学和适用场景

要求：
- 有技术深度 (源码分析/架构图/数据对比)
- 有个人观点 (不是简单翻译文档)
- 标注参考资料

---

## 任务 2: 课程反馈 (必做)

回答以下问题 (简短即可，不计入字数要求)：
1. 课程中哪个模块对你帮助最大？为什么？
2. 哪个模块你觉得最难？如何改进？
3. 你希望增加/删除什么内容？
4. 动手实验的难度合适吗？
5. 对课程的整体评价 (1-5 分)

---

## 提交要求

1. 技术博客 (Markdown 格式，可发布到个人博客/GitHub/知乎等)
2. 课程反馈
3. 打包提交，命名为 `学号_姓名_课程总结.zip`

---

## 评分标准

| 维度 | 权重 | 要求 |
|------|------|------|
| 技术深度 | 40% | 深入分析，有源码/数据/架构图支撑 |
| 个人见解 | 25% | 不是简单总结，有独立的思考和分析 |
| 表达与结构 | 20% | 文章逻辑清晰、可读性好 |
| 课程反馈 | 15% | 认真填写，提出建设性意见 |

---

## 参考资料

- AI-fundamentals 完整仓库: https://github.com/ForceInjection/AI-fundamentals
- 课程设计材料: 同目录下所有模块的 `syllabus.md`
- 推荐阅读:
  - PagedAttention Paper (SOSP 2023)
  - Mooncake Paper
  - FlashAttention Paper
  - vLLM 源码: https://github.com/vllm-project/vllm
  - LMCache 源码: https://github.com/LMCache/LMCache
  - nano-vllm: https://github.com/ForceInjection/nano-vllm
  - Agent Infra: `08_agentic_system/agent_infra/` 全部文档
