/*
 * 实验 1: 向量加法 — 第一个 CUDA 程序
 * 对应 PPT 第 30-31 页 [动手 1]
 *
 * 教学要点:
 *   1. Host-Device 模型: CPU 分配显存、拷贝数据、启动 kernel；GPU 执行 kernel
 *   2. 线程索引: tid = blockIdx.x * blockDim.x + threadIdx.x
 *   3. Kernel 异步: Host 代码在 kernel 启动后立即继续，需 cudaDeviceSynchronize()
 *   4. PCIe 传输: H2D + D2H 时间远大于 kernel 执行时间
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <cuda_runtime.h>
#include <sys/time.h>

// CUDA 错误检查宏
#define CUDA_CHECK(call) {                                              \
    cudaError_t err = call;                                             \
    if (err != cudaSuccess) {                                           \
        fprintf(stderr, "CUDA Error at %s:%d: %s\n",                    \
                __FILE__, __LINE__, cudaGetErrorString(err));           \
        exit(1);                                                        \
    }                                                                    \
}

// CPU 版本: 串行循环
void vec_add_cpu(const float *a, const float *b, float *c, int n) {
    for (int i = 0; i < n; i++) {
        c[i] = a[i] + b[i];
    }
}

// GPU 版本: 并行 kernel
// tid = blockIdx.x * blockDim.x + threadIdx.x
// 这个公式把"我是第几个线程"映射到"我应该处理哪个数据元素"
__global__ void vec_add_gpu(const float *a, const float *b, float *c, int n) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
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
    int N = 1 << 24;  // 16M = 16,777,216 元素
    size_t bytes = N * sizeof(float);  // ~64 MB per array

    printf("=========================================\n");
    printf("  实验 1: 向量加法 - CPU vs GPU\n");
    printf("  N = %d (%.1fM), 数据量 = %.0f MB\n", N, N/1e6, bytes*3.0/1e6);
    printf("=========================================\n\n");

    // 分配并初始化 Host 内存
    float *h_a = (float*)malloc(bytes);
    float *h_b = (float*)malloc(bytes);
    float *h_c_cpu = (float*)malloc(bytes);
    float *h_c_gpu = (float*)malloc(bytes);
    for (int i = 0; i < N; i++) {
        h_a[i] = (float)rand() / RAND_MAX;
        h_b[i] = (float)rand() / RAND_MAX;
    }

    // --- CPU 版本 ---
    printf("[CPU] 串行计算 (for 循环) ...\n");
    double cpu_start = get_time();
    vec_add_cpu(h_a, h_b, h_c_cpu, N);
    double cpu_time = (get_time() - cpu_start) * 1000;
    printf("[CPU] 耗时: %.2f ms\n\n", cpu_time);

    // --- GPU 版本 ---
    printf("[GPU] 并行计算 ...\n");

    // 1. 分配 Device 内存
    float *d_a, *d_b, *d_c;
    CUDA_CHECK(cudaMalloc(&d_a, bytes));
    CUDA_CHECK(cudaMalloc(&d_b, bytes));
    CUDA_CHECK(cudaMalloc(&d_c, bytes));

    // 2. 创建 CUDA Event 计时
    cudaEvent_t ev_h2d_start, ev_h2d_stop, ev_k_start, ev_k_stop,
                ev_d2h_start, ev_d2h_stop, ev_total_start, ev_total_stop;
    CUDA_CHECK(cudaEventCreate(&ev_h2d_start));
    CUDA_CHECK(cudaEventCreate(&ev_h2d_stop));
    CUDA_CHECK(cudaEventCreate(&ev_k_start));
    CUDA_CHECK(cudaEventCreate(&ev_k_stop));
    CUDA_CHECK(cudaEventCreate(&ev_d2h_start));
    CUDA_CHECK(cudaEventCreate(&ev_d2h_stop));
    CUDA_CHECK(cudaEventCreate(&ev_total_start));
    CUDA_CHECK(cudaEventCreate(&ev_total_stop));

    CUDA_CHECK(cudaEventRecord(ev_total_start));

    // 3. H2D: Host → Device (PCIe 传输)
    CUDA_CHECK(cudaEventRecord(ev_h2d_start));
    CUDA_CHECK(cudaMemcpy(d_a, h_a, bytes, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_b, h_b, bytes, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaEventRecord(ev_h2d_stop));

    // 4. Kernel 启动
    int threads = 256;
    int blocks  = (N + threads - 1) / threads;
    printf("[GPU] 配置: %d blocks x %d threads = %d 线程\n",
           blocks, threads, blocks * threads);

    CUDA_CHECK(cudaEventRecord(ev_k_start));
    vec_add_gpu<<<blocks, threads>>>(d_a, d_b, d_c, N);
    CUDA_CHECK(cudaEventRecord(ev_k_stop));

    // 5. D2H: Device → Host
    CUDA_CHECK(cudaEventRecord(ev_d2h_start));
    CUDA_CHECK(cudaMemcpy(h_c_gpu, d_c, bytes, cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaEventRecord(ev_d2h_stop));

    CUDA_CHECK(cudaEventRecord(ev_total_stop));
    CUDA_CHECK(cudaEventSynchronize(ev_total_stop));

    // 6. 计时结果
    float ms_h2d, ms_kernel, ms_d2h, ms_total;
    CUDA_CHECK(cudaEventElapsedTime(&ms_h2d, ev_h2d_start, ev_h2d_stop));
    CUDA_CHECK(cudaEventElapsedTime(&ms_kernel, ev_k_start, ev_k_stop));
    CUDA_CHECK(cudaEventElapsedTime(&ms_d2h, ev_d2h_start, ev_d2h_stop));
    CUDA_CHECK(cudaEventElapsedTime(&ms_total, ev_total_start, ev_total_stop));

    printf("\n");
    printf("  H2D (CPU->GPU):    %8.3f ms  (%5.1f%%)\n",
           ms_h2d, ms_h2d / ms_total * 100);
    printf("  Kernel (GPU):      %8.3f ms  (%5.1f%%)\n",
           ms_kernel, ms_kernel / ms_total * 100);
    printf("  D2H (GPU->CPU):    %8.3f ms  (%5.1f%%)\n",
           ms_d2h, ms_d2h / ms_total * 100);
    printf("  --------------------------------\n");
    printf("  总计:              %8.3f ms\n\n", ms_total);

    // 带宽计算
    float gb_read  = (bytes * 2) / 1e9;   // A + B
    float gb_write = bytes / 1e9;          // C
    float bw = (gb_read + gb_write) / (ms_kernel / 1000.0);
    printf("  Kernel 有效带宽: %.1f GB/s\n", bw);
    printf("  加速比 (GPU/CPU): %.1fx\n\n", cpu_time / ms_total);

    // 正确性验证
    int errors = 0;
    for (int i = 0; i < N; i++) {
        if (fabsf(h_c_cpu[i] - h_c_gpu[i]) > 0.001f) errors++;
    }
    if (errors == 0)
        printf("  正确性验证: 通过 (0 / %d errors)\n\n", N);
    else
        printf("  正确性验证: 失败 (%d / %d errors)\n\n", errors, N);

    // 思考题 (对应 PPT 第 30-31 页)
    printf("--- 思考题 (对应 PPT 第 30-31 页) ---\n\n");
    printf("1. 当前数据量 N=16.8M，每个元素需 2 次读 (A,B) + 1 次写 (C)，\n");
    printf("   请计算理论访存量 (bytes)。结合 Kernel 有效带宽 %.0f GB/s，\n", bw);
    printf("   判断当前 kernel 是计算瓶颈还是访存瓶颈。\n");
    printf("   提示: 比较 FLOPs/byte (算术强度) 与 GPU 峰值 FLOPs/Bandwidth\n\n");
    printf("2. 如果 N=1024，GPU 加速比会变大还是变小？修改 N 的值并重新编译\n");
    printf("   运行，验证你的判断。\n");
    printf("   提示: GPU kernel 启动有 ~5-10 us 的固定开销\n\n");
    printf("3. 假设模型推理需要将 200GB 数据通过 PCIe 传给 GPU 做计算。\n");
    printf("   PCIe Gen4 x16 单向带宽 32 GB/s，如果 Kernel 只需 0.1ms：\n");
    printf("   a) 总传输时间是多少？传输占多少比例？\n");
    printf("   b) 这说明 GPU 编程中什么样的工程问题？\n\n");
    printf("4. 线程索引公式 tid = blockIdx.x * blockDim.x + threadIdx.x\n");
    printf("   中，blockDim.x 和 gridDim.x 分别由哪个启动参数决定？\n");
    printf("   如果 N=16.8M 且 threads=128，blocks 数量变为多少？\n");
    printf("   tid 的范围还是 0~N-1 吗？\n\n");

    // 清理
    CUDA_CHECK(cudaFree(d_a)); CUDA_CHECK(cudaFree(d_b)); CUDA_CHECK(cudaFree(d_c));
    free(h_a); free(h_b); free(h_c_cpu); free(h_c_gpu);
    return 0;
}
