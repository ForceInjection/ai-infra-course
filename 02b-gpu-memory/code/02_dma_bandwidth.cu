/*
 * 模块 2b: GPU 内存管理 — CPU↔GPU DMA 带宽测试 (CUDA C 版本)
 *
 * 编译: nvcc -O2 02_dma_bandwidth.cu -o dma_bandwidth
 * 运行: ./dma_bandwidth
 *
 * 教学要点:
 *   1. Pinned (cudaMallocHost) vs Pageable (malloc): DMA 传输路径不同
 *   2. Pageable: 每次 cudaMemcpy 需内核遍历页表 → lock 页面 → scatter-gather
 *   3. Pinned: 页面预先锁定，DMA 引擎直传物理地址 → 跳过一次页表遍历
 *   4. 结果: pinned 比 pageable 快 2-3× (PCIe 越快，差距越大)
 */

#include <stdio.h>
#include <stdlib.h>
#include <cuda_runtime.h>

#define CUDA_CHECK(call) {                                              \
    cudaError_t err = call;                                             \
    if (err != cudaSuccess) {                                           \
        fprintf(stderr, "CUDA Error at %s:%d: %s\n",                    \
                __FILE__, __LINE__, cudaGetErrorString(err));           \
        exit(1);                                                        \
    }                                                                    \
}

void test_one(double size_gb, size_t bytes, const char *dir_name,
              cudaMemcpyKind kind, int warmup, int iters) {
    void *h_pageable, *h_pinned, *d_buf;

    // Pageable: 普通 malloc，页面可能被换出，每次 DMA 需页表遍历
    h_pageable = malloc(bytes);
    if (!h_pageable) { printf("  malloc(%.1f GB) failed\n", bytes/1e9); return; }

    // Pinned: cudaMallocHost 锁定的页面，DMA 引擎直传
    CUDA_CHECK(cudaMallocHost(&h_pinned, bytes));
    CUDA_CHECK(cudaMalloc(&d_buf, bytes));

    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));

    // --- Pageable ---
    void *src = (kind == cudaMemcpyHostToDevice) ? h_pageable : d_buf;
    void *dst = (kind == cudaMemcpyHostToDevice) ? d_buf : h_pageable;
    for (int i = 0; i < warmup; i++)
        CUDA_CHECK(cudaMemcpy(dst, src, bytes, kind));
    CUDA_CHECK(cudaDeviceSynchronize());

    CUDA_CHECK(cudaEventRecord(start, 0));
    for (int i = 0; i < iters; i++)
        CUDA_CHECK(cudaMemcpy(dst, src, bytes, kind));
    CUDA_CHECK(cudaEventRecord(stop, 0));
    CUDA_CHECK(cudaEventSynchronize(stop));

    float ms_pageable;
    CUDA_CHECK(cudaEventElapsedTime(&ms_pageable, start, stop));
    double bw_pageable = (bytes * iters) / (ms_pageable / 1000.0) / 1e9;

    // --- Pinned ---
    src = (kind == cudaMemcpyHostToDevice) ? h_pinned : d_buf;
    dst = (kind == cudaMemcpyHostToDevice) ? d_buf : h_pinned;
    for (int i = 0; i < warmup; i++)
        CUDA_CHECK(cudaMemcpy(dst, src, bytes, kind));
    CUDA_CHECK(cudaDeviceSynchronize());

    CUDA_CHECK(cudaEventRecord(start, 0));
    for (int i = 0; i < iters; i++)
        CUDA_CHECK(cudaMemcpy(dst, src, bytes, kind));
    CUDA_CHECK(cudaEventRecord(stop, 0));
    CUDA_CHECK(cudaEventSynchronize(stop));

    float ms_pinned;
    CUDA_CHECK(cudaEventElapsedTime(&ms_pinned, start, stop));
    double bw_pinned = (bytes * iters) / (ms_pinned / 1000.0) / 1e9;

    double ratio = bw_pinned / bw_pageable;
    printf("  %4.1f GB  %-4s  %8.2f GB/s  %8.2f GB/s   %5.1fx   +%6.1f GB/s\n",
           size_gb, dir_name,
           bw_pageable, bw_pinned, ratio, bw_pinned - bw_pageable);

    CUDA_CHECK(cudaEventDestroy(start));
    CUDA_CHECK(cudaEventDestroy(stop));
    CUDA_CHECK(cudaFree(d_buf));
    CUDA_CHECK(cudaFreeHost(h_pinned));
    free(h_pageable);
}

int main() {
    int dev;
    CUDA_CHECK(cudaGetDevice(&dev));
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, dev));

    printf("===========================================================\n");
    printf("  CPU-GPU DMA Bandwidth Test (pageable vs pinned)\n");
    printf("  GPU: %s (Compute %d.%d, %d SMs)\n",
           prop.name, prop.major, prop.minor, prop.multiProcessorCount);
    printf("===========================================================\n\n");

    double sizes_gb[] = {0.5, 1.0, 2.0, 4.0};
    int num_sizes = sizeof(sizes_gb) / sizeof(sizes_gb[0]);
    int warmup = 3, iters = 10;

    printf("  Size     Dir   Pageable      Pinned     Ratio    Pin-page\n");
    printf("  ---------------------------------------------------------\n");

    for (int i = 0; i < num_sizes; i++) {
        size_t bytes = (size_t)(sizes_gb[i] * 1024 * 1024 * 1024);
        test_one(sizes_gb[i], bytes, "H2D", cudaMemcpyHostToDevice, warmup, iters);
        test_one(sizes_gb[i], bytes, "D2H", cudaMemcpyDeviceToHost, warmup, iters);
    }

    printf("\n");
    printf("--- 思考题 ---\n");
    printf("1. 为什么 Pinned 比 Pageable 快？\n");
    printf("   -> Pageable 每次 cudaMemcpy 都要遍历页表、逐页锁定\n");
    printf("   -> Pinned (cudaMallocHost) 预先锁定，DMA 引擎直传物理地址\n\n");
    printf("2. 为什么 D2H 比 H2D 慢？\n");
    printf("   -> D2H 时 CPU 端需要将数据写入 pageable buffer（页表遍历）\n");
    printf("   -> 或等待 pinned buffer 的 DMA 完成（总线仲裁开销）\n\n");
    printf("3. Pinned 内存的代价是什么？\n");
    printf("   -> 占用物理页面，不能 swap；分配过多会导致系统内存不足\n");
    printf("   -> 建议 pinned 内存总量 < 物理内存的 50%%\n\n");
    printf("4. 这和 vLLM 的 KV Cache 有什么关系？\n");
    printf("   -> KV Cache 在 GPU HBM 中，不需要 H2D/D2H（已在 Device 端）\n");
    printf("   -> 但模型权重加载时，pinned memory 可以加速 CPU→GPU 传输\n");

    return 0;
}
