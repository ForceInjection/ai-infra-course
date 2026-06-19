# 模块 1：Linux 基础与容器技术入门

> 90 分钟 &nbsp;|&nbsp; 53 页 PPT &nbsp;|&nbsp; 4 个 Bash 脚本 &nbsp;|&nbsp; 4 个可视化 HTML

## 目录结构

```text
01-linux-containers/
├── README.md                          # 本文件
├── syllabus.md                        # 教学大纲 (90 分钟时间分配)
├── ppt-outline.md                     # PPT 大纲 (53 页)
├── hands-on-exercise.md               # 课堂动手题 (3 个实验)
├── homework.md                        # 课后练习
├── lab-environment.md                 # 实验环境搭建说明
├── Linux基础与容器技术入门.pptx        # 课件
├── code/                              # 配套脚本 (4 个)
│   ├── README.md                      #   编译运行说明 + 预期输出
│   ├── 01_namespace_demo.sh           #   Namespace 隔离 (PPT §2, 第14页)
│   ├── 02_cgroup_demo.sh              #   Cgroup 资源限制 (PPT §2, 第15页)
│   ├── 03_overlayfs_demo.sh           #   OverlayFS 分层存储 (PPT §3, 第22页)
│   └── 04_docker_layer_demo.sh        #   Docker 镜像分层 (PPT §3, 第25页)
└── visuals/                           # 可视化 HTML (4 个)
    ├── overlayfs-demo.html            #   OverlayFS + COW 交互演示
    ├── pid-namespace-demo.html        #   PID Namespace Host vs Container 双视角
    ├── docker-run-gpus-all.html       #   docker run --gpus all 完整调用链路
    └── containerd-architecture.html   #   containerd 架构 + vs Docker 早期对比
```

## 可视化 HTML

| 文件                           | 用途                                                | 教学场景                                          |
| ------------------------------ | --------------------------------------------------- | ------------------------------------------------- |
| `overlayfs-demo.html`          | OverlayFS 三层 (lower/upper/merged) + Copy-on-Write | 讲解 Docker 分层存储时打开，点击按钮演示 COW 过程 |
| `pid-namespace-demo.html`      | Host vs Container 双栏进程列表对比                  | 讲解 PID Namespace 时打开，启动容器观察 PID 映射  |
| `docker-run-gpus-all.html`     | `docker run --gpus all` 完整调用链路                | 课程收尾时打开，用一条命令串起整节课知识点        |
| `containerd-architecture.html` | containerd 内部架构 + vs Docker 早期单体架构对比    | 讲解容器运行时时打开，说明为什么需要分层解耦      |

## 教学流程

| 阶段                  | 时长   | PPT 页 | 动手                                        |
| --------------------- | ------ | ------ | ------------------------------------------- |
| Linux 命令行基础      | 20 min | 3–11   | 第 9 页：基础实操                           |
| Namespace 与 Cgroup   | 23 min | 12–20  | 第 19 页：NS 隔离 / 第 20 页：Cgroup 限制   |
| Docker 与联合文件系统 | 23 min | 21–31  | 第 28 页：OverlayFS / 第 31 页：Docker 分层 |
| GPU 开发环境          | 14 min | 32–37  | 第 36 页：GPU 容器验证                      |
| 总结回顾              | 10 min | 38–42  | —                                           |

## 实验环境

| 方式        | 说明                            |
| ----------- | ------------------------------- |
| Bash 脚本   | 直接执行 `.sh`，部分需要 `sudo` |
| 可视化 HTML | 浏览器直接打开，无需服务器      |

## 参考来源

- [cloud-native-dev](https://github.com/ForceInjection/cloud-native-dev) — Linux 入门、Cgroup/Namespace/UnionFS 教程、Demo 脚本
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals) — GPU 容器环境搭建
