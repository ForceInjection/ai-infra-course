# 模块 4：Kubernetes 入门与 GPU 工作负载调度

> 120 分钟 &nbsp;|&nbsp; 52 页 PPT &nbsp;|&nbsp; 3 个 YAML 文件 &nbsp;|&nbsp; 2 个可视化 HTML

从单机 GPU 操作走向集群级 GPU 编排。核心问题：「你有 100 台 GPU 服务器，怎么管理 1000 个 GPU 应用？」— K8s 入门 → Device Plugin → DRA → GPU 调度实战。

---

## 本章内容

| 部分                   | 时长   | PPT 页 | 重点内容                                          | 动手                                   |
| ---------------------- | ------ | ------ | ------------------------------------------------- | -------------------------------------- |
| K8s 入门               | 35 min | 3–18   | Pod/Deployment/Service、声明式、控制循环          | 第 16 页: 部署 Nginx                   |
| Device Plugin 机制     | 25 min | 19–28  | ListAndWatch/Allocate、NVIDIA DP 时序、CDI 演进   | —                                      |
| DRA — 动态资源分配     | 30 min | 29–40  | ResourceClaim/ResourceClass、拓扑感知、Kueue 队列 | 第 47 页: DRA Claim 概念演示           |
| GPU 调度策略与动手实践 | 30 min | 41–52  | Filter/Score/Bind、GPU 拓扑调度、全链路回顾       | 第 45 页: GPU Pod + 第 46 页: 资源争抢 |

---

## 可视化 HTML

| 文件                                                          | 用途                                                         | 教学场景                      |
| ------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------- |
| [K8s GPU 调度全链路可视化](visuals/k8s-gpu-flow.html)         | K8s GPU 调度全链路 — 7 步可交互动画                          | 全链路回顾时打开，逐步骤讲解  |
| [Device Plugin 交互时序](visuals/device-plugin-sequence.html) | Device Plugin gRPC 接口 — Register / ListAndWatch / Allocate | 讲解 Device Plugin 机制时打开 |

---

## 配套代码

| 文件                                            | 内容                                            | 对应 PPT    |
| ----------------------------------------------- | ----------------------------------------------- | ----------- |
| [`01_nginx_demo.yaml`](code/01_nginx_demo.yaml) | Nginx Deployment + ConfigMap + NodePort Service | 第 16 页    |
| [`02_gpu_pod.yaml`](code/02_gpu_pod.yaml)       | GPU Pod — nvidia-smi 测试                       | 第 45 页    |
| [`03_gpu_deploy.yaml`](code/03_gpu_deploy.yaml) | GPU Deployment — 生产级工作负载                 | 第 45-46 页 |

详见 [`code/README.md`](code/README.md)。

---

## 课堂练习

详见 [`hands-on-exercise.md`](hands-on-exercise.md)。

---

## 课后作业

详见 [`homework.md`](homework.md)。实验环境搭建见 [`lab-environment.md`](lab-environment.md)。

---

## 参考资料

- [Kubernetes 官方文档](https://kubernetes.io/docs/concepts/) — Pod/Deployment/Service 等核心概念
- [NVIDIA k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin) — NVIDIA Device Plugin 源码
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) — GPU 容器注入机制
- [Kueue](https://kueue.sigs.k8s.io/) — 作业级队列管理
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) — K8s 系列分析文章
