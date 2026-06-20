/*
 * 模块2 高级：GPU 内存管理 — CPU↔GPU 带宽测试 (CUDA C 版本)
 *
 * 编译: nvcc -O2 02_dma_bandwidth.cu -o dma_bandwidth
 * 运行: ./dma_bandwidth
 *
 * 测量 pageable (malloc) vs pinned (cudaMallocHost) 的 DMA 传输带宽。
 * 使用 CUDA Events 精确计时，对比 H2D 和 D2H 两个方向。
 */

#include <stdio.h>
#include <stdlib.h>
#include <cuda_runtime.h>

#define CHECK(call) { \
    cudaError_t err = call; \
    if (err != cudaSuccess) { \
        fprintf(stderr, "CUDA error at %s:%d — %s\n", __FILE__, __LINE__, \
                cudaGetErrorString(err)); \
        exit(1); \
    } \
}

// 测试指定大小的 pageable 和 pinned 传输
void test_one(size_t bytes, const char *dir_name,
              cudaMemcpyKind kind, int warmup, int iters) {
    void *h_pageable, *h_pinned, *d_buf;

    // 分配 pageable (普通 malloc)
    h_pageable = malloc(bytes);
    if (!h_pageable) { printf("  malloc(%.1f GB) failed\n", bytes/1e9); return; }

    // 分配 pinned (页锁定)
    CHECK(cudaMallocHost(&h_pinned, bytes));

    // 分配 device 内存
    CHECK(cudaMalloc(&d_buf, bytes));

    cudaEvent_t start, stop;
    CHECK(cudaEventCreate(&start));
    CHECK(cudaEventCreate(&stop));

    // ── Pageable ──
    void *src = (kind == cudaMemcpyHostToDevice) ? h_pageable : d_buf;
    void *dst = (kind == cudaMemcpyHostToDevice) ? d_buf : h_pageable;
    for (int i = 0; i < warmup; i++)
        CHECK(cudaMemcpy(dst, src, bytes, kind));
    CHECK(cudaDeviceSynchronize());

    CHECK(cudaEventRecord(start, 0));
    for (int i = 0; i < iters; i++)
        CHECK(cudaMemcpy(dst, src, bytes, kind));
    CHECK(cudaEventRecord(stop, 0));
    CHECK(cudaEventSynchronize(stop));

    float ms_pageable;
    CHECK(cudaEventElapsedTime(&ms_pageable, start, stop));
    double bw_pageable = (bytes * iters) / (ms_pageable / 1000.0) / 1e9;

    // ── Pinned ──
    src = (kind == cudaMemcpyHostToDevice) ? h_pinned : d_buf;
    dst = (kind == cudaMemcpyHostToDevice) ? d_buf : h_pinned;
    for (int i = 0; i < warmup; i++)
        CHECK(cudaMemcpy(dst, src, bytes, kind));
    CHECK(cudaDeviceSynchronize());

    CHECK(cudaEventRecord(start, 0));
    for (int i = 0; i < iters; i++)
        CHECK(cudaMemcpy(dst, src, bytes, kind));
    CHECK(cudaEventRecord(stop, 0));
    CHECK(cudaEventSynchronize(stop));

    float ms_pinned;
    CHECK(cudaEventElapsedTime(&ms_pinned, start, stop));
    double bw_pinned = (bytes * iters) / (ms_pinned / 1000.0) / 1e9;

    printf("%5.1fGB %4s  %8.2f GB/s  %8.2f GB/s  %6.1fx  +%6.1f GB/s\n",
           bytes / 1e9, dir_name,
           bw_pageable, bw_pinned,
           bw_pinned / bw_pageable, bw_pinned - bw_pageable);

    // 清理
    CHECK(cudaEventDestroy(start));
    CHECK(cudaEventDestroy(stop));
    CHECK(cudaFree(d_buf));
    CHECK(cudaFreeHost(h_pinned));
    free(h_pageable);
}

int main() {
    // 打印 GPU 信息
    int dev;
    CHECK(cudaGetDevice(&dev));
    cudaDeviceProp prop;
    CHECK(cudaGetDeviceProperties(&prop, dev));
    printf("GPU: %s (Compute %d.%d, %d SMs)\n\n",
           prop.name, prop.major, prop.minor,
           prop.multiProcessorCount);

    double sizes_gb[] = {0.5, 1.0, 2.0, 4.0};
    int num_sizes = sizeof(sizes_gb) / sizeof(sizes_gb[0]);
    int warmup = 3, iters = 10;

    printf(" Size    Dir    Pageable      Pinned     Ratio    Pin-page\n");
    printf("-----------------------------------------------------------\n");

    for (int i = 0; i < num_sizes; i++) {
        size_t bytes = (size_t)(sizes_gb[i] * 1024 * 1024 * 1024);
        test_one(bytes, "H2D", cudaMemcpyHostToDevice, warmup, iters);
        test_one(bytes, "D2H", cudaMemcpyDeviceToHost, warmup, iters);
    }
    return 0;
}
