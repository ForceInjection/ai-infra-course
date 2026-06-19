# 模块 1：Linux 基础与容器技术入门 — 课堂动手题

## 题目：从底层理解容器 — Namespace、Cgroup、UnionFS → Docker

### 题目描述

Docker 的本质 = Namespace (隔离) + Cgroup (限制) + UnionFS (分层存储)。本实验从这三个底层技术出发，逐步构建对容器的理解，最后体验 Docker 如何把它们组合在一起。

### 预计时间

约 25 分钟（共 3 个实验，穿插在对应讲解段落后执行；教师可根据课堂进度选择做 2 个）

| 实验                       | 对应 PPT 页  | 对应课程部分                                     | 时长    |
| -------------------------- | ------------ | ------------------------------------------------ | ------- |
| 实验 1: Namespace 进程隔离 | 第 19 页     | Part 2 — 讲完 PID Namespace 后                   | ~8 min  |
| 实验 2: Cgroup + OverlayFS | 第 20、28 页 | Part 2 末 + Part 3 中 — 讲完 Cgroup/OverlayFS 后 | ~10 min |
| 实验 3: Docker 分层与运行  | 第 31 页     | Part 3 末 — 讲完 Dockerfile 后                   | ~7 min  |

---

## 实验 1: Namespace 进程隔离 (8 min)

> 参考: cloud-native-dev `0_Introduction/面向云原生的 Linux 基础课程/demos/process_isolation_demo.sh` 和 `1.0_Docker/Cgroup 和 Namespace 学习教程.md` §2

### Step 1: 查看当前进程的 Namespace

```bash
# 查看当前 Shell 所属的 namespace
ls -la /proc/self/ns/

# 查看系统中的所有 namespace
lsns | head -10
```

### Step 2: 使用 unshare 创建隔离环境

```bash
# 创建新的 PID + Mount namespace，并成为其中的 root
sudo unshare --pid --mount --fork --mount-proc /bin/bash

# 在隔离环境中验证:
echo "容器内 PID: $$"     # 应该显示 1
ps aux                     # 只能看到隔离环境内的进程
hostname isolated-container
echo "新主机名: $(hostname)"

# 退出隔离环境
exit
```

观察:

- PID 1 → 隔离环境内的 Shell
- 宿主机上 `ps aux | grep bash` 可以看到这个进程，但 PID 不同

### Step 3: 在外部查看 namespace

```bash
# 在另一个终端中运行
sudo lsns | grep unshare
# 或通过 /proc 查看某进程的 namespace
sudo ls -la /proc/<PID>/ns/
```

---

## 实验 2: Cgroup 资源限制 + OverlayFS 分层存储 (10 min)

> 参考: cloud-native-dev `1.0_Docker/Cgroup 和 Namespace 学习教程.md` §4 和 `1.0_Docker/Union Filesystem 学习教程.md` §2

### Part A: Cgroup 内存限制 (5 min)

```bash
# === Ubuntu 22.04+ (cgroup v2，默认) ===
sudo mkdir -p /sys/fs/cgroup/demo
echo "+memory" | sudo tee /sys/fs/cgroup/cgroup.subtree_control
echo "50000000" | sudo tee /sys/fs/cgroup/demo/memory.max
echo $$ | sudo tee /sys/fs/cgroup/demo/cgroup.procs
cat /sys/fs/cgroup/demo/memory.current   # 查看当前内存使用
cat /sys/fs/cgroup/demo/memory.max       # 查看内存上限

# === 如果系统使用 cgroup v1，改用以下命令 ===
# sudo mkdir -p /sys/fs/cgroup/memory/demo
# echo 50000000 | sudo tee /sys/fs/cgroup/memory/demo/memory.limit_in_bytes
# echo $$ | sudo tee /sys/fs/cgroup/memory/demo/cgroup.procs
# cat /sys/fs/cgroup/memory/demo/memory.usage_in_bytes
```

> 进阶: 使用 `stress --vm 1 --vm-bytes 100M` 测试 OOM Killer 效果。

### Part B: OverlayFS 动手体验 (5 min)

```bash
# 创建目录结构
mkdir -p ~/overlay-demo/{lower,upper,work,merged}

# 在下层放置基础文件
echo "This is base layer" > ~/overlay-demo/lower/base.txt
echo "Original config" > ~/overlay-demo/lower/config.txt

# 挂载 OverlayFS
sudo mount -t overlay overlay \
    -o lowerdir=~/overlay-demo/lower,upperdir=~/overlay-demo/upper,workdir=~/overlay-demo/work \
    ~/overlay-demo/merged

# 查看合并视图
ls -la ~/overlay-demo/merged/
cat ~/overlay-demo/merged/base.txt

# 写操作 → 修改只出现在 upper
echo "Modified in container" >> ~/overlay-demo/merged/config.txt
echo "New file created in container" > ~/overlay-demo/merged/new.txt

# 观察各层变化
echo "=== lower (不变) ===" && cat ~/overlay-demo/lower/config.txt
echo "=== upper (新增修改) ===" && ls -la ~/overlay-demo/upper/

# 清理
sudo umount ~/overlay-demo/merged
rm -rf ~/overlay-demo
```

关键观察: **lower 层的 config.txt 没变，修改出现在 upper 层** — 这就是 Docker 的 Copy-on-Write 机制。

---

## 实验 3: Docker 分层与运行 (7 min)

### Step 1: 观察镜像分层

```bash
# 拉取基础镜像
docker pull ubuntu:22.04

# 查看镜像的层历史
docker history ubuntu:22.04

# 查看层详细信息
docker image inspect ubuntu:22.04 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for i, layer in enumerate(data[0]['RootFS']['Layers']):
    print(f'Layer {i}: {layer[:50]}...')
"
```

### Step 2: 构建多层的自定义镜像

```bash
mkdir docker-layer-demo && cd docker-layer-demo

cat > Dockerfile << 'EOF'
FROM ubuntu:22.04
RUN echo "Layer 2: update" && apt-get update -qq
RUN echo "Layer 3: install curl" && apt-get install -y -qq curl
RUN echo "Layer 4: install vim" && apt-get install -y -qq vim
RUN echo "Layer 5: cleanup" && apt-get clean && rm -rf /var/lib/apt/lists/*
EOF

docker build -t layer-demo .
docker history layer-demo
```

观察每一层的大小和创建命令。

### Step 3: 运行容器并查看存储

```bash
# 启动容器
docker run -d --name layer-test layer-demo sleep 300

# 查看容器层
docker diff layer-test   # 查看相比镜像的变化
docker inspect layer-test | python3 -c "
import json, sys
data = json.load(sys.stdin)
gd = data[0]['GraphDriver']
print(f'Driver: {gd[\"Name\"]}')
print(f'LowerDir: {gd[\"Data\"][\"LowerDir\"][:80]}...')
print(f'UpperDir: {gd[\"Data\"][\"UpperDir\"]}')
print(f'MergedDir: {gd[\"Data\"][\"MergedDir\"]}')
"

# 清理
docker rm -f layer-test
cd .. && rm -rf docker-layer-demo
```

观察 `UpperDir` 和 `LowerDir` — 这正是 OverlayFS 的 upperdir 和 lowerdir！

---

## 讲解要点

### 1. 容器 = Namespace + Cgroup + UnionFS

- **Namespace**: 让容器"看到"独立的世界 (PID 从 1 开始、独立网络栈、独立文件系统)
- **Cgroup**: 防止容器"吃掉"所有资源 (CPU、内存、IO 限制)
- **UnionFS/OverlayFS**: 让容器"以为"自己有完整文件系统 (实际是 layering + COW)

### 2. OverlayFS 是 Docker overlay2 存储驱动的核心

- `LowerDir` = 镜像的所有只读层
- `UpperDir` = 容器的可写层
- `MergedDir` = 容器内看到的统一文件系统
- 修改文件时从 LowerDir 复制到 UpperDir → Copy-on-Write

### 3. Docker 镜像的层优化

- 每条 Dockerfile 指令生成一个新层
- 不变的层在多次构建间共享（缓存）
- 合并 RUN 指令减少层数（如 `apt-get update && apt-get install -y pkg1 pkg2 && apt-get clean`）

### 4. 容器 vs 虚拟机的本质差异

| 维度     | 容器                 | 虚拟机                    |
| -------- | -------------------- | ------------------------- |
| 隔离机制 | Namespace + Cgroup   | Hypervisor + Guest OS     |
| 启动时间 | 毫秒级               | 秒级~分钟级               |
| 磁盘占用 | MB 级 (共享基础镜像) | GB 级 (每 VM 一份完整 OS) |
| 内核     | 共享宿主机内核       | 独立 Guest Kernel         |

---

## 实验检查点

完成后应能回答:

- [ ] `unshare --pid --mount-proc --fork /bin/bash` 创建了哪些 namespace？
- [ ] OverlayFS 的 lowerdir、upperdir、merged 各自的作用是什么？
- [ ] Docker 的 `docker history` 输出中，每一行对应什么？
- [ ] 为什么容器内 `apt-get install` 的包不会影响宿主机？
