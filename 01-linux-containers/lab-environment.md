# 模块 1：Linux 基础与容器技术入门 — 实验环境说明

## 环境要求

### 硬件要求

| 项目 | 最低配置           | 推荐配置                             |
| ---- | ------------------ | ------------------------------------ |
| CPU  | 4 核               | 8 核+                                |
| 内存 | 8 GB               | 16 GB+                               |
| 磁盘 | 50 GB 可用空间     | 100 GB SSD                           |
| GPU  | 无（本模块不需要） | NVIDIA GPU (可选，用于 GPU 容器演示) |
| 网络 | 可访问 Docker Hub  | 稳定互联网连接                       |

### 操作系统

- **推荐**: Ubuntu 22.04 LTS (x86_64)
- **备选**: Ubuntu 20.04 LTS, Debian 11+, CentOS 8+ / Rocky Linux 8+
- **Mac 用户**: 推荐使用 Colima 或 OrbStack 作为 Docker 运行时（避免 Docker Desktop 的资源开销）
- 如使用 macOS/Windows，部分底层实验（unshare、cgroup、mount overlay）**必须**在 Linux 虚拟机中完成

### Mac 环境搭建

> 参考: cloud-native-dev `0_Introduction/Install/mac/` 安装脚本

```bash
# 方案 1: 使用 Colima (推荐，免费)
brew install colima docker
colima start --cpu 4 --memory 8 --disk 50
docker run --rm hello-world

# 方案 2: 使用 OrbStack (免费，体验好)
brew install orbstack
# 启动 OrbStack 后，docker 自动可用

# 对于底层实验，通过 multipass 创建 Ubuntu VM
brew install multipass
multipass launch --name linux-lab --cpus 4 --mem 8G --disk 50G
multipass shell linux-lab
```

### 软件要求

| 软件                     | 版本          | 用途         |
| ------------------------ | ------------- | ------------ |
| Docker Engine            | ≥ 24.0        | 容器运行时   |
| NVIDIA Driver            | ≥ 535 (可选)  | GPU 容器支持 |
| NVIDIA Container Toolkit | ≥ 1.14 (可选) | GPU 容器支持 |

---

## 环境搭建步骤

### 步骤 1：安装 Docker Engine

```bash
# 卸载旧版本 (如存在)
sudo apt-get remove docker docker-engine docker.io containerd runc

# 安装依赖
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

# 验证安装
sudo docker run --rm hello-world

# 将当前用户加入 docker 组 (免 sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### 步骤 2：安装 Cgroup 工具和 stress

```bash
sudo apt-get install -y cgroup-tools stress
```

### 步骤 2.5：验证 OverlayFS 支持

```bash
# 检查内核是否支持 OverlayFS
grep -i overlay /proc/filesystems
lsmod | grep overlay

# 如果没有加载，手动加载
sudo modprobe overlay
```

### 步骤 3：(可选) 安装 NVIDIA Container Toolkit

仅当有 NVIDIA GPU 时执行：

```bash
# 添加 NVIDIA 仓库
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 配置 Docker 使用 nvidia runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 验证
sudo docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

### 步骤 4：拉取必要的镜像

```bash
# 基础 Ubuntu 镜像 (用于 Linux 和 Docker 实验)
docker pull ubuntu:22.04

# CUDA 开发镜像 (如需 GPU 演示)
docker pull nvidia/cuda:12.4.0-devel-ubuntu22.04
```

---

## 环境验证清单

在上课前，请确认以下所有项都能通过：

```bash
# 1. Docker 正常运行
docker version

# 2. 能拉取镜像
docker pull alpine:latest

# 3. 能运行容器
docker run --rm alpine echo "Hello from Docker"

# 4. cgroup 工具可用
which cgcreate cgset cgexec
ls /sys/fs/cgroup/

# 5. OverlayFS 内核支持
grep overlay /proc/filesystems

# 6. stress 工具可用
which stress

# 7. (如有 GPU) GPU 容器可用
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

---

## 常见问题

### Q: Docker 拉取镜像很慢

```bash
# 配置国内镜像加速器，编辑 /etc/docker/daemon.json:
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.m.daocloud.io"
  ]
}
sudo systemctl restart docker
```

### Q: `docker run` 报 permission denied

```bash
# 确保用户在 docker 组中
sudo usermod -aG docker $USER
# 注销重新登录，或执行
newgrp docker
```

### Q: GPU 容器提示 could not select device driver

```bash
# 确认 nvidia-container-toolkit 已安装
nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Q: macOS/Windows 环境如何准备

- 安装 VirtualBox 或 UTM，创建 Ubuntu 22.04 虚拟机 (≥ 4 核, ≥ 8 GB 内存)
- SSH 进入虚拟机后按上述步骤操作
- 不建议直接在 macOS 上操作 (Namespace/Cgroup 行为与 Linux 不同)
