# 模块 3：GPU 虚拟化与容器化实践 — 课后练习

## 题目：构建并优化 LLM 推理服务容器镜像

### 目标

构建一个包含 vLLM 的高效 Docker 镜像，实现 LLM 推理服务的一键部署。通过对比不同构建策略的镜像大小和启动速度，理解 Docker 镜像优化的实际价值。

### 截止时间

下次课前 (一周)

---

## 基础任务 (必做)

### 任务 1: 构建基础 vLLM 镜像

编写一个 Dockerfile，构建包含 vLLM 的推理服务镜像：

```dockerfile
# Dockerfile.vllm (基础版本)
FROM nvidia/cuda:12.4.0-devel-ubuntu22.04

RUN apt-get update && apt-get install -y python3-pip git && \
    pip install vllm

COPY serve.sh /serve.sh
RUN chmod +x /serve.sh

ENTRYPOINT ["/serve.sh"]
```

`serve.sh`:
```bash
#!/bin/bash
# 默认使用 Qwen2.5-0.5B (极小模型，适合实验)
MODEL=${MODEL_NAME:-Qwen/Qwen2.5-0.5B-Instruct}
python -m vllm.entrypoints.openai.api_server \
    --model $MODEL \
    --host 0.0.0.0 \
    --port 8000
```

```bash
# 构建
docker build -f Dockerfile.vllm -t vllm-service:basic .
# 查看镜像大小
docker images vllm-service:basic
```

记录镜像大小和构建时间。

### 任务 2: 使用多阶段构建优化

修改 Dockerfile，使用多阶段构建减小镜像体积：

```dockerfile
# Dockerfile.vllm (优化版本)
# --- Stage 1: Build ---
FROM nvidia/cuda:12.4.0-devel-ubuntu22.04 AS builder
RUN apt-get update && apt-get install -y python3-pip git
RUN pip install --no-cache-dir vllm

# --- Stage 2: Runtime ---
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y python3-minimal
COPY --from=builder /usr/local/lib/python3.*/dist-packages /usr/local/lib/python3.*/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY serve.sh /serve.sh
RUN chmod +x /serve.sh
ENTRYPOINT ["/serve.sh"]
```

对比优化前后的镜像大小。

### 任务 3: 测试 GPU 虚拟化效果

如果已完成模块 2 的实验且搭建了 HAMi，请在同一张 GPU 上：
1. 启动两个 vLLM 服务实例（使用不同的模型或端口）
2. 配置每个实例的显存限制
3. 验证两个实例能否同时正常运行

```yaml
# 示例 Pod 配置
apiVersion: v1
kind: Pod
metadata:
  name: vllm-instance-1
spec:
  containers:
  - name: vllm
    image: vllm-service:optimized
    env:
    - name: MODEL_NAME
      value: "Qwen/Qwen2.5-0.5B-Instruct"
    resources:
      limits:
        nvidia.com/gpu: 1
        nvidia.com/gpumem: 4096       # 4 GB 显存限制
        nvidia.com/gpucores: 40       # 40% 算力
    ports:
    - containerPort: 8000
```

---

## 进阶任务 (选做)

### 任务 4: 镜像安全扫描

使用 Docker Scout 或 Trivy 扫描镜像的安全漏洞：

```bash
# 使用 Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image vllm-service:optimized

# 或使用 Docker Scout
docker scout quickview vllm-service:optimized
```

报告关键漏洞并提供修复建议。

### 任务 5: 实现多架构镜像构建

使用 `docker buildx` 构建同时支持 x86_64 和 arm64 的镜像：

```bash
docker buildx create --name multiarch --use
docker buildx build --platform linux/amd64,linux/arm64 \
    -f Dockerfile.vllm -t vllm-service:multiarch --push .
```

---

## 提交要求

1. 提交两个 Dockerfile (基础版 + 优化版)
2. 提交 `serve.sh` 脚本
3. 提交实验报告 (≤ 2 页)，包含：
   - 基础版 vs 优化版的镜像大小对比
   - 镜像构建时间对比
   - 镜像每一层的大小分布 (`docker history` 输出)
   - 基础版 vs 优化版的冷启动时间对比
   - (可选) 安全扫描结果
4. 如果能运行 GPU 虚拟化测试，提交日志截图

---

## 评分标准

| 维度 | 权重 | 要求 |
|------|------|------|
| 任务 1-3 完成度 | 60% | 成功构建两个镜像，完成大小对比 |
| 优化效果 | 15% | 多阶段构建有明显的大小缩减 |
| 实验报告 | 15% | 有数据支撑的对比分析 |
| 进阶任务 | 10% | 完成至少一项进阶任务 |

---

## 参考资料

- AI-fundamentals: `02_gpu_programming/01_environment/02_cuda_image_build_analysis.md` — CUDA 镜像构建深度解析
- AI-fundamentals: `04_cloud_native_ai_platform/gpu_manager/hami/hmai-gpu-resources-guide.md` — HAMi 资源管理手册
- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/)
- [vLLM Docker 官方镜像](https://docs.vllm.ai/en/latest/getting_started/installation.html)
