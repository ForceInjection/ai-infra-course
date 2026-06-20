# 模块 3：GPU 虚拟化与容器化实践 — 课堂动手题

## 题目：LD_PRELOAD 拦截实验 + GPU 容器构建

### 题目描述

通过两个实验理解 GPU 虚拟化的核心机制：

1. **LD_PRELOAD malloc hook** — 理解函数拦截原理，这是 HAMi 的基石
2. **GPU 容器验证** — 验证 NVIDIA Container Toolkit 的设备注入

### 预计时间

15 分钟

---

## 实验 1: LD_PRELOAD malloc hook (8 min)

> 对应 PPT 第 12 页 + 第 33 页 [动手 1]

### Step 1: 编写 hook 代码 (3 min)

```c
// mymalloc.c
#define _GNU_SOURCE
#include <stdio.h>
#include <dlfcn.h>

static size_t total_allocated = 0;

void *malloc(size_t size) {
    static void *(*real_malloc)(size_t) = NULL;
    if (!real_malloc)
        real_malloc = dlsym(RTLD_NEXT, "malloc");

    void *p = real_malloc(size);
    total_allocated += size;
    printf("[HOOK] malloc(%zu) = %p  (累计: %zu bytes)\n",
           size, p, total_allocated);
    return p;
}
```

### Step 2: 编译并测试 (2 min)

```bash
# 编译为共享库
gcc -shared -fPIC mymalloc.c -o libmymalloc.so -ldl

# 用 LD_PRELOAD 运行任意程序
LD_PRELOAD=./libmymalloc.so ls -la

# 再试一个
LD_PRELOAD=./libmymalloc.so python3 -c "x = [1]*1000"
```

### Step 3: 思考与讨论 (3 min)

- 观察: `ls` 和 `python3` 的 `malloc` 调用全部被我们的 hook 拦截了
- 如果把 `malloc` 换成 `cuMemAlloc`，我们就可以：
  - 记录每次显存分配的大小
  - 检查累计分配是否超过配额 → 超配额时返回 `CUDA_ERROR_OUT_OF_MEMORY`
  - 这就是 HAMi 显存隔离的核心！

> **关键理解**: HAMi 的 `libvgpu.so` 就是用同样的方式 hook `cuMemAlloc`、`cuLaunchKernel` 等 CUDA API。

---

## 实验 2: GPU 容器验证 (7 min)

> 对应 PPT 第 34 页 [动手 2]

### Step 1: 基础验证 (2 min)

```bash
# 在容器内查看 GPU
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# 查看容器内的 GPU 设备文件
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 ls -la /dev/nvidia*

# 查看注入的环境变量
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 env | grep NVIDIA
```

### Step 2: CUDA 编译环境验证 (2 min)

```bash
# 用 devel 镜像编译并运行 CUDA 程序
docker run --rm --gpus all -v $(pwd):/workspace nvidia/cuda:12.4.0-devel-ubuntu22.04 bash -c "
cd /workspace
cat > test.cu << 'EOF'
#include <stdio.h>
__global__ void hello() {
    printf(\"GPU thread %d\\n\", threadIdx.x);
}
int main() {
    hello<<<1,4>>>();
    cudaDeviceSynchronize();
    return 0;
}
EOF
nvcc -o test test.cu && ./test
"
```

### Step 3: vLLM 推理镜像快速构建 (3 min)

```bash
# 编写最简单的 vLLM Dockerfile
cat > Dockerfile << 'EOF'
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y python3-pip && pip install vllm
ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server"]
CMD ["--model", "Qwen/Qwen2.5-0.5B-Instruct", "--host", "0.0.0.0", "--port", "8000"]
EOF

# 构建 (可以只做前几步，不一定跑完)
docker build -t vllm-demo:v1 .

# 查看镜像大小和层
docker history vllm-demo:v1
```

---

## 讲解要点

### 1. LD_PRELOAD = HAMi 的基石

- `dlsym(RTLD_NEXT, "malloc")` 获取原始函数 → 我们的 hook 调用原始函数 → 在前后加入检查逻辑
- HAMi: `dlsym(RTLD_NEXT, "cuMemAlloc")` → 检查显存配额 → 调用真正的 `cuMemAlloc`
- 「你刚写的 30 行代码，就是 HAMi 几千行代码的核心原理」

### 2. GPU 设备如何进入容器

- `nvidia-container-runtime-hook` 在容器启动前执行
- 通过 NVML 查询 GPU → `mknod` 创建设备文件 → `mount --bind` 挂载驱动库
- 「容器内看到的 GPU，是宿主机通过 hook 注入的」

### 3. 容器镜像分层

- `nvidia/cuda:12.4.0-base` → ~100MB (只有运行时库)
- `nvidia/cuda:12.4.0-runtime` → ~600MB (+cuBLAS/cuFFT)
- `nvidia/cuda:12.4.0-devel` → ~3GB (+nvcc+头文件)
- 推理用 runtime，编译用 devel
