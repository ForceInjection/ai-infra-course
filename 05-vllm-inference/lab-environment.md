# 模块 5：大模型推理框架入门：以 vLLM 为例 — 实验环境说明

## 环境要求

### 硬件要求

| 项目 | 最低配置       | 推荐配置                          |
| ---- | -------------- | --------------------------------- |
| CPU  | 8 核           | 16 核+                            |
| 内存 | 16 GB          | 32 GB+                            |
| 磁盘 | 50 GB 可用空间 | 100 GB+                           |
| GPU  | ≥ 8 GB 显存    | ≥ 16 GB 显存 (A100/H100/RTX 4090) |

> **最低 GPU 要求**: 至少能运行 Qwen2.5-0.5B (约 1GB 模型参数)，建议 ≥ 8 GB 显存以运行 7B 模型。

### 操作系统

- **推荐**: Ubuntu 22.04 LTS
- **备选**: 任何支持 CUDA 12.x 的 Linux 发行版

### 软件要求

| 软件         | 版本    | 用途                            |
| ------------ | ------- | ------------------------------- |
| Python       | ≥ 3.10  | 运行 vLLM                       |
| CUDA Toolkit | ≥ 12.1  | GPU 计算                        |
| vLLM         | ≥ 0.6.0 | 推理引擎                        |
| nano-vllm    | latest  | 教学级推理引擎 (~1400行 Python) |

---

## 环境搭建

### vLLM 环境

### Step 1: 创建 Python 虚拟环境

```bash
python3 -m venv vllm-env
source vllm-env/bin/activate
```

### Step 2: 安装 vLLM

```bash
# 使用 pip 安装 (预编译 wheel)
pip install vllm

# 或从源码安装最新版
# pip install git+https://github.com/vllm-project/vllm.git
```

### Step 3: 验证安装

```bash
python -c "import vllm; print(vllm.__version__)"

# 检查是否检测到 GPU
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')"
```

### Step 4: 下载测试模型

```bash
# 使用极小模型进行快速测试
# Qwen2.5-0.5B-Instruct (~1 GB)
python -c "from transformers import AutoModel; AutoModel.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct')"
```

### nano-vllm 环境

```bash
# 安装 nano-vllm
pip install git+https://github.com/GeeeekExplorer/nano-vllm.git

# 下载测试模型 (Qwen3-0.6B, ~1.2GB)
huggingface-cli download --resume-download Qwen/Qwen3-0.6B \
    --local-dir ~/huggingface/Qwen3-0.6B/ \
    --local-dir-use-symlinks False

# 验证
python -c "from nanovllm import LLM; print('nano-vllm OK')"
```

---

## 环境验证清单

```bash
# 1. vLLM 基本启动测试
vllm serve Qwen/Qwen2.5-0.5B-Instruct \
    --host 0.0.0.0 --port 8000 \
    --max-model-len 2048 &

# 等待服务就绪
sleep 30

# 2. API 调用测试
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "messages": [{"role": "user", "content": "你好，请用一句话介绍自己"}],
        "max_tokens": 50
    }'

# 3. 停止服务
kill %1
```

---

## 模型选择建议

根据 GPU 显存选择合适的模型:

| GPU 显存 | 推荐模型                        | 参数量 | 模型大小 |
| -------- | ------------------------------- | ------ | -------- |
| 4-6 GB   | Qwen2.5-0.5B-Instruct           | 0.5B   | ~1 GB    |
| 8-12 GB  | Qwen2.5-7B-Instruct (INT4 量化) | 7B     | ~4.5 GB  |
| 16-24 GB | Qwen2.5-7B-Instruct             | 7B     | ~14 GB   |
| 24-40 GB | Qwen2.5-14B-Instruct            | 14B    | ~28 GB   |
| 40 GB+   | Qwen2.5-32B-Instruct            | 32B    | ~64 GB   |
| 80 GB+   | Qwen2.5-72B-Instruct            | 72B    | ~144 GB  |

---

## 常见问题

### Q: vLLM 启动 OOM

```bash
# 降低 GPU 显存使用比例
vllm serve <model> --gpu-memory-utilization 0.7

# 或使用更小的模型
vllm serve Qwen/Qwen2.5-0.5B-Instruct
```

### Q: CUDA 版本不兼容

```bash
# 检查 CUDA 版本
nvcc --version
python -c "import torch; print(torch.version.cuda)"

# vLLM 需要 CUDA ≥ 12.1，如果版本低则升级驱动
```

### Q: 下载模型很慢

```bash
# 使用 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com
# 或使用 ModelScope
pip install modelscope
```

### Q: 无 GPU 环境如何实验

```bash
# vLLM 可以在 CPU 上运行 (性能较低)
VLLM_CPU_ONLY=1 pip install vllm
# 或使用 Google Colab (免费 T4 GPU)
```
