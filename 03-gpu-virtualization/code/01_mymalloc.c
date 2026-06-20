/*
 * 模块 3：GPU 虚拟化与容器化实践 — LD_PRELOAD malloc hook 演示
 * PPT 第 12 页 + 第 33 页 [动手 1]
 *
 * 编译: gcc -shared -fPIC 01_mymalloc.c -o libmymalloc.so -ldl
 * 运行: LD_PRELOAD=./libmymalloc.so <任意程序>
 * 示例: LD_PRELOAD=./libmymalloc.so ls -la
 *
 * 原理: LD_PRELOAD 让动态链接器优先加载我们的 libmymalloc.so，
 *       其中的 malloc() 会替代系统的 malloc()。
 *       HAMi 的 libvgpu.so 用完全相同的机制拦截 cuMemAlloc 等 CUDA API。
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>

/* ── 配额管理 (模拟 HAMi 的显存配额) ── */
static size_t quota = 100 * 1024 * 1024;  // 100MB 配额 (演示用。小配额会导致 ls/python 自身启动就超限)
static size_t used = 0;

/* ── 防重入标志 (printf 内部会调用 malloc，不保护会死循环) ── */
static __thread int in_hook = 0;

/* ── hook malloc ── */
void *malloc(size_t size) {
    static void *(*real_malloc)(size_t) = NULL;
    if (!real_malloc)
        real_malloc = dlsym(RTLD_NEXT, "malloc");

    /* 如果是 printf/fprintf 内部调用的 malloc，直接放行 */
    if (in_hook) return real_malloc(size);

    in_hook = 1;

    /* 配额检查 — 模拟 HAMi 的 cuMemAlloc 拦截逻辑 */
    if (used + size > quota) {
        fprintf(stderr, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        fprintf(stderr, "[QUOTA EXCEEDED] malloc(%zu bytes) 被拒绝\n", size);
        fprintf(stderr, "  已用: %zu / 配额: %zu (%.1f%%)\n",
                used, quota, 100.0 * used / quota);
        fprintf(stderr, "  类比: HAMi 中 cuMemAlloc 超配额 → 返回 CUDA_ERROR_OUT_OF_MEMORY\n");
        fprintf(stderr, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        in_hook = 0;
        return NULL;  // 模拟 CUDA_ERROR_OUT_OF_MEMORY
    }

    /* 调用真正的 malloc */
    void *p = real_malloc(size);
    if (p) {
        used += size;
        printf("[HOOK] malloc(%zu) → %p  (已用 %zu / %zu, %.1f%%)\n",
               size, p, used, quota, 100.0 * used / quota);
    }
    in_hook = 0;
    return p;
}

/* ── hook free (配额释放 — HAMi 中进程退出时释放) ── */
void free(void *ptr) {
    static void (*real_free)(void *) = NULL;
    if (!real_free)
        real_free = dlsym(RTLD_NEXT, "free");

    /* 注意: 简单的 demo 不跟踪单个指针的分配大小，
     *      实际 HAMi 的实现会更精确地跟踪每次 cuMemAlloc/cuMemFree */
    real_free(ptr);
}
