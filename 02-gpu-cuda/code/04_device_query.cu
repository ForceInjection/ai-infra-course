/*
 * GPU 设备查询 — 查看硬件参数
 * 对应课程: 模块 2 — GPU 硬件架构与 CUDA 编程入门
 * 用途: 查询 GPU 的硬件规格、计算能力、内存信息
 */

#include <stdio.h>
#include <cuda_runtime.h>

int main() {
    int deviceCount;
    cudaGetDeviceCount(&deviceCount);

    printf("=========================================\n");
    printf("  GPU 设备查询\n");
    printf("  检测到 %d 个 CUDA 设备\n", deviceCount);
    printf("=========================================\n\n");

    for (int i = 0; i < deviceCount; i++) {
        cudaDeviceProp prop;
        cudaGetDeviceProperties(&prop, i);

        printf("=== GPU %d: %s ===\n", i, prop.name);
        printf("\n");

        // 计算能力
        printf("  计算能力:         %d.%d\n", prop.major, prop.minor);

        // SM 和核心
        printf("  SM 数量:          %d\n", prop.multiProcessorCount);
        printf("  CUDA Cores (估算): %d (每个 SM 64 FP32 + 64 INT32 cores (A100 = 6912 total))\n",
               prop.multiProcessorCount * 128);

        // 线程限制
        printf("  Warp Size:        %d\n", prop.warpSize);
        printf("  Max Threads/Block: %d\n", prop.maxThreadsPerBlock);
        printf("  Max Threads/SM:   %d\n", prop.maxThreadsPerMultiProcessor);
        printf("  Max Blocks/SM:    %d\n",
               prop.maxThreadsPerMultiProcessor / prop.maxThreadsPerBlock);

        // 内存
        printf("\n  --- 内存 ---\n");
        printf("  Global Memory:    %.1f GB\n",
               prop.totalGlobalMem / 1024.0 / 1024.0 / 1024.0);
        printf("  Shared Memory/Block: %zu KB\n",
               prop.sharedMemPerBlock / 1024);
        printf("  Registers/Block:  %d\n", prop.regsPerBlock);
        printf("  L2 Cache:         %.1f MB\n",
               prop.l2CacheSize / 1024.0 / 1024.0);

        // 显存带宽计算
        float bw_gb_s = 2.0f * prop.memoryClockRate * (prop.memoryBusWidth / 8) / 1.0e6;
        printf("  Memory Clock:     %.0f MHz\n", prop.memoryClockRate / 1000.0);
        printf("  Memory Bus Width: %d-bit\n", prop.memoryBusWidth);
        printf("  理论带宽:         %.1f GB/s\n", bw_gb_s);

        // 时钟频率
        printf("\n  --- 时钟 ---\n");
        printf("  GPU Clock:        %.0f MHz\n", prop.clockRate / 1000.0);

        // 理论 FP32 峰值 = CUDA Cores × 频率(GHz) × 2 (FMA)
        int cuda_cores = prop.multiProcessorCount * 128;
        float peak_fp32_tflops = cuda_cores * (prop.clockRate / 1.0e6) * 2.0 / 1000.0;
        printf("\n  理论 FP32 峰值:   %.1f TFLOPS\n", peak_fp32_tflops);
        printf("  理论带宽/峰值比:  %.2f (FLOPs/byte — Roofline Ridge Point)\n",
               peak_fp32_tflops * 1000.0 / bw_gb_s);

        printf("\n");
    }

    // 对 A100 的特殊说明
    printf("=========================================\n");
    printf("  A100 关键特性 (本机为 8×A100-SXM4-80GB):\n");
    printf("  - SM: 108/GPU\n");
    printf("  - CUDA Cores: 6912/GPU\n");
    printf("  - Tensor Cores: 432/GPU (第3代)\n");
    printf("  - HBM2e: 80 GB, 带宽 2.0 TB/s\n");
    printf("  - NVLink 3.0: 600 GB/s 双向\n");
    printf("  - MIG: 支持 (最多 7 个实例)\n");
    printf("=========================================\n");

    return 0;
}
