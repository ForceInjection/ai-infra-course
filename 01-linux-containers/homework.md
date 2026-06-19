# 模块 1：Linux 基础与容器技术入门 — 课后练习

## 题目：手工构建 Linux 进程隔离环境 + Docker 分层存储探索

### 目标

第一部分：不使用 Docker，仅通过 Linux 原生命令手工创建隔离环境。
第二部分：深入探索 Docker 和 OverlayFS 的分层存储机制。

### 截止时间

下次课前 (一周)

---

## 任务 1：手工构建 Linux 进程隔离环境

### 基础任务 (必做)

编写一个 Shell 脚本 `my_container.sh`，实现以下功能：

```bash
#!/bin/bash
# my_container.sh — 手工容器脚本
# 用法: sudo ./my_container.sh <rootfs_dir> <command>

ROOTFS="$1"
COMMAND="$2"
```

**要求**:

1. **文件系统隔离**: 使用 `unshare --mount` + `mount --bind` 为进程创建独立的 mount namespace，或使用 `chroot` 切换到指定的 rootfs

2. **PID 隔离**: 使用 `unshare --pid --fork` 使进程看到独立的 PID 空间 (容器内 PID 从 1 开始)

3. **网络隔离**: 使用 `unshare --net` 为进程分配独立的网络栈

4. **Cgroup 资源限制**: 使用 `cgcreate`/`cgset` 为进程设置：
   - CPU 限制: 最多使用 1 个 CPU 核心
   - 内存限制: 最多使用 256 MB

5. **在隔离环境中执行命令**: 在隔离环境中运行作为参数传入的命令

### 提示与参考

```bash
# 创建 cgroup
sudo cgcreate -g cpu,memory:/mycontainer

# 设置 CPU 限制 (1 核心 = 100000 微秒/100000 微秒)
sudo cgset -r cpu.cfs_quota_us=100000 mycontainer
sudo cgset -r cpu.cfs_period_us=100000 mycontainer

# 设置内存限制
sudo cgset -r memory.limit_in_bytes=268435456 mycontainer  # 256 MB

# 在隔离环境中运行程序
sudo cgexec -g cpu,memory:/mycontainer \
    unshare --mount --pid --fork --net \
    chroot /path/to/rootfs /bin/bash

# 准备最小 rootfs 的方法:
# 1. mkdir -p /tmp/mini-rootfs/{bin,lib,lib64,usr/lib,usr/lib64}
# 2. cp /bin/bash /tmp/mini-rootfs/bin/
# 3. 使用 ldd /bin/bash 找到依赖的 .so 文件并复制过去
```

### 验证方法

在隔离环境中运行以下命令验证：

```bash
# 1. PID 隔离验证
echo "Container PID: $$"   # 应该显示 1 或很小的数字

# 2. 文件系统隔离验证
ls /       # 应该只看到 rootfs 中的文件

# 3. 网络隔离验证
ip addr    # 应该只有 lo 接口

# 4. CPU 限制验证 (开另一个终端在宿主机运行)
# 在容器内: stress --cpu 2
# 在宿主机: top 观察 CPU 使用率，容器进程不应超过 1 核

# 5. 内存限制验证
# 在容器内: stress --vm 1 --vm-bytes 300M
# 应该触发 OOM Killer，进程被杀死
```

---

## 任务 2：Docker 分层存储探索 (必做)

参考 cloud-native-dev `1.0_Docker/Union Filesystem 学习教程.md` §4，完成以下探索：

1. **分析 Docker 镜像层**: 选择一个你常用的 Docker 镜像（如 `ubuntu:22.04`, `python:3.11`），使用 `docker history` 查看其层结构。记录每一层的大小和用途。

2. **验证层共享**: 拉取两个共享基础镜像的 image（如 `ubuntu:22.04` 和 `ubuntu:20.04` 或 `python:3.11`），确认 `docker system df -v` 中共享层的存储仅计算一次。

3. **多层构建实验**: 编写一个至少有 5 层的 Dockerfile，先构建一次，然后修改中间某一行，再次构建。记录哪些层使用了缓存（`CACHED`），哪些层被重建。解释缓存失效原理。

4. **OverlayFS 文件定位**: 使用 `docker inspect` 找到某运行中容器的 `UpperDir` 和 `LowerDir`，进入 `UpperDir` 查看容器运行时产生的新文件和修改文件。删除容器后观察 `UpperDir` 的变化。

---

## 进阶任务 (选做)

### Option A: 增强手工容器

在上述基础容器的基础上，实现以下增强功能：

1. **Overlay 文件系统**: 不使用 chroot，而是用 OverlayFS 挂载 (类似 Docker 的分层机制)
2. **容器快照**: 在退出容器时，将 upperdir 打包保存为一个 tar 文件，实现类似 `docker commit` 的效果
3. **资源监控**: 在脚本中添加 CPU/内存使用监控，容器退出时打印统计信息

### Option B: 多容器网络实验

参考 cloud-native-dev `0_Introduction/面向云原生的 Linux 基础课程/demos/container_communication.sh`，使用 `ip netns` 创建两个网络隔离的 namespace，通过 veth pair 连接它们。验证网络隔离和连通性。

---

## 提交要求

1. 提交 `my_container.sh` 脚本
2. 提交 Docker 分层存储探索报告 (≤ 2 页)，包含：
   - `docker history` 输出截图和分析
   - 层缓存实验记录
   - OverlayFS UpperDir/LowerDir 探索截图
3. 简述以下问题：
   - Docker 在你手工实现的容器之上还做了哪些事情？（至少列出 3 点）
   - OverlayFS 的 Copy-on-Write 机制如何让多个容器共享同一个基础镜像？

---

## 评分标准

| 维度              | 权重 | 要求                                               |
| ----------------- | ---- | -------------------------------------------------- |
| 任务 1 (手工容器) | 35%  | 至少实现 PID/Mount/Network 隔离 + CPU/内存限制之一 |
| 任务 2 (分层存储) | 35%  | 完成所有 4 项探索并提交报告                        |
| 代码与文档质量    | 15%  | 脚本有清晰的注释、错误处理；报告有截图和分析       |
| 进阶任务          | 15%  | 完成至少一项进阶功能                               |

---

## 参考资料

- cloud-native-dev: `1.0_Docker/Cgroup 和 Namespace 学习教程.md` — Namespace/Cgroup 完整教程 (§2 unshare 实验, §4 cgroup 实验)
- cloud-native-dev: `1.0_Docker/Union Filesystem 学习教程.md` — OverlayFS 原理与实践 (§2 OverlayFS 挂载, §3 Docker 存储驱动, §4 镜像分层分析)
- cloud-native-dev: `0_Introduction/面向云原生的 Linux 基础课程/demos/process_isolation_demo.sh` — 进程隔离演示参考
- cloud-native-dev: `0_Introduction/面向云原生的 Linux 基础课程/demos/image_layers_demo.sh` — 镜像层演示参考
- `man unshare` / `man cgcreate` / `man cgset` — Linux 手册
- AI-fundamentals: `04_cloud_native_ai_platform/k8s/01_nvidia_container_toolkit_analysis.md` — 容器运行时接入 GPU
