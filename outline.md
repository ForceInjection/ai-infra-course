# 云原生 AI 基础设施：原理与实践

## 1. 课程介绍

《云原生 AI 基础设施：原理与实践》面向高年级本科生，系统介绍云原生人工智能基础设施（AI Infra）的核心技术体系。课程从 Linux 基础与底层容器技术（Namespace、Cgroup）起步，依次覆盖 GPU 硬件架构与 CUDA 编程、GPU 虚拟化与标准化容器化实践、从 Device Plugin 到 DRA 的 Kubernetes 调度演进，以及以 vLLM 为代表的高吞吐推理框架和 KV Cache 加速优化策略。最后，课程将延展至 MaaS（Model as a Service）场景下的 AI 网关等关键组件，并探讨 AI Infra 与 Agent Infra 融合的前沿趋势。通过原理讲解与动手实践相结合的方式，帮助学生深入理解 AI Infra 各层次的设计思想与技术原理，为后续在该领域的深入探索和工程实践奠定坚实基础。

内容地址：

- 本地：/Users/wangtianqing/Project/wechat/AI-fundamentals/
- Github：https://github.com/ForceInjection/AI-fundamentals

## 2. 课程大纲

本课程的教学内容按照从底层硬件到上层框架的逻辑链路展开，分为八个核心模块。各模块紧密结合云原生生态与大模型推理场景，通过理论解析与上机实验，逐步构建完整的云原生人工智能基础设施知识体系。

### 1. Linux 基础与容器技术入门

掌握 Linux 命令行、文件系统与进程管理等核心操作，深入理解 Namespace 与 Cgroup 等容器底层隔离与限制原理，学习 Docker 镜像拉取、容器启动与管理等基础操作，完成本地容器化开发环境的搭建。

### 2. GPU 硬件架构与 CUDA 编程入门

认识 GPU 的并行计算模型、显存层次与线程组织方式，动手安装 NVIDIA 驱动与 CUDA 工具链，编写并运行简单的 CUDA 程序完成矩阵运算。

### 3. GPU 虚拟化与容器化实践

介绍 GPU 虚拟化的多种形态，并重点剖析 HAMi 开源项目的 CUDA 拦截机制。在 GPU 容器化实践中，掌握 runtime 配置及 --gpus 等参数的传入方法，学习 Docker 镜像构建与优化技巧，将大语言模型服务打包成标准化容器镜像，实现跨环境的一键运行。

### 4. Kubernetes 入门与 GPU 工作负载调度

掌握 Pod、Deployment、Service 等核心对象，学习从 Device Plugin 到 DRA (Dynamic Resource Allocation) 的资源管理演进，深入探讨集群中的 GPU 调度策略。动手在集群中配置 GPU 资源并调度已容器化的模型应用，完成声明式部署。

### 5. 大模型推理框架入门：以 vLLM 为例

解析 vLLM 的系统架构，深入介绍 PagedAttention、连续批处理 (Continuous Batching) 以及 Prefix Caching (前缀缓存) 等核心技术。动手使用 vLLM 部署高吞吐大模型推理服务，并通过 API 在 Kubernetes 环境中实际调用。

### 6. 大模型推理加速实践：KV Cache 原理与优化

承接 vLLM 的架构解析，深入剖析 Transformer 自回归推理中的 KV Cache 机制。详细推导其显存占用的计算公式，探讨 KV Cache Offloading 卸载技术，并引入 TurboQuant 等量化压缩策略，结合 LMCache 与 MoonCake 示例，实验对比不同优化方案对推理效率的影响。

### 7. 云原生 AI 推理基础设施进阶：构建 Model as a Service

以实现 Model as a Service (MaaS) 为目标，系统讲解除推理引擎外的核心基础设施组件。以 llm-d 与 AIBrix 为例，介绍 AI 网关在路由分发、负载均衡与认证鉴权中的基本功能，并拓展介绍模型路由策略、弹性伸缩机制以及可观测性建设等多个关键组件，动手搭建企业级的高可用推理接入层。

### 8. 课程总结与 AI Infra 前沿展望

回顾课程关键技术链路，系统总结云原生人工智能基础设施的核心架构与实践经验。探讨 AI Infra 的未来发展趋势，重点展望其与 Agent Infra（智能体基础设施）的深度结合与协同演进方向。
