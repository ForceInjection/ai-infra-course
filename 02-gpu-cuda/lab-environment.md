# 模块 2：GPU 硬件架构与 CUDA 编程入门 — 实验环境说明

## 环境要求

### 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核+ |
| 内存 | 16 GB | 32 GB+ |
| 磁盘 | 50 GB SSD | 100 GB+ SSD |
| GPU | NVIDIA GPU (Compute Capability ≥ 6.0) | A100/H100 (教学集群) 或 RTX 3060+ (个人电脑) |
| GPU 显存 | 4 GB+ | 8 GB+ |

> **Compute Capability 对照**: GTX 10 系列 = 6.1, RTX 20 系列 = 7.5, RTX 30 系列 = 8.6, RTX 40 系列 = 8.9, A100 = 8.0, H100 = 9.0

### 操作系统

- **推荐**: Ubuntu 22.04 LTS (x86_64)
- **备选**: Ubuntu 20.04 LTS
- 也可以使用 WSL2 (Windows) 或 Docker 容器环境

### GPU 环境选择

| 方案 | 适用场景 | 说明 |
|------|---------|------|
| 本地 GPU | 有 NVIDIA 显卡的个人电脑 | 直接安装驱动 + CUDA Toolkit |
| Docker 容器 | 有 GPU 但不想影响宿主机环境 | 使用模块 1 中搭建的 CUDA 容器 |
| 云 GPU | 无本地 GPU | AWS/AutoDL/Lambda Labs 等按需租用 |
| Google Colab | 免费、轻度使用 | 自带 CUDA 环境，适合简单实验 |

---

## 环境搭建步骤

### 方案 A：本地安装 (推荐有 NVIDIA GPU 的学生)

#### Step 1: 安装 NVIDIA 驱动

```bash
# 查看推荐驱动版本
ubuntu-drivers devices

# 安装推荐驱动 (Ubuntu)
sudo apt update
sudo apt install -y nvidia-driver-550

# 重启
sudo reboot

# 验证驱动
nvidia-smi
```

> **注意**: 如果遇到 Nouveau 驱动冲突，需要先禁用: `sudo bash -c "echo blacklist nouveau > /etc/modprobe.d/blacklist-nvidia-nouveau.conf"` 然后重启。

#### Step 2: 安装 CUDA Toolkit

```bash
# 使用 NVIDIA 官方 runfile 安装 (推荐，不依赖系统包管理器)
wget https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda_12.4.0_550.54.14_linux.run
sudo sh cuda_12.4.0_550.54.14_linux.run

# 安装时取消选中 Driver (已经安装过了)，只安装 Toolkit

# 设置环境变量 (添加到 ~/.bashrc)
echo 'export PATH=/usr/local/cuda-12.4/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 验证
nvcc --version
```

#### Step 3: 安装示例代码与编译

```bash
# 克隆 CUDA 示例
git clone https://github.com/NVIDIA/cuda-samples.git
cd cuda-samples/Samples/1_Utilities/deviceQuery
make
./deviceQuery
```

### 方案 B：Docker 容器 (已有 GPU + Docker 环境)

```bash
# 拉取 CUDA 开发镜像
docker pull nvidia/cuda:12.4.0-devel-ubuntu22.04

# 启动交互式开发容器
docker run -it --gpus all \
    -v $(pwd):/workspace \
    -w /workspace \
    nvidia/cuda:12.4.0-devel-ubuntu22.04 /bin/bash

# 验证
nvcc --version
nvidia-smi
```

### 方案 C：Google Colab (免费，无需本地 GPU)

1. 打开 https://colab.research.google.com/
2. 新建 Notebook → 运行时 → 更改运行时类型 → 选择 T4 GPU
3. Colab 自带 CUDA 环境，可以直接运行 CUDA C++ 代码 (通过 `%%cu` magic)

```python
# Colab 中运行 CUDA
!nvcc --version
!nvidia-smi
```

---

## 环境验证清单

```bash
# 1. 确认 GPU 可见
nvidia-smi

# 2. 确认 nvcc 可用
nvcc --version

# 3. 编译测试程序
cat > test.cu << 'EOF'
#include <stdio.h>
#include <cuda_runtime.h>

__global__ void hello() {
    printf("GPU thread %d of block %d\n", threadIdx.x, blockIdx.x);
}

int main() {
    int deviceCount;
    cudaGetDeviceCount(&deviceCount);
    printf("Found %d CUDA device(s)\n", deviceCount);
    hello<<<2, 4>>>();
    cudaDeviceSynchronize();
    return 0;
}
EOF

nvcc -o test test.cu
./test

# 预期输出:
# Found 1 CUDA device(s)
# GPU thread 0 of block 0
# GPU thread 1 of block 0
# ...
```

---

## 常见问题

### Q: `nvidia-smi` 显示 "No devices were found"
- 检查 GPU 是否正确插入/供电
- `lspci | grep -i nvidia` 查看系统是否识别到设备
- 如果是笔记本，确认独显直连已开启

### Q: `nvcc` 命令找不到
- 确认 CUDA Toolkit 已安装: `ls /usr/local/cuda/bin/`
- 确认环境变量已设置: `echo $PATH | grep cuda`
- 重新 source: `source ~/.bashrc`

### Q: `cudaMalloc` 返回错误
- 确认驱动版本与 CUDA 版本兼容
- `nvidia-smi` 顶部显示的 "CUDA Version" 是驱动支持的最高 CUDA 版本

### Q: Colab 中怎样运行 .cu 文件
- 使用 `%%cu` cell magic 直接写 CUDA 代码
- 或使用 `!nvcc -o prog prog.cu && ./prog`
