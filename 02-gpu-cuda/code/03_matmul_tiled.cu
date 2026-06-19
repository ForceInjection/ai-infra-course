/*
 * 实验 3: 矩阵乘法 — Tiled 版本 (Shared Memory 优化)
 * 对应课程: 模块 2 — GPU 硬件架构与 CUDA 编程入门
 * PPT 页码: 第 36 页 [动手 2]
 *
 * 目标: 理解 Shared Memory Tiling、__syncthreads()、Bank Conflict
 */

#include <stdio.h>
#include <stdlib.h>
#include <cuda_runtime.h>

#define CHECK(call) {                                                          \
    cudaError_t err = call;                                                    \
    if (err != cudaSuccess) {                                                  \
        fprintf(stderr, "CUDA error at %s:%d — %s\n",                          \
                __FILE__, __LINE__, cudaGetErrorString(err));                  \
        exit(1);                                                               \
    }                                                                          \
}

#define M 1024
#define N 1024
#define K 1024
#define TILE_SIZE 16  // 可改为 8, 16, 32 测试 bank conflict

// ===== Tiled 版本: 使用 Shared Memory 缓存 tile =====
__global__ void matmul_tiled(float *A, float *B, float *C) {
    int row = blockIdx.y * TILE_SIZE + threadIdx.y;
    int col = blockIdx.x * TILE_SIZE + threadIdx.x;

    // Shared Memory: Block 内所有线程共享
    // 加 padding (+1) 可消除 TILE=32 时的 bank conflict
    __shared__ float As[TILE_SIZE][TILE_SIZE];
    __shared__ float Bs[TILE_SIZE][TILE_SIZE];

    float sum = 0.0f;
    int tiles = (K + TILE_SIZE - 1) / TILE_SIZE;

    for (int t = 0; t < tiles; t++) {
        // === 协作加载 A tile ===
        int a_col = t * TILE_SIZE + threadIdx.x;
        if (row < M && a_col < K)
            As[threadIdx.y][threadIdx.x] = A[row * K + a_col];
        else
            As[threadIdx.y][threadIdx.x] = 0.0f;

        // === 协作加载 B tile ===
        int b_row = t * TILE_SIZE + threadIdx.y;
        if (b_row < K && col < N)
            Bs[threadIdx.y][threadIdx.x] = B[b_row * N + col];
        else
            Bs[threadIdx.y][threadIdx.x] = 0.0f;

        // === 同步: 确保 tile 加载完再计算 ===
        __syncthreads();

        // === 从 Shared Memory 读取做乘加 ===
        for (int k = 0; k < TILE_SIZE; k++) {
            sum += As[threadIdx.y][k] * Bs[k][threadIdx.x];
        }

        // === 同步: 确保所有线程算完再加载下一个 tile ===
        __syncthreads();
    }

    if (row < M && col < N)
        C[row * N + col] = sum;
}

// ===== 先运行 naive 版本做对比 =====
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
    printf("=========================================\n");
    printf("  实验 3: 矩阵乘法 — Tiled (Shared Memory)\n");
    printf("  M=%d, N=%d, K=%d, TILE_SIZE=%d\n", M, N, K, TILE_SIZE);
    printf("=========================================\n\n");

    size_t bytes_A = M * K * sizeof(float);
    size_t bytes_B = K * N * sizeof(float);
    size_t bytes_C = M * N * sizeof(float);

    float *h_A = (float*)malloc(bytes_A);
    float *h_B = (float*)malloc(bytes_B);
    float *h_C_naive = (float*)malloc(bytes_C);
    float *h_C_tiled = (float*)malloc(bytes_C);

    for (int i = 0; i < M * K; i++) h_A[i] = (float)rand() / RAND_MAX;
    for (int i = 0; i < K * N; i++) h_B[i] = (float)rand() / RAND_MAX;

    float *d_A, *d_B, *d_C;
    CHECK(cudaMalloc(&d_A, bytes_A));
    CHECK(cudaMalloc(&d_B, bytes_B));
    CHECK(cudaMalloc(&d_C, bytes_C));
    CHECK(cudaMemcpy(d_A, h_A, bytes_A, cudaMemcpyHostToDevice));
    CHECK(cudaMemcpy(d_B, h_B, bytes_B, cudaMemcpyHostToDevice));

    cudaEvent_t start, stop;
    CHECK(cudaEventCreate(&start));
    CHECK(cudaEventCreate(&stop));

    // === Naive 版本 ===
    dim3 block(16, 16);  // reuse BLOCK_SIZE=16
    dim3 grid((N + 15) / 16, (M + 15) / 16);

    CHECK(cudaEventRecord(start));
    matmul_naive<<<grid, block>>>(d_A, d_B, d_C);
    CHECK(cudaEventRecord(stop));
    CHECK(cudaEventSynchronize(stop));
    float ms_naive;
    CHECK(cudaEventElapsedTime(&ms_naive, start, stop));
    CHECK(cudaMemcpy(h_C_naive, d_C, bytes_C, cudaMemcpyDeviceToHost));
    double gflops_naive = (2.0 * M * N * K) / (ms_naive / 1000.0) / 1e9;

    // === Tiled 版本 ===
    dim3 block_t(TILE_SIZE, TILE_SIZE);
    dim3 grid_t((N + TILE_SIZE - 1) / TILE_SIZE, (M + TILE_SIZE - 1) / TILE_SIZE);

    CHECK(cudaEventRecord(start));
    matmul_tiled<<<grid_t, block_t>>>(d_A, d_B, d_C);
    CHECK(cudaEventRecord(stop));
    CHECK(cudaEventSynchronize(stop));
    float ms_tiled;
    CHECK(cudaEventElapsedTime(&ms_tiled, start, stop));
    CHECK(cudaMemcpy(h_C_tiled, d_C, bytes_C, cudaMemcpyDeviceToHost));
    double gflops_tiled = (2.0 * M * N * K) / (ms_tiled / 1000.0) / 1e9;

    // === 结果 ===
    printf("%-20s %12s %15s %20s\n", "版本", "耗时(ms)", "GFLOPS", "Global Memory 访问");
    printf("----------------------------------------------------------------------\n");
    printf("%-20s %12.3f %15.1f %20s\n", "Naive (Global Mem)", ms_naive, gflops_naive, "每元素 ~K 次");
    printf("%-20s %12.3f %15.1f %20s\n",
           "Tiled (Shared Mem)", ms_tiled, gflops_tiled, "每元素 ~K/TILE 次");
    printf("\n");
    printf("加速比: %.1f×\n\n", ms_naive / ms_tiled);

    // 验证正确性
    int errors = 0;
    for (int i = 0; i < M * N; i++) {
        if (fabsf(h_C_naive[i] - h_C_tiled[i]) > 0.01f) errors++;
    }
    printf("正确性验证: %d / %d errors\n\n", errors, M * N);

    // === Shared Memory 和 Bank Conflict 分析 ===
    int shared_per_block = 2 * TILE_SIZE * TILE_SIZE * sizeof(float);
    printf("Shared Memory 使用: %d bytes/block (2 tiles × %d×%d floats)\n",
           shared_per_block, TILE_SIZE, TILE_SIZE);
    printf("Bank Conflict 分析:\n");
    printf("  TILE=%d: Bs 的列访问 stride = %d bytes → %d-way bank conflict\n",
           TILE_SIZE, TILE_SIZE * (int)sizeof(float),
           (TILE_SIZE * (int)sizeof(float) / 4));
    printf("  解决方案: __shared__ float Bs[TILE_SIZE][TILE_SIZE+1]\n");

    CHECK(cudaFree(d_A)); CHECK(cudaFree(d_B)); CHECK(cudaFree(d_C));
    free(h_A); free(h_B); free(h_C_naive); free(h_C_tiled);
    return 0;
}
