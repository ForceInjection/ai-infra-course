/*
 * 实验 3: 矩阵乘法 — Tiled 版本 (Shared Memory 优化)
 * 对应 PPT 第 36 页 [动手 2]
 *
 * 教学要点:
 *   1. Shared Memory Tiling: 分块协作加载, 减少 Global Memory 访问
 *   2. __syncthreads(): Block 内线程同步 barrier
 *   3. Arithmetic Intensity (AI): FLOPs / Bytes, 判断瓶颈是计算还是带宽
 *   4. Bank Conflict: Shared Memory 的 32 个 bank 同时访问冲突
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <cuda_runtime.h>

#define CUDA_CHECK(call) {                                              \
    cudaError_t err = call;                                             \
    if (err != cudaSuccess) {                                           \
        fprintf(stderr, "CUDA Error at %s:%d: %s\n",                    \
                __FILE__, __LINE__, cudaGetErrorString(err));           \
        exit(1);                                                        \
    }                                                                    \
}

#define M 1024
#define N 1024
#define K 1024
#define TILE_SIZE 16

// --- Tiled 矩阵乘法 (Shared Memory) ---
//
// 核心思想: 把 A、B 切分为 TILE_SIZE × TILE_SIZE 的小块(tile)。
//   Block 内所有线程协作, 每次把一个 tile 从 Global Memory 加载到 Shared Memory,
//   然后从 Shared Memory 反复读取做乘加运算, 处理完后再加载下一个 tile。
//
// 为什么快? Shared Memory ~20 cycles vs Global Memory (HBM) ~600 cycles (参考 PPT 第 12 页延迟金字塔)
// 为什么 __syncthreads() 要两次? 第一次等所有线程加载完 tile, 第二次等所有线程算完再加载下一个 tile
//
__global__ void matmul_tiled(const float *A, const float *B, float *C) {
    int row = blockIdx.y * TILE_SIZE + threadIdx.y;
    int col = blockIdx.x * TILE_SIZE + threadIdx.x;

    // Block 内所有线程共享的 on-chip SRAM
    __shared__ float As[TILE_SIZE][TILE_SIZE];
    __shared__ float Bs[TILE_SIZE][TILE_SIZE];

    float sum = 0.0f;
    int tiles = (K + TILE_SIZE - 1) / TILE_SIZE;

    for (int t = 0; t < tiles; t++) {
        // 协作加载 A 的当前 tile: 每个线程加载一个元素
        int a_col = t * TILE_SIZE + threadIdx.x;
        As[threadIdx.y][threadIdx.x] = (row < M && a_col < K)
            ? A[row * K + a_col] : 0.0f;

        // 协作加载 B 的当前 tile
        int b_row = t * TILE_SIZE + threadIdx.y;
        Bs[threadIdx.y][threadIdx.x] = (b_row < K && col < N)
            ? B[b_row * N + col] : 0.0f;

        // barrier: 所有线程都加载完才能开始计算
        __syncthreads();

        // 从 Shared Memory 读取做乘加
        for (int k = 0; k < TILE_SIZE; k++) {
            sum += As[threadIdx.y][k] * Bs[k][threadIdx.x];
        }

        // barrier: 所有线程都算完才能加载下一个 tile
        __syncthreads();
    }

    if (row < M && col < N)
        C[row * N + col] = sum;
}

// --- Naive 矩阵乘法 (仅 Global Memory, 作为对比基准) ---
// 每个线程直接从 HBM 读取 A 的一整行和 B 的一整列
// 问题: 每个 A[row][k] 被不同线程重复读取 — 没有数据复用
__global__ void matmul_naive(const float *A, const float *B, float *C) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < M && col < N) {
        float sum = 0.0f;
        for (int k = 0; k < K; k++) {
            sum += A[row * K + k] * B[k * N + col];
        }
        C[row * N + col] = sum;
    }
}

int main() {
    printf("===========================================================\n");
    printf("  实验 3: 矩阵乘法 - Naive vs Tiled (Shared Memory)\n");
    printf("  M=%d, N=%d, K=%d, TILE_SIZE=%d\n", M, N, K, TILE_SIZE);
    printf("===========================================================\n\n");

    size_t bytes_A = M * K * sizeof(float);
    size_t bytes_B = K * N * sizeof(float);
    size_t bytes_C = M * N * sizeof(float);

    printf("  矩阵大小: A[%d x %d] = %.1f MB, B[%d x %d] = %.1f MB, C[%d x %d] = %.1f MB\n\n",
           M, K, bytes_A/1e6, K, N, bytes_B/1e6, M, N, bytes_C/1e6);

    // 分配 Host 内存并初始化
    float *h_A = (float*)malloc(bytes_A);
    float *h_B = (float*)malloc(bytes_B);
    float *h_C_naive = (float*)malloc(bytes_C);
    float *h_C_tiled = (float*)malloc(bytes_C);
    for (int i = 0; i < M * K; i++) h_A[i] = (float)rand() / RAND_MAX;
    for (int i = 0; i < K * N; i++) h_B[i] = (float)rand() / RAND_MAX;

    // 分配 Device 内存并拷贝
    float *d_A, *d_B, *d_C;
    CUDA_CHECK(cudaMalloc(&d_A, bytes_A));
    CUDA_CHECK(cudaMalloc(&d_B, bytes_B));
    CUDA_CHECK(cudaMalloc(&d_C, bytes_C));
    CUDA_CHECK(cudaMemcpy(d_A, h_A, bytes_A, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_B, h_B, bytes_B, cudaMemcpyHostToDevice));

    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));

    // --- Naive 版本 ---
    printf("[1] Naive 版本 (仅 Global Memory)\n");
    dim3 block(16, 16);
    dim3 grid((N + 15) / 16, (M + 15) / 16);

    CUDA_CHECK(cudaEventRecord(start));
    matmul_naive<<<grid, block>>>(d_A, d_B, d_C);
    CUDA_CHECK(cudaEventRecord(stop));
    CUDA_CHECK(cudaEventSynchronize(stop));

    float ms_naive;
    CUDA_CHECK(cudaEventElapsedTime(&ms_naive, start, stop));
    CUDA_CHECK(cudaMemcpy(h_C_naive, d_C, bytes_C, cudaMemcpyDeviceToHost));

    double gflops_naive = (2.0 * M * N * K) / (ms_naive / 1000.0) / 1e9;
    double bytes_read_naive = (double)M * N * K * 2 * sizeof(float);
    double ai_naive = (2.0 * M * N * K) / bytes_read_naive;

    printf("  耗时: %.3f ms, 性能: %.1f GFLOPS\n", ms_naive, gflops_naive);
    printf("  AI (Arithmetic Intensity): %.1f FLOPs/byte\n", ai_naive);
    printf("  每个 K 维元素被 %d 个线程各读一次, 共 ~%d 次 Global Memory 读取\n\n",
           K, K);

    // --- Tiled 版本 ---
    printf("[2] Tiled 版本 (Shared Memory, TILE=%d)\n", TILE_SIZE);

    dim3 block_t(TILE_SIZE, TILE_SIZE);
    dim3 grid_t((N + TILE_SIZE - 1) / TILE_SIZE,
                (M + TILE_SIZE - 1) / TILE_SIZE);

    CUDA_CHECK(cudaEventRecord(start));
    matmul_tiled<<<grid_t, block_t>>>(d_A, d_B, d_C);
    CUDA_CHECK(cudaEventRecord(stop));
    CUDA_CHECK(cudaEventSynchronize(stop));

    float ms_tiled;
    CUDA_CHECK(cudaEventElapsedTime(&ms_tiled, start, stop));
    CUDA_CHECK(cudaMemcpy(h_C_tiled, d_C, bytes_C, cudaMemcpyDeviceToHost));

    double gflops_tiled = (2.0 * M * N * K) / (ms_tiled / 1000.0) / 1e9;
    double bytes_read_tiled = (double)(M * K + K * N) * sizeof(float);
    double ai_tiled = (2.0 * M * N * K) / bytes_read_tiled;

    printf("  耗时: %.3f ms, 性能: %.1f GFLOPS\n", ms_tiled, gflops_tiled);
    printf("  AI (Arithmetic Intensity): %.1f FLOPs/byte\n", ai_tiled);
    printf("  Global Memory 读取: A 和 B 各一次 (协作加载), 每个元素仅读 ~1 次\n\n");

    // --- 性能对比 ---
    printf("--- 性能对比 ---\n");
    printf("  Naive (Global Mem):  %8.3f ms, %8.1f GFLOPS\n", ms_naive, gflops_naive);
    printf("  Tiled (Shared Mem):  %8.3f ms, %8.1f GFLOPS\n", ms_tiled, gflops_tiled);
    printf("  加速比: %.1fx\n\n", ms_naive / ms_tiled);

    // --- 正确性 ---
    float max_err = 0.0f;
    for (int i = 0; i < M * N; i++) {
        float e = fabsf(h_C_naive[i] - h_C_tiled[i]);
        if (e > max_err) max_err = e;
    }
    if (max_err < 0.01f)
        printf("  正确性验证: 通过 (最大误差: %.6f)\n\n", max_err);
    else
        printf("  正确性验证: 失败 (最大误差: %.6f)\n\n", max_err);

    // --- Shared Memory 与 Bank Conflict ---
    printf("--- Shared Memory 与 Bank Conflict (参考 PPT 第 15 页: SM 内部结构) ---\n");
    int shared_bytes = 2 * TILE_SIZE * TILE_SIZE * sizeof(float);
    printf("  Shared Memory 使用: %d bytes/block (2 tiles x %d x %d floats)\n",
           shared_bytes, TILE_SIZE, TILE_SIZE);
    printf("  Bank Conflict: TILE=%d 时 Bs 列访问 stride=%d bytes -> %d-way conflict\n",
           TILE_SIZE, TILE_SIZE * (int)sizeof(float),
           TILE_SIZE * (int)sizeof(float) / 4);
    printf("  解决方案: __shared__ float Bs[TILE_SIZE][TILE_SIZE+1] (+1 列 padding)\n\n");

    // --- 思考题 (对应 PPT 第 33-36 页) ---
    printf("--- 思考题 ---\n");
    printf("1. Tiled 版本为什么比 Naive 快?\n");
    printf("   -> 对比 Global Memory 读取次数: Naive ~K 次/元素 vs Tiled ~1 次/元素\n");
    printf("   -> Shared Memory 延迟 ~20 cycles vs HBM ~600 cycles (PPT 第 12 页)\n\n");
    printf("2. TILE_SIZE 取多少最合适?\n");
    printf("   -> 每个 SM 的 Shared Memory 上限 48 KB (H100), 当前只用 2 KB\n");
    printf("   -> 尝试 TILE_SIZE=8 和 TILE_SIZE=32, 观察性能和 bank conflict 变化\n\n");
    printf("3. 理论峰值 ~67 TFLOPS (H100 FP32), 我们只做到 ~7 TFLOPS, 差距在哪?\n");
    printf("   -> 16-way bank conflict 吃掉了一部分性能\n");
    printf("   -> 还可以用 vectorized load (float4), double buffering 继续优化\n\n");
    printf("4. 什么时候 GPU 比 CPU 快?\n");
    printf("   -> AI > GPU 峰值 FLOPs/Bandwidth 时是计算瓶颈 (如矩阵乘法)\n");
    printf("   -> AI < GPU 峰值 FLOPs/Bandwidth 时是带宽瓶颈 (如向量加法)\n");
    printf("   -> H100 的 Roofline Ridge Point: 19.96 FLOPs/byte (来自 device_query)\n\n");

    CUDA_CHECK(cudaFree(d_A)); CUDA_CHECK(cudaFree(d_B)); CUDA_CHECK(cudaFree(d_C));
    free(h_A); free(h_B); free(h_C_naive); free(h_C_tiled);
    return 0;
}
