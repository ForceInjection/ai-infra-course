# GPU 推理容器镜像
# 构建: docker build -t gpu-inference-hook .
# 运行: docker run --gpus all -e CUDA_MEM_QUOTA_MB=512 gpu-inference-hook

FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

# 安装 Python + nano-vllm 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip git build-essential && \
    rm -rf /var/lib/apt/lists/*

# TODO: 安装 nano-vllm (参考模块 5 lab-environment.md)
# RUN pip3 install ...

# 复制 hook 源码并编译
# TODO: COPY cuda_hook.c Makefile /app/
# TODO: RUN cd /app && make

# 复制实验脚本
# TODO: COPY experiments/ /app/experiments/

WORKDIR /app

# 验证 GPU 可见性和 hook 加载
# TODO: CMD 或 ENTRYPOINT
