/*
 * 实验 1: 向量加法 — 第一个 CUDA 程序
 * 对应课程: 模块 2 — GPU 硬件架构与 CUDA 编程入门
 * PPT 页码: 第 30-31 页 [动手 1]
 *
 * 目标: 理解 CPU 循环 vs GPU Kernel 的思维差异
 *      理解 Host-Device 模型和线程索引
 */

#include <stdio.h>
#include <stdlib.h>
#include <cuda_runtime.h>
#include <sys/time.h>

// CUDA 错误检查宏
#define CHECK(call) {                                                          \
    cudaError_t err = call;                                                    \
    if (err != cudaSuccess) {                                                  \
        fprintf(stderr, "CUDA error at %s:%d — %s\n",                          \
                __FILE__, __LINE__, cudaGetErrorString(err));                  \
        exit(1);                                                               \
    }                                                                          \
}

// ===== CPU 版本: 串行循环 =====
void vec_add_cpu(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i++) {
        c[i] = a[i] + b[i];
    }
}

// ===== GPU 版本: 并行 Kernel =====
__global__ void vec_add_gpu(float *a, float *b, float *c, int n) {
    // 线程索引 — CUDA 编程最重要的公式
    int tid = blockIdx.x * blockDim.x + threadIdx.x;

    // 边界检查: 线程数可能超过 N
    if (tid < n) {
        c[tid] = a[tid] + b[tid];
    }
}

double get_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec * 1e-6;
}

int main() {
    int N = 1 << 24;  // 16M 元素 = ~64 MB per array
    size_t bytes = N * sizeof(float);

    printf("=========================================\n");
    printf("  实验 1: 向量加法 — CPU vs GPU\n");
    printf("  N = %d (%.1f M 元素)\n", N, N / 1e6);
    printf("=========================================\n\n");

    // ===== 分配 Host 内存 =====
    float *h_a = (float*)malloc(bytes);
    float *h_b = (float*)malloc(bytes);
    float *h_c_cpu = (float*)malloc(bytes);
    float *h_c_gpu = (float*)malloc(bytes);

    // 初始化数据
    for (int i = 0; i < N; i++) {
        h_a[i] = rand() / (float)RAND_MAX;
        h_b[i] = rand() / (float)RAND_MAX;
    }

    // ===== CPU 版本 =====
    printf("[CPU] 串行计算...\n");
    double cpu_start = get_time();
    vec_add_cpu(h_a, h_b, h_c_cpu, N);
    double cpu_elapsed = get_time() - cpu_start;
    printf("[CPU] 耗时: %.3f ms\n\n", cpu_elapsed * 1000);

    // ===== GPU 版本 =====
    printf("[GPU] 并行计算...\n");

    // 1. 在 GPU 上分配显存
    float *d_a, *d_b, *d_c;
    CHECK(cudaMalloc(&d_a, bytes));
    CHECK(cudaMalloc(&d_b, bytes));
    CHECK(cudaMalloc(&d_c, bytes));

    // 2. 创建 CUDA Event 用于 GPU 端精确计时
    cudaEvent_t start_total, stop_total;
    cudaEvent_t start_h2d, stop_h2d;
    cudaEvent_t start_kernel, stop_kernel;
    cudaEvent_t start_d2h, stop_d2h;
    CHECK(cudaEventCreate(&start_total));
    CHECK(cudaEventCreate(&stop_total));
    CHECK(cudaEventCreate(&start_h2d));
    CHECK(cudaEventCreate(&stop_h2d));
    CHECK(cudaEventCreate(&start_kernel));
    CHECK(cudaEventCreate(&stop_kernel));
    CHECK(cudaEventCreate(&start_d2h));
    CHECK(cudaEventCreate(&stop_d2h));

    // 3. 拷贝数据 + 启动 Kernel
    CHECK(cudaEventRecord(start_total));

    CHECK(cudaEventRecord(start_h2d));
    CHECK(cudaMemcpy(d_a, h_a, bytes, cudaMemcpyHostToDevice));
    CHECK(cudaMemcpy(d_b, h_b, bytes, cudaMemcpyHostToDevice));
    CHECK(cudaEventRecord(stop_h2d));

    int threads = 256;
    int blocks = (N + threads - 1) / threads;
    CHECK(cudaEventRecord(start_kernel));
    vec_add_gpu<<<blocks, threads>>>(d_a, d_b, d_c, N);
    CHECK(cudaEventRecord(stop_kernel));

    CHECK(cudaEventRecord(start_d2h));
    CHECK(cudaMemcpy(h_c_gpu, d_c, bytes, cudaMemcpyDeviceToHost));
    CHECK(cudaEventRecord(stop_d2h));

    CHECK(cudaEventRecord(stop_total));
    CHECK(cudaEventSynchronize(stop_total));

    // 4. 输出各阶段时间
    float ms_h2d, ms_kernel, ms_d2h, ms_total;
    CHECK(cudaEventElapsedTime(&ms_h2d, start_h2d, stop_h2d));
    CHECK(cudaEventElapsedTime(&ms_kernel, start_kernel, stop_kernel));
    CHECK(cudaEventElapsedTime(&ms_d2h, start_d2h, stop_d2h));
    CHECK(cudaEventElapsedTime(&ms_total, start_total, stop_total));

    printf("[GPU] H2D 传输:  %.3f ms\n", ms_h2d);
    printf("[GPU] Kernel 执行: %.3f ms\n", ms_kernel);
    printf("[GPU] D2H 传输:  %.3f ms\n", ms_d2h);
    printf("[GPU] 总耗时:    %.3f ms\n", ms_total);
    printf("[GPU] 加速比:    %.1f× (vs CPU)\n\n", cpu_elapsed * 1000 / ms_total);

    // 5. 验证正确性
    int errors = 0;
    for (int i = 0; i < N; i++) {
        if (fabsf(h_c_cpu[i] - h_c_gpu[i]) > 0.001f) errors++;
    }
    printf("正确性验证: %d / %d errors\n", errors, N);

    // 6. 带宽计算
    float gb_read = (bytes * 2) / 1e9;   // A + B
    float gb_write = bytes / 1e9;         // C
    printf("显存带宽: 读取 %.2f GB, 写入 %.2f GB\n", gb_read, gb_write);
    printf("有效带宽: %.1f GB/s\n\n", (gb_read + gb_write) / (ms_kernel / 1000));

    // ===== 思考题 =====
    printf("思考题:\n");
    printf("1. H2D 传输 + Kernel + D2H 各占多少比例?\n");
    printf("2. 如果 N=1024，GPU 还比 CPU 快吗? 为什么?\n");
    printf("3. 有效带宽距离理论带宽 (HBM3 ~3.35 TB/s) 有多远?\n");

    // 清理
    CHECK(cudaFree(d_a));
    CHECK(cudaFree(d_b));
    CHECK(cudaFree(d_c));
    free(h_a); free(h_b); free(h_c_cpu); free(h_c_gpu);
    return 0;
}
