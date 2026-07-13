# 模块 1：Linux 基础与容器技术入门

> 90 分钟 &nbsp;|&nbsp; 42 页 PPT &nbsp;|&nbsp; 4 个 Bash 脚本 &nbsp;|&nbsp; 5 个可视化 HTML

---

## 本章内容

| 阶段                  | 时长   | PPT 页 | 动手                                        |
| --------------------- | ------ | ------ | ------------------------------------------- |
| Linux 命令行基础      | 20 min | 3–11   | 第 9 页：基础实操                           |
| Namespace 与 Cgroup   | 23 min | 12–20  | 第 19 页：NS 隔离 / 第 20 页：Cgroup 限制   |
| Docker 与联合文件系统 | 23 min | 21–31  | 第 28 页：OverlayFS / 第 31 页：Docker 分层 |
| GPU 开发环境          | 14 min | 32–37  | 第 36 页：GPU 容器验证                      |
| 总结回顾              | 10 min | 38–42  | —                                           |

---

## 可视化 HTML

| 文件                                                                        | 用途                                                | 教学场景                                          |
| --------------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------- |
| [Linux I/O 栈 — 存储栈与网络栈](visuals/linux-io-stack.html)                | 存储栈 (write→NVMe) + 网络栈 (send→NIC) 6 层调用链  | 讲解内核空间时打开，对比两条 I/O 路径的共性与差异 |
| [OverlayFS 分层存储 & Copy-on-Write 可视化](visuals/overlayfs-demo.html)    | OverlayFS 三层 (lower/upper/merged) + Copy-on-Write | 讲解 Docker 分层存储时打开，点击按钮演示 COW 过程 |
| [PID Namespace 双视角 — Host vs Container](visuals/pid-namespace-demo.html) | Host vs Container 双栏进程列表对比                  | 讲解 PID Namespace 时打开，启动容器观察 PID 映射  |
| [docker run --gpus all 完整调用链路](visuals/docker-run-gpus-all.html)      | `docker run --gpus all` 完整调用链路                | 课程收尾时打开，用一条命令串起整节课知识点        |
| [containerd 架构可视化](visuals/containerd-architecture.html)               | containerd 内部架构 + vs Docker 早期单体架构对比    | 讲解容器运行时时打开，说明为什么需要分层解耦      |

---

## 配套脚本

| 脚本                                                      | 内容                                    | 对应 PPT |
| --------------------------------------------------------- | --------------------------------------- | -------- |
| [`01_namespace_demo.sh`](code/01_namespace_demo.sh)       | PID / UTS / Mount Namespace 隔离演示    | 第 14 页 |
| [`02_cgroup_demo.sh`](code/02_cgroup_demo.sh)             | Cgroup 资源限制 (CPU / 内存)            | 第 15 页 |
| [`03_overlayfs_demo.sh`](code/03_overlayfs_demo.sh)       | OverlayFS 分层存储底层操作              | 第 22 页 |
| [`04_docker_layer_demo.sh`](code/04_docker_layer_demo.sh) | Docker 镜像分层 + `docker inspect` 分析 | 第 25 页 |

详见 [`code/README.md`](code/README.md)。

---

## 课堂练习

详见 [`hands-on-exercise.md`](hands-on-exercise.md)。

---

## 课后作业

详见 [`homework.md`](homework.md)。实验环境搭建参考： [`lab-environment.md`](lab-environment.md)。

---

## 参考资料

- [cloud-native-dev](https://github.com/ForceInjection/cloud-native-dev) — Linux 入门、Cgroup/Namespace/UnionFS 教程、Demo 脚本
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) — GPU 容器环境搭建
