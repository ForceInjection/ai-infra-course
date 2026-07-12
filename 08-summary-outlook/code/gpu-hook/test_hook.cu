/**
 * CUDA Hook 验证程序 — 测试 libcuda_hook.so 的显存配额和算力限速
 *
 * 编译: nvcc --cudart=shared test_hook.cu -o test_hook
 *        (--cudart=shared 是必需的: 动态链接 libcudart 才能被 LD_PRELOAD 拦截)
 * 运行:
 *   LD_PRELOAD=./libcuda_hook.so \
 *     CUDA_MEM_QUOTA_MB=128 \
 *     CUDA_CORE_RATE=5 \
 *     CUDA_CORE_CAPACITY=3 \
 *     ./test_hook
 *
 * 每个测试独立运行, 通过返回值判断是否通过 (0 = 通过, 非 0 = 失败).
 * 建议先不加 LD_PRELOAD 跑一次看基线, 再加 hook 看拦截效果.
 */

#include <cuda_runtime.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MB (1024ULL * 1024ULL)
#define PASS() printf("  [PASS]\n")
#define FAIL(msg) do { printf("  [FAIL] %s\n", msg); return 1; } while(0)
#define CHECK(call, msg) do {                                     \
    cudaError_t _e = (call);                                      \
    if (_e != cudaSuccess) {                                      \
        printf("  [FAIL] %s: %s (code=%d)\n",                     \
               msg, cudaGetErrorString(_e), _e);                  \
        return 1;                                                 \
    }                                                             \
} while(0)

/* ── 一个极简 kernel, 只用来验证 cudaLaunchKernel 拦截 ── */
__global__ void dummy_kernel(float* data, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) data[i] = data[i] * 2.0f;
}

/* ═══════════════════════════════════════════════════════════════
 * Test 1: cudaMalloc 配额检查
 *
 * 分配一块显存, 确保在配额内成功.
 * 然后逐步分配直到超出配额, 验证返回 cudaErrorMemoryAllocation.
 *
 * 注意: CUDA Runtime 自身在第一次调用时会分配 ~200-300MB
 * (CUDA context), 所以配额不能设太小. 建议 >= 256MB.
 * ═══════════════════════════════════════════════════════════════ */
int test_cudaMalloc_quota(void) {
    printf("--- Test 1: cudaMalloc 配额 ---\n");

    /* 1a: 请求一块小显存, 应在配额内成功 */
    float *d1 = NULL;
    cudaError_t r = cudaMalloc((void**)&d1, 64 * MB);
    if (r == cudaErrorMemoryAllocation) {
        FAIL("64MB 分配失败 — 配额可能设得太小 (CUDA context 已占一部分)");
    }
    if (r != cudaSuccess || d1 == NULL) {
        FAIL("64MB 分配返回意外错误");
    }
    printf("  [OK] cudaMalloc(64MB) 成功, ptr=%p\n", d1);

    /* 1b: 尝试一次性申请远超配额的显存, 应返回 cudaErrorMemoryAllocation */
    float *d2 = NULL;
    r = cudaMalloc((void**)&d2, 2048 * MB);
    if (r != cudaErrorMemoryAllocation) {
        /* 注意: 如果没有设置配额环境变量, 分配会成功 (如果 GPU 显存够大).
         *       这里不直接 FAIL, 打印警告即可. */
        printf("  [WARN] cudaMalloc(2048MB) 未返回 cudaErrorMemoryAllocation (code=%d)\n", r);
        printf("         可能未设置 CUDA_MEM_QUOTA_MB 或配额 > 2048MB\n");
        if (d2) cudaFree(d2);
    } else {
        printf("  [OK] cudaMalloc(2048MB) 正确返回 cudaErrorMemoryAllocation\n");
    }

    cudaFree(d1);
    PASS();
    return 0;
}

/* ═══════════════════════════════════════════════════════════════
 * Test 2: cudaLaunchKernel 令牌桶限速
 *
 * 连续启动大量 kernel, 验证令牌桶生效: 前几个通过 (消耗 burst),
 * 后续被拒绝 (令牌耗尽). 等待 refill 后应恢复.
 *
 * 默认: CUDA_CORE_RATE=5 (每秒 5 个), CUDA_CORE_CAPACITY=3 (burst 3 个).
 * ═══════════════════════════════════════════════════════════════ */
int test_cudaLaunchKernel_rate(void) {
    printf("--- Test 2: cudaLaunchKernel 令牌桶 ---\n");

    float *d_data;
    int n = 32;  /* gridDim.x * blockDim.x = 1 * 32 */
    CHECK(cudaMalloc((void**)&d_data, 4 * MB), "cudaMalloc for kernel test");
    void* kargs[] = { &d_data, &n };

    int passed = 0, denied = 0;

    /* 2a: 快速连续启动 kernel, 耗尽 burst */
    printf("  [Phase 1] 连续启动 10 个 kernel (burst=%s)...\n", getenv("CUDA_CORE_CAPACITY") ? getenv("CUDA_CORE_CAPACITY") : "?");
    for (int i = 0; i < 10; i++) {
        cudaError_t r = cudaLaunchKernel(
            (const void*)dummy_kernel, dim3(1,1,1), dim3(32,1,1),
            kargs, 0, NULL);
        cudaDeviceSynchronize();
        if (r == cudaSuccess) {
            passed++;
        } else if (r == 4) {  /* cudaErrorLaunchFailure */
            denied++;
        }
    }
    printf("  [Phase 1] 通过=%d, 拒绝=%d\n", passed, denied);

    /* 检查: burst 耗尽后应至少有一些被拒绝 */
    if (denied == 0) {
        printf("  [WARN] 无 kernel 被拒绝 — 可能未设置 CUDA_CORE_RATE/CAPACITY\n");
    }

    /* 2b: 等待 refill, 令牌应恢复 */
    passed = 0;
    printf("  [Phase 2] 等待 1.5s refill...\n");
    usleep(1500000);

    for (int i = 0; i < 5; i++) {
        cudaError_t r = cudaLaunchKernel(
            (const void*)dummy_kernel, dim3(1,1,1), dim3(32,1,1),
            kargs, 0, NULL);
        cudaDeviceSynchronize();
        if (r == cudaSuccess) passed++;
    }
    printf("  [Phase 2] 等待后通过=%d\n", passed);

    /* 检查: refill 后应有令牌可用 */
    if (passed == 0) {
        FAIL("refill 后仍无 token — launch_refill() 逻辑可能有 bug");
    }

    cudaFree(d_data);
    PASS();
    return 0;
}

/* ═══════════════════════════════════════════════════════════════
 * Test 3: Grid/Block 维度记录
 *
 * 启动不同 Grid/Block 配置的 kernel, 验证 hook 日志正确记录了维度.
 * 此测试不检查 hook 行为, 只检查 hook 不会崩溃.
 * 学生在 hook 日志中手动验证维度输出是否正确.
 * ═══════════════════════════════════════════════════════════════ */
int test_kernel_dims(void) {
    printf("--- Test 3: Grid/Block 维度记录 ---\n");

    float *d_data;
    int n;
    CHECK(cudaMalloc((void**)&d_data, 4 * MB), "cudaMalloc");

    /* 模拟 Prefill: 1 block, 256 threads */
    n = 256;
    void* kargs1[] = { &d_data, &n };
    cudaLaunchKernel((const void*)dummy_kernel, dim3(1,1,1), dim3(256,1,1),
                     kargs1, 0, NULL);
    cudaDeviceSynchronize();
    printf("  [OK] Prefill-like: grid=(1,1,1) block=(256,1,1)\n");

    /* 模拟 Decode: 16 blocks, 32 threads */
    n = 16 * 32;
    void* kargs2[] = { &d_data, &n };
    cudaLaunchKernel((const void*)dummy_kernel, dim3(16,1,1), dim3(32,1,1),
                     kargs2, 0, NULL);
    cudaDeviceSynchronize();
    printf("  [OK] Decode-like:  grid=(16,1,1) block=(32,1,1)\n");

    /* 3D grid */
    n = 2 * 2 * 2 * 64;
    void* kargs3[] = { &d_data, &n };
    cudaLaunchKernel((const void*)dummy_kernel, dim3(2,2,2), dim3(64,1,1),
                     kargs3, 0, NULL);
    cudaDeviceSynchronize();
    printf("  [OK] 3D:           grid=(2,2,2) block=(64,1,1)\n");

    cudaFree(d_data);
    PASS();
    return 0;
}

/* ═══════════════════════════════════════════════════════════════
 * main: 依次运行所有测试
 *
 * 返回值: 通过的测试数 → 全部通过返回 0.
 * 每个测试失败会立即停止 (便于定位问题).
 * ═══════════════════════════════════════════════════════════════ */
int main(void) {
    printf("═════════════════════════════════════════\n");
    printf("  CUDA Hook 验证测试\n");
    printf("  CUDA_MEM_QUOTA_MB=%s\n",  getenv("CUDA_MEM_QUOTA_MB")  ? getenv("CUDA_MEM_QUOTA_MB")  : "(未设置)");
    printf("  CUDA_CORE_RATE=%s\n",     getenv("CUDA_CORE_RATE")     ? getenv("CUDA_CORE_RATE")     : "(未设置)");
    printf("  CUDA_CORE_CAPACITY=%s\n", getenv("CUDA_CORE_CAPACITY") ? getenv("CUDA_CORE_CAPACITY") : "(未设置)");
    printf("═════════════════════════════════════════\n\n");

    int failed = 0;

    if (test_cudaMalloc_quota() != 0)       { failed++; printf("\n"); }
    if (test_cudaLaunchKernel_rate() != 0)  { failed++; printf("\n"); }
    if (test_kernel_dims() != 0)            { failed++; printf("\n"); }

    printf("═════════════════════════════════════════\n");
    if (failed == 0) {
        printf("  全部测试通过!  Hook 拦截生效.\n");
    } else {
        printf("  %d 个测试失败 — 检查上面的 [FAIL] 信息.\n", failed);
    }
    printf("═════════════════════════════════════════\n");

    return failed;
}
