/*
 * 实验 2: 矩阵乘法 — Naive 版本 (仅 Global Memory)
 * 对应课程: 模块 2 — GPU 硬件架构与 CUDA 编程入门
 * PPT 页码: 第 33-34 页 [动手 2]
 *
 * 目标: 理解 2D 线程索引、带宽瓶颈分析、Arithmetic Intensity
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
#define BLOCK_SIZE 16

__global__ void matmul_naive(float *A, float *B, float *C) {
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
    printf("=========================================\n");
    printf("  实验 2: 矩阵乘法 — Naive (Global Memory)\n");
    printf("  M=%d, N=%d, K=%d\n", M, N, K);
    printf("=========================================\n\n");

    size_t bytes_A = M * K * sizeof(float);
    size_t bytes_B = K * N * sizeof(float);
    size_t bytes_C = M * N * sizeof(float);

    // 分配 Host 内存
    float *h_A = (float*)malloc(bytes_A);
    float *h_B = (float*)malloc(bytes_B);
    float *h_C = (float*)malloc(bytes_C);

    // 随机初始化
    for (int i = 0; i < M * K; i++) h_A[i] = (float)rand() / RAND_MAX;
    for (int i = 0; i < K * N; i++) h_B[i] = (float)rand() / RAND_MAX;

    // 分配 Device 内存
    float *d_A, *d_B, *d_C;
    CHECK(cudaMalloc(&d_A, bytes_A));
    CHECK(cudaMalloc(&d_B, bytes_B));
    CHECK(cudaMalloc(&d_C, bytes_C));

    // 拷贝到 Device
    CHECK(cudaMemcpy(d_A, h_A, bytes_A, cudaMemcpyHostToDevice));
    CHECK(cudaMemcpy(d_B, h_B, bytes_B, cudaMemcpyHostToDevice));

    dim3 block(BLOCK_SIZE, BLOCK_SIZE);
    dim3 grid((N + BLOCK_SIZE - 1) / BLOCK_SIZE,
              (M + BLOCK_SIZE - 1) / BLOCK_SIZE);

    // Kernel 执行计时
    cudaEvent_t start, stop;
    CHECK(cudaEventCreate(&start));
    CHECK(cudaEventCreate(&stop));
    CHECK(cudaEventRecord(start));

    matmul_naive<<<grid, block>>>(d_A, d_B, d_C);

    CHECK(cudaEventRecord(stop));
    CHECK(cudaEventSynchronize(stop));
    float ms;
    CHECK(cudaEventElapsedTime(&ms, start, stop));

    // 取回结果
    CHECK(cudaMemcpy(h_C, d_C, bytes_C, cudaMemcpyDeviceToHost));

    // 性能分析
    double flops = 2.0 * M * N * K;  // 乘 + 加
    double gflops = flops / (ms / 1000.0) / 1e9;
    double bytes_transferred = (M * K + K * N + M * N) * sizeof(float);
    double ai = flops / bytes_transferred;  // Arithmetic Intensity

    printf("[Naive] 耗时:           %.3f ms\n", ms);
    printf("[Naive] 性能:           %.1f GFLOPS\n", gflops);
    printf("[Naive] Arithmetic Intensity: %.1f FLOPs/byte\n", ai);
    printf("[Naive] 每个元素从 Global Memory 被读取次数: ~%d 次\n", K);
    printf("\n");

    // 瓶颈分析
    printf("瓶颈分析:\n");
    printf("  向量加法的 AI: 0.083 FLOPs/byte → 带宽瓶颈\n");
    printf("  矩阵乘法 naive 的 AI: %.1f FLOPs/byte\n", ai);
    printf("  → 如果 AI < GPU 峰值 FLOPs/Bandwidth，则是带宽瓶颈\n");
    printf("  → 下一步: 用 Shared Memory 减少 Global Memory 访问\n");

    // 清理
    CHECK(cudaFree(d_A));
    CHECK(cudaFree(d_B));
    CHECK(cudaFree(d_C));
    free(h_A); free(h_B); free(h_C);

    return 0;
}
