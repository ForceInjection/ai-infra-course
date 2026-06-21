/**
 * LD_PRELOAD CUDA Runtime API Hook
 *
 * 编译: make
 * 用法: LD_PRELOAD=./libcuda_hook.so CUDA_MEM_QUOTA_MB=512 python example.py
 *
 * 参考: 模块 3 code/01_mymalloc.c (malloc hook 模式)
 * 关键: __thread 递归守卫 — printf 内部可能调 cudaMalloc, 必须防止死循环
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ── 递归守卫 (与模块 3 malloc hook 相同模式) ── */
static __thread int in_hook = 0;

/* ── 原始 CUDA Runtime API 函数指针 ── */
typedef int (*cudaError_t);
typedef void* (*orig_cudaMalloc_t)(size_t size);
typedef void* (*orig_cudaFree_t)(void* devPtr);

static orig_cudaMalloc_t real_cudaMalloc = NULL;
static orig_cudaFree_t    real_cudaFree    = NULL;

/* ── 显存配额管理 ── */
static size_t quota_bytes = 0;      /* 配额上限 (bytes), 0 = 无限制 */
static size_t allocated_bytes = 0;  /* 当前已分配总量 */

/* ── 辅助: 获取原始函数指针 ── */
static void* get_real(const char* name) {
    void* p = dlsym(RTLD_NEXT, name);
    if (!p) {
        fprintf(stderr, "[HOOK] FATAL: dlsym(%s) failed: %s\n", name, dlerror());
        abort();
    }
    return p;
}

/* ── 初始化: 读取环境变量 ── */
__attribute__((constructor))
static void hook_init(void) {
    const char* quota_str = getenv("CUDA_MEM_QUOTA_MB");
    if (quota_str) {
        quota_bytes = (size_t)(atof(quota_str) * 1024.0 * 1024.0);
        fprintf(stderr, "[HOOK] 显存配额: %.0f MB (%zu bytes)\n",
                atof(quota_str), quota_bytes);
    } else {
        fprintf(stderr, "[HOOK] 无显存配额限制 (记录模式)\n");
    }

    real_cudaMalloc = (orig_cudaMalloc_t)get_real("cudaMalloc");
    real_cudaFree   = (orig_cudaFree_t)get_real("cudaFree");
}

/* ═══════════════════════════════════════════════════════════════
 * TODO 1: 拦截 cudaMalloc
 *
 * 要求:
 *   1. 检查 in_hook, 防止递归
 *   2. 调用 real_cudaMalloc 分配显存
 *   3. 如果成功:
 *      - 更新 allocated_bytes
 *      - 打印日志: [HOOK] cudaMalloc(size=XXX) -> ptr=0xXXX, total=XXX MB
 *   4. 如果超出配额: 返回 cudaErrorMemoryAllocation (值为 2),
 *      不调用 real_cudaMalloc
 *   5. 返回 real_cudaMalloc 的返回值 (cudaError_t, 0 = 成功)
 *
 * 提示:
 *   - cudaMalloc 的签名: cudaError_t cudaMalloc(void** devPtr, size_t size)
 *   - 第一个参数是 void** (输出参数, 指向分配的设备内存指针)
 *   - 第二个参数是 size_t (请求分配的字节数)
 *   - 成功返回 0 (cudaSuccess), 内存不足返回 2 (cudaErrorMemoryAllocation)
 * ═══════════════════════════════════════════════════════════════ */

cudaError_t cudaMalloc(void** devPtr, size_t size) {
    /* ── 递归守卫 ── */
    if (in_hook) {
        /* TODO: 如果正在 hook 中, 直接调用原始函数 */
        return 0; /* ← 替换为正确实现 */
    }
    in_hook = 1;

    /* TODO: 检查配额 (如果 quota_bytes > 0) */
    /* TODO: 如果超出配额, 打印日志并返回 cudaErrorMemoryAllocation (2) */

    /* TODO: 调用 real_cudaMalloc */
    cudaError_t result = 0; /* ← 替换: result = real_cudaMalloc(devPtr, size); */

    /* TODO: 如果分配成功, 更新 allocated_bytes 并打印日志 */
    /* 日志格式: fprintf(stderr, "[HOOK] cudaMalloc(%zu) -> %p | total: %.1f MB\n",
                         size, *devPtr, allocated_bytes / (1024.0*1024.0)); */

    in_hook = 0;
    return result;
}

/* ═══════════════════════════════════════════════════════════════
 * TODO 2 (选做): 拦截 cudaFree
 *
 * 要求:
 *   1. 调用 real_cudaFree
 *   2. 更新 allocated_bytes (减去对应大小)
 *   3. 打印日志
 *
 * 注意: cudaFree 的函数签名是 cudaError_t cudaFree(void* devPtr)
 *       与 malloc/free 不同, cudaFree 不传大小参数。
 *       因此需要额外维护一个 ptr→size 映射表来确定释放了多少字节。
 *       (简化方案: 不跟踪释放, 只记录分配)
 * ═══════════════════════════════════════════════════════════════ */
