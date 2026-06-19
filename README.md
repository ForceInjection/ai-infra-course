# 云原生 AI 基础设施：原理与实践 — 课程设计

> **面向对象**: 高年级本科生
> **课时安排**: 8 次课 × 90 分钟 = 12 学时
> **课程材料来源**: [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals)

---

## 课程简介

本课程系统介绍云原生人工智能基础设施（AI Infra）的核心技术体系。从 Linux 基础与底层容器技术起步，依次覆盖 GPU 硬件架构与 CUDA 编程、GPU 虚拟化与标准化容器化实践、从 Device Plugin 到 DRA 的 Kubernetes 调度演进，以及以 vLLM 为代表的高吞吐推理框架和 KV Cache 加速优化策略。最后延展至 MaaS 场景下的 AI 网关等关键组件，并探讨 AI Infra 与 Agent Infra 融合的前沿趋势。

## 课程特色

- **原理 + 实践**: 每节课包含理论讲解和动手实验
- **从底层到上层**: 按硬件→内核→容器→编排→推理框架的逻辑链路展开
- **课后巩固**: 每节课配有课后练习，持续深化理解

## 课程目录

| 模块 | 主题                                    | 核心内容                            |
| ---- | --------------------------------------- | ----------------------------------- |
| 1    | Linux 基础与容器技术入门                | Namespace/Cgroup、Docker            |
| 2    | GPU 硬件架构与 CUDA 编程入门            | GPU 架构、CUDA Kernel               |
| 3    | GPU 虚拟化与容器化实践                  | HAMi、NVIDIA Container Toolkit      |
| 4    | Kubernetes 入门与 GPU 工作负载调度      | Device Plugin、DRA、Kueue           |
| 5    | 大模型推理框架入门：以 vLLM 为例        | PagedAttention、Continuous Batching |
| 6    | 大模型推理加速实践：KV Cache 原理与优化 | KV Cache、LMCache、量化压缩         |
| 7    | 云原生 AI 推理基础设施进阶：构建 MaaS   | AI 网关、路由、弹性伸缩             |
| 8    | 课程总结与 AI Infra 前沿展望            | Agent Infra、AI Native              |

## 每节课包含

| 文件                   | 说明                                      |
| ---------------------- | ----------------------------------------- |
| `syllabus.md`          | 教学大纲：知识点、时间分配、教学目标      |
| `ppt-outline.md`       | PPT 大纲：每页内容、排版建议              |
| `lab-environment.md`   | 实验环境说明：硬件/软件要求、环境搭建步骤 |
| `hands-on-exercise.md` | 课堂动手题：题目、步骤、讲解要点          |
| `homework.md`          | 课后练习：题目、要求、提交方式            |

## 材料来源

课程内容参考 [AI-fundamentals 仓库](https://github.com/ForceInjection/AI-fundamentals)，本地路径：`/Users/wangtianqing/Project/wechat/AI-fundamentals/`。

各模块对应的参考材料路径见各模块 `syllabus.md` 中的「参考材料」部分。
