# 模块 2：GPU 硬件架构与 CUDA 编程入门 — 课堂动手题

## 题目：CUDA 向量加法 + 矩阵乘法（Naive vs Tiled）

### 题目描述

从零编写三个 CUDA 程序，逐步体验「正确→高效」的优化过程：

1. **向量加法**: 第一个 CUDA 程序，理解 kernel 启动和线程索引
2. **矩阵乘法 naive**: 正确的实现，发现带宽瓶颈
3. **矩阵乘法 tiled**: 用 shared memory 加速，理解优化原理

### 预计时间

约 25 分钟（共 3 个实验，穿插在对应讲解段落后执行）

| 实验                   | 对应 PPT 页    | 触发时机                              | 时长    |
| ---------------------- | -------------- | ------------------------------------- | ------- |
| 实验 1: 向量加法       | 第 30–31 页    | Part 3 开始 — 讲完 Host-Device 模型后 | ~8 min  |
| 实验 2: Naive 矩阵乘法 | 第 33–34 页    | Part 3 中 — 讲完矩阵乘法映射后        | ~7 min  |
| 实验 3: Tiled 矩阵乘法 | 第 36 页       | Part 3 末 — 讲完 Tiling 原理后        | ~10 min |

---

## 实验 1: 向量加法 — 第一个 CUDA 程序 (8 min)

### Step 1: 编写代码 (3 min)

```cuda
// vec_add.cu
#include <stdio.h>
#include <cuda_runtime.h>
#include <sys/time.h>

__global__ void vec_add_gpu(float *A, float *B, float *C, int N) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid < N) {
        C[tid] = A[tid] + B[tid];
    }
}

double get_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec * 1e-6;
}

void vec_add_cpu(float *A, float *B, float *C, int N) {
    for (int i = 0; i < N; i++) C[i] = A[i] + B[i];
}

int main() {
    int N = 1 << 24;  // 16M elements
    size_t bytes = N * sizeof(float);

    // CPU 版本
    float *h_A = (float*)malloc(bytes);
    float *h_B = (float*)malloc(bytes);
    float *h_C_cpu = (float*)malloc(bytes);
    float *h_C_gpu = (float*)malloc(bytes);
    for (int i = 0; i < N; i++) {
        h_A[i] = rand() / (float)RAND_MAX;
        h_B[i] = rand() / (float)RAND_MAX;
    }

    // === CPU 版本 ===
    double start = get_time();
    vec_add_cpu(h_A, h_B, h_C_cpu, N);
    printf("CPU: %.3f ms\n", (get_time() - start) * 1000);

    // === GPU 版本 ===
    float *d_A, *d_B, *d_C;
    cudaMalloc(&d_A, bytes);
    cudaMalloc(&d_B, bytes);
    cudaMalloc(&d_C, bytes);

    cudaEvent_t gpu_start, gpu_stop;
    cudaEventCreate(&gpu_start);
    cudaEventCreate(&gpu_stop);
    cudaEventRecord(gpu_start);

    cudaMemcpy(d_A, h_A, bytes, cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B, bytes, cudaMemcpyHostToDevice);
    int threads = 256;
    int blocks = (N + threads - 1) / threads;
    vec_add_gpu<<<blocks, threads>>>(d_A, d_B, d_C, N);
    cudaMemcpy(h_C_gpu, d_C, bytes, cudaMemcpyDeviceToHost);

    cudaEventRecord(gpu_stop);
    cudaEventSynchronize(gpu_stop);
    float ms;
    cudaEventElapsedTime(&ms, gpu_start, gpu_stop);
    printf("GPU (total incl. transfer): %.3f ms\n", ms);

    // 验证正确性
    int errors = 0;
    for (int i = 0; i < N; i++)
        if (abs(h_C_cpu[i] - h_C_gpu[i]) > 0.001f) errors++;
    printf("Errors: %d / %d\n", errors, N);

    cudaFree(d_A); cudaFree(d_B); cudaFree(d_C);
    free(h_A); free(h_B); free(h_C_cpu); free(h_C_gpu);
    return 0;
}
```

### Step 2: 编译运行 (2 min)

```bash
nvcc -O2 vec_add.cu -o vec_add
./vec_add
```

### Step 3: 分别测量传输和计算时间 (3 min)

修改代码，用三个 `cudaEvent` 对分别测量 H2D 传输、Kernel 执行、D2H 传输。讨论:

- 哪个阶段占比最大？
- 如果 N 只有 1024，GPU 还更快吗？为什么？

---

## 实验 2: Naive 矩阵乘法 (7 min)

```cuda
// matmul_naive.cu
#include <stdio.h>
#include <cuda_runtime.h>

#define M 1024
#define N 1024
#define K 1024
#define BLOCK_SIZE 16

__global__ void matmul_naive(float *A, float *B, float *C) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < M && col < N) {
        float sum = 0.0f;
        for (int k = 0; k < K; k++)
            sum += A[row * K + k] * B[k * N + col];
        C[row * N + col] = sum;
    }
}

int main() {
    size_t bytes_A = M * K * sizeof(float);
    size_t bytes_B = K * N * sizeof(float);
    size_t bytes_C = M * N * sizeof(float);

    float *h_A = (float*)malloc(bytes_A);
    float *h_B = (float*)malloc(bytes_B);
    float *h_C = (float*)malloc(bytes_C);
    for (int i = 0; i < M*K; i++) h_A[i] = (float)rand()/RAND_MAX;
    for (int i = 0; i < K*N; i++) h_B[i] = (float)rand()/RAND_MAX;

    float *d_A, *d_B, *d_C;
    cudaMalloc(&d_A, bytes_A);
    cudaMalloc(&d_B, bytes_B);
    cudaMalloc(&d_C, bytes_C);
    cudaMemcpy(d_A, h_A, bytes_A, cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B, bytes_B, cudaMemcpyHostToDevice);

    dim3 block(BLOCK_SIZE, BLOCK_SIZE);
    dim3 grid((N+BLOCK_SIZE-1)/BLOCK_SIZE, (M+BLOCK_SIZE-1)/BLOCK_SIZE);

    cudaEvent_t start, stop;
    cudaEventCreate(&start); cudaEventCreate(&stop);
    cudaEventRecord(start);
    matmul_naive<<<grid, block>>>(d_A, d_B, d_C);
    cudaEventRecord(stop);
    cudaEventSynchronize(stop);
    float ms;
    cudaEventElapsedTime(&ms, start, stop);
    cudaMemcpy(h_C, d_C, bytes_C, cudaMemcpyDeviceToHost);

    printf("Naive MatMul (%dx%dx%d): %.3f ms\n", M, N, K, ms);
    printf("Arithmetic Intensity: %.1f FLOPs/byte\n", (2.0f*M*N*K)/((M*K+K*N+M*N)*4.0f));

    cudaFree(d_A); cudaFree(d_B); cudaFree(d_C);
    free(h_A); free(h_B); free(h_C);
    return 0;
}
```

---

## 实验 3: Tiled 矩阵乘法 — Shared Memory 优化 (10 min)

```cuda
// matmul_tiled.cu
#define TILE_SIZE 16

__global__ void matmul_tiled(float *A, float *B, float *C) {
    int row = blockIdx.y * TILE_SIZE + threadIdx.y;
    int col = blockIdx.x * TILE_SIZE + threadIdx.x;

    __shared__ float As[TILE_SIZE][TILE_SIZE];
    __shared__ float Bs[TILE_SIZE][TILE_SIZE];

    float sum = 0.0f;
    int tiles = (K + TILE_SIZE - 1) / TILE_SIZE;

    for (int t = 0; t < tiles; t++) {
        // 协作加载 A tile
        int a_col = t * TILE_SIZE + threadIdx.x;
        As[threadIdx.y][threadIdx.x] = (row < M && a_col < K) ? A[row * K + a_col] : 0.0f;

        // 协作加载 B tile
        int b_row = t * TILE_SIZE + threadIdx.y;
        Bs[threadIdx.y][threadIdx.x] = (b_row < K && col < N) ? B[b_row * N + col] : 0.0f;

        __syncthreads();

        for (int k = 0; k < TILE_SIZE; k++)
            sum += As[threadIdx.y][k] * Bs[k][threadIdx.x];

        __syncthreads();
    }

    if (row < M && col < N)
        C[row * N + col] = sum;
}
```

### 性能对比

编译运行三个版本，填写下表:

| 版本                | 时间 (ms) | 加速比 | Global Memory 每个元素被读次数 |
| ------------------- | --------- | ------ | ------------------------------ |
| CPU 串行            |           | 1×     | —                              |
| GPU Naive           |           |        | K 次                           |
| GPU Tiled (TILE=16) |           |        | K/16 次                        |
| GPU Tiled (TILE=32) |           |        | K/32 次 (注意 bank conflict!)  |

### 思考

- TILE=32 比 TILE=16 快吗？如果不快，为什么？（提示: bank conflict）
- 如何消除 bank conflict？（提示: `__shared__ float As[TILE][TILE+1]`）

---

## 讲解要点

### 1. CPU 循环 vs GPU Kernel — 思维的转变

- CPU: `for (i=0; i<N; i++) C[i] = A[i] + B[i];` → 按时间顺序，一次一个
- GPU: 去掉 for 循环，用 `tid` 代替 `i` → N 个线程同时执行，按空间铺开
- "CPU 编程 = 写循环，GPU 编程 = 写 kernel + 算索引"

### 2. 线程索引公式是 CUDA 编程最重要的公式

- 1D: `tid = blockIdx.x * blockDim.x + threadIdx.x`
- 2D: `row = blockIdx.y * blockDim.y + threadIdx.y`, `col = blockIdx.x * blockDim.x + threadIdx.x`
- 理解: "我的线程在整个 Grid 中的全局位置 → 我应该处理的数据元素"

### 3. Shared Memory Tiling — 为什么有效？

- Global Memory 延迟 ~600 cycles，Shared Memory 延迟 ~20 cycles (差 30 倍)
- Naive: 每个元素从 Global Memory 读 K 次
- Tiled: 每个元素从 Global Memory 读 1 次（加载进 Shared Memory），然后从 Shared Memory 读 K/TILE 次
- "Tiling 的本质 = 用 Shared Memory 做缓存，减少 Global Memory 访问次数"

### 4. `__syncthreads()` 的双重作用

- 加载后同步: 确保 block 内所有线程都加载完数据再开始计算
- 计算后同步: 确保所有线程都算完再覆盖 Shared Memory
- 放在 if-else 分支内会导致死锁（部分线程永远到不了 barrier）

### 5. 下一步优化方向（课后探索）

- Bank Conflict 消除: `TILE+1` padding
- Vectorized Access: 用 `float4` 一次读 4 个元素
- Occupancy: 调整 block size 让更多 warp 同时驻留在 SM 上
