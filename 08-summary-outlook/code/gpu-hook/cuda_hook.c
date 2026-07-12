/**
 * LD_PRELOAD CUDA Runtime API Hook — 显存配额 + 算力限速
 *
 * 编译: make
 * 用法:
 *   make && make test-gpu
 *
 *   或手动:
 *   LD_PRELOAD=./libcuda_hook.so \
 *     CUDA_MEM_QUOTA_MB=128 \
 *     CUDA_CORE_RATE=5 \
 *     CUDA_CORE_CAPACITY=3 \
 *     ./test_hook
 *
 * 参考:
 *   模块 3 code/01_mymalloc.c    — LD_PRELOAD 三步模式 + 递归守卫 + 配额检查
 *   模块 3 code/03_token_bucket.py — 令牌桶 _refill() + acquire() 逻辑
 *
 * ═══════════════════════════════════════════════════════════
 * LD_PRELOAD 拦截原理 (与模块 3 malloc hook 完全一致)
 * ═══════════════════════════════════════════════════════════
 *
 *   1. 符号劫持: LD_PRELOAD 把 libcuda_hook.so 插入搜索链最前端
 *   2. dlsym(RTLD_NEXT, "cudaMalloc") — 获取 NVIDIA 驱动的原始实现
 *   3. 配额/令牌检查 → 放行或拒绝 → 转发给原始函数
 *
 *   递归守卫: __thread in_hook — fprintf 内部可能触发 cudaMalloc，
 *   必须防止 hook → 日志 → cudaMalloc → hook 的死循环。
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ── CUDA 类型定义 ── */
typedef int cudaError_t;

/* dim3: CUDA 三维向量, 实际就是三个 unsigned int */
typedef struct {
    unsigned int x, y, z;
} dim3;

typedef cudaError_t (*orig_cudaMalloc_t)(void** devPtr, size_t size);
typedef cudaError_t (*orig_cudaFree_t)(void* devPtr);
typedef cudaError_t (*orig_cudaLaunchKernel_t)(
    const void* func, dim3 gridDim, dim3 blockDim,
    void** args, size_t sharedMem, void* stream);

static orig_cudaMalloc_t       real_cudaMalloc       = NULL;
static orig_cudaFree_t         real_cudaFree         = NULL;
static orig_cudaLaunchKernel_t real_cudaLaunchKernel = NULL;

/* ── 递归守卫 (与模块 3 01_mymalloc.c 相同模式) ── */
static __thread int in_hook = 0;

/* ── 显存配额管理 (对应模块 3 malloc hook 的 used/quota) ── */
static size_t quota_bytes     = 0;  /* 配额上限 (bytes), 0 = 无限制 */
static size_t allocated_bytes = 0;  /* 当前已分配总量 */

/* ── 算力令牌桶 (对应模块 3 03_token_bucket.py 的 TokenBucket 类) ── */
static double  launch_rate     = 0;   /* CUDA_CORE_RATE:    每秒补充令牌数 */
static double  launch_capacity = 0;   /* CUDA_CORE_CAPACITY: 桶容量 (最大突发) */
static double  launch_tokens   = 0;   /* 当前令牌数 */
static struct timespec launch_last_refill = {0};

/* ── 令牌桶 refill (对应 03_token_bucket.py TokenBucket._refill) ── */
static void launch_refill(void) {
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    double elapsed = (now.tv_sec - launch_last_refill.tv_sec)
                   + (now.tv_nsec - launch_last_refill.tv_nsec) / 1e9;
    launch_tokens += elapsed * launch_rate;
    if (launch_tokens > launch_capacity)
        launch_tokens = launch_capacity;
    launch_last_refill = now;
}

/* ── 初始化: 读取环境变量 (不在此处解析 CUDA 符号 — 由各 hook 函数懒加载) ── */
__attribute__((constructor))
static void hook_init(void) {
    const char* mem_str  = getenv("CUDA_MEM_QUOTA_MB");
    const char* rate_str = getenv("CUDA_CORE_RATE");
    const char* cap_str  = getenv("CUDA_CORE_CAPACITY");

    if (mem_str) {
        quota_bytes = (size_t)(atof(mem_str) * 1024.0 * 1024.0);
        fprintf(stderr, "[HOOK] 显存配额: %.0f MB (%zu bytes)\n",
                atof(mem_str), quota_bytes);
    } else {
        fprintf(stderr, "[HOOK] 显存配额: 无限制 (仅记录)\n");
    }

    if (rate_str && cap_str) {
        launch_rate     = atof(rate_str);
        launch_capacity = atof(cap_str);
        launch_tokens   = launch_capacity;  /* 初始满桶 */
        clock_gettime(CLOCK_MONOTONIC, &launch_last_refill);
        fprintf(stderr, "[HOOK] 算力限速: %.0f tokens/s, burst %d\n",
                launch_rate, (int)launch_capacity);
    } else {
        fprintf(stderr, "[HOOK] 算力限速: 无限制 (仅记录)\n");
    }
}

/* ═══════════════════════════════════════════════════════════════
 * TODO 1: 显存拦截 — cudaMalloc
 *
 * 要求 (直接翻译模块 3 01_mymalloc.c 的 malloc hook):
 *   1. 递归守卫: in_hook 为真时直接调用 real_cudaMalloc 放行
 *   2. 配额检查: allocated_bytes + size > quota_bytes → 返回错误
 *   3. 调用 real_cudaMalloc(devPtr, size)
 *   4. 成功后更新 allocated_bytes, 打印日志
 *
 * 签名: cudaError_t cudaMalloc(void** devPtr, size_t size)
 * 成功返回 0 (cudaSuccess), 超配额返回 2 (cudaErrorMemoryAllocation)
 *
 * 提示: 代码结构与 01_mymalloc.c 第 63-95 行完全相同,
 *       把 real_malloc 换成 real_cudaMalloc, used 换成 allocated_bytes 即可.
 * ═══════════════════════════════════════════════════════════════ */

cudaError_t cudaMalloc(void** devPtr, size_t size) {
    /* ── 懒加载: 第一次调用时解析原始 cudaMalloc (与 01_mymalloc.c 第 64-66 行相同模式) ── */
    if (!real_cudaMalloc)
        real_cudaMalloc = (orig_cudaMalloc_t)dlsym(RTLD_NEXT, "cudaMalloc");

    /* ── STEP 1: 递归守卫 ── */
    if (in_hook) {
        return real_cudaMalloc(devPtr, size);
    }
    in_hook = 1;

    /* ── STEP 2: 配额检查 ── */
    /* TODO: 如果 quota_bytes > 0 且 allocated_bytes + size > quota_bytes:
     *         fprintf(stderr, "[HOOK] cudaMalloc(%zu) DENIED | total: %.1f / %.1f MB\n",
     *                 size, allocated_bytes/(1024.0*1024.0), quota_bytes/(1024.0*1024.0));
     *         in_hook = 0;
     *         return 2;  // cudaErrorMemoryAllocation
     */

    /* ── STEP 3: 调用原始 cudaMalloc ── */
    /* TODO: cudaError_t result = real_cudaMalloc(devPtr, size); */

    /* ── STEP 4: 记录并返回 ── */
    /* TODO: 如果 result == 0 (成功):
     *         allocated_bytes += size;
     *         fprintf(stderr, "[HOOK] cudaMalloc(%zu) -> %p | total: %.1f MB\n",
     *                 size, *devPtr, allocated_bytes / (1024.0*1024.0));
     */

    cudaError_t result = 0; /* ← 替换为上面的实现 */
    in_hook = 0;
    return result;
}

/* ═══════════════════════════════════════════════════════════════
 * TODO 2: 算力拦截 — cudaLaunchKernel
 *
 * 要求 (直接翻译模块 3 03_token_bucket.py 的 TokenBucket.acquire):
 *   1. 递归守卫 (同 TODO 1)
 *   2. (选做) Prefill 阶段放行: gridDim 很小且 blockDim 很大时放行
 *   3. launch_refill() → 检查 launch_tokens >= 1
 *   4. 有令牌: launch_tokens--, 调用 real_cudaLaunchKernel, 打印 Grid/Block 维度
 *   5. 无令牌: 返回 4 (cudaErrorLaunchFailure)
 *
 * 签名:
 *   cudaError_t cudaLaunchKernel(const void* func,
 *       dim3 gridDim, dim3 blockDim, void** args,
 *       size_t sharedMem, cudaStream_t stream);
 *
 * 提示:
 *   - dim3.x/y/z 分别对应三个维度的线程块数或线程数
 *   - 令牌桶逻辑参考 03_token_bucket.py 第 39-56 行 (acquire 方法)
 *   - 时间获取用 clock_gettime(CLOCK_MONOTONIC, ...)
 * ═══════════════════════════════════════════════════════════════ */

cudaError_t cudaLaunchKernel(
    const void* func, dim3 gridDim, dim3 blockDim,
    void** args, size_t sharedMem, void* stream)
{
    /* ── 懒加载: 第一次调用时解析原始 cudaLaunchKernel ── */
    if (!real_cudaLaunchKernel)
        real_cudaLaunchKernel = (orig_cudaLaunchKernel_t)dlsym(RTLD_NEXT, "cudaLaunchKernel");

    /* ── STEP 1: 递归守卫 ── */
    if (in_hook) {
        return real_cudaLaunchKernel(func, gridDim, blockDim, args, sharedMem, stream);
    }
    in_hook = 1;

    /* ── STEP 2 (选做): Prefill 阶段放行 ── */
    /* 提示: Prefill 通常 gridDim 只有 1-2 个 Block, blockDim 很大。
     *       Decode 阶段 gridDim >> 1 (每 token 一个 block)。
     *       简化实现可跳过此区分, 对所有 kernel 均等对待。 */

    /* ── STEP 3: 令牌桶检查 ── */
    cudaError_t result;

    /* TODO: launch_refill();
     *       if (launch_rate > 0 && launch_tokens < 1) {
     *           fprintf(stderr, "[HOOK] cudaLaunchKernel(grid=%u,%u,%u block=%u,%u,%u) DENIED | tokens=%.1f\n",
     *                   gridDim.x, gridDim.y, gridDim.z, blockDim.x, blockDim.y, blockDim.z, launch_tokens);
     *           in_hook = 0;
     *           return 4;  // cudaErrorLaunchFailure
     *       }
     *       launch_tokens -= 1; */

    /* ── STEP 4: 调用原始函数 ── */
    /* TODO: result = real_cudaLaunchKernel(func, gridDim, blockDim, args, sharedMem, stream); */

    /* ── STEP 5: 打印 Grid/Block 维度 ── */
    /* TODO: fprintf(stderr, "[HOOK] cudaLaunchKernel(grid=%u,%u,%u block=%u,%u,%u) -> %d | tokens=%.1f\n",
     *                gridDim.x, gridDim.y, gridDim.z, blockDim.x, blockDim.y, blockDim.z, result, launch_tokens); */

    result = 0; /* ← 替换为上面的实现 */
    in_hook = 0;
    return result;
}

/* ═══════════════════════════════════════════════════════════════
 * TODO 3 (选做): 显存释放 — cudaFree
 *
 * 要求:
 *   1. 递归守卫 (同 TODO 1)
 *   2. 调用 real_cudaFree 释放显存
 *   3. 打印释放记录
 *
 * 签名: cudaError_t cudaFree(void* devPtr)
 *
 * 注意: cudaFree 不传 size 参数, 要精确跟踪已分配量需要额外维护
 *       ptr→size 映射表 (Hash Table 或链表). 简化方案: 只记录释放
 *       事件, 不递减 allocated_bytes. 与模块 3 01_mymalloc.c 第 98-108
 *       行 free() 的简化策略相同.
 * ═══════════════════════════════════════════════════════════════ */

cudaError_t cudaFree(void* devPtr) {
    /* ── 懒加载: 第一次调用时解析原始 cudaFree ── */
    if (!real_cudaFree)
        real_cudaFree = (orig_cudaFree_t)dlsym(RTLD_NEXT, "cudaFree");

    /* ── STEP 1: 递归守卫 ── */
    if (in_hook) {
        return real_cudaFree(devPtr);
    }
    in_hook = 1;

    /* ── STEP 2: 调用原始 cudaFree ── */
    /* TODO: cudaError_t result = real_cudaFree(devPtr); */

    /* ── STEP 3: 记录释放 (简化: 不递减 allocated_bytes) ── */
    /* TODO: fprintf(stderr, "[HOOK] cudaFree(%p) -> %d\n", devPtr, result); */

    cudaError_t result = 0; /* ← 替换为上面的实现 */
    in_hook = 0;
    return result;
}
