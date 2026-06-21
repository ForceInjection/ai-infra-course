# 方向 A: 容器化 GPU 推理 — 从隔离到拦截

**难度**: ★★★☆ &nbsp;|&nbsp; **覆盖模块**: 1 (容器), 3 (GPU 虚拟化), 5 (vLLM) &nbsp;|&nbsp; **CUDA 12.8+**

## 快速开始

```bash
# 1. 编译 CUDA hook
make

# 2. 测试 hook 加载 (不需要 GPU)
make test

# 3. 有 GPU 时: 在 nano-vllm 中验证
pip install nanovllm
LD_PRELOAD=./libcuda_hook.so CUDA_MEM_QUOTA_MB=512 python3 -c "
from nanovllm import LLM, SamplingParams
llm = LLM('Qwen/Qwen3-0.6B', enforce_eager=True)
llm.generate(['Hello'], SamplingParams(max_tokens=10))
"

# 4. 构建 Docker 镜像
docker build -t gpu-inference-hook .
docker run --gpus all -e CUDA_MEM_QUOTA_MB=512 gpu-inference-hook
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `cuda_hook.c` | LD_PRELOAD CUDA hook 骨架 (搜索 `TODO`) |
| `Makefile` | 一键编译 `libcuda_hook.so` |
| `Dockerfile` | GPU 推理容器模板 |

## 无 GPU 替代方案

如果无 GPU，可将 `cudaMalloc` 替换为 `malloc`，重做模块 3 的 LD_PRELOAD 实验并增强配额管理逻辑。
