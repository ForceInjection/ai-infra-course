/*
 * 模块 3：GPU 虚拟化与容器化实践 — LD_PRELOAD malloc hook 演示
 * PPT 第 12 页 + 第 33 页 [动手 1]
 *
 * 编译: gcc -shared -fPIC 01_mymalloc.c -o libmymalloc.so -ldl
 * 运行: LD_PRELOAD=./libmymalloc.so <任意程序>
 *
 * ═══════════════════════════════════════════════════════════
 * LD_PRELOAD 拦截原理 (三步)
 * ═══════════════════════════════════════════════════════════
 *
 * 第一步 — 符号劫持:
 *   程序调用 malloc() 时，动态链接器 (ld.so) 按顺序搜索已加载的共享库。
 *   LD_PRELOAD 把我们的 libmymalloc.so 插入搜索链的最前端，
 *   因此我们的 malloc() 被优先找到并调用，系统的 malloc() 被"遮蔽"。
 *
 * 第二步 — 获取原始函数:
 *   dlsym(RTLD_NEXT, "malloc") 在搜索链中从当前位置继续向后查找，
 *   返回下一个名为 "malloc" 的符号 — 即 glibc 的原始 malloc。
 *   我们把它保存为 real_malloc，在需要真正分配内存时调用它。
 *
 * 第三步 — 转发调用 (Hook 模式):
 *   hook_malloc(size):
 *     1. 检查配额 → 超限则返回 NULL (不调用 real_malloc)
 *     2. 调用 real_malloc(size) → 真正分配内存
 *     3. 记录分配量 → 更新 used 计数器
 *     4. 返回指针给调用者
 *
 * ═══════════════════════════════════════════════════════════
 * 递归守卫 (__thread in_hook)
 * ═══════════════════════════════════════════════════════════
 *
 *   hook 内部调用 printf() → printf 内部调用 malloc() → 又进入 hook → 死循环!
 *   解决: 用 __thread 变量 in_hook 标记"正在 hook 中"。
 *   进入 hook 时 in_hook=1，printf 内部触发的 malloc 看到 in_hook=1，
 *   直接走 real_malloc 放行，不再检查配额或打印日志。
 *
 * ═══════════════════════════════════════════════════════════
 * HAMi 的类比
 * ═══════════════════════════════════════════════════════════
 *
 *   HAMi 的 libvgpu.so 用完全相同的三步拦截 CUDA API:
 *   1. LD_PRELOAD=libvgpu.so → 拦截 cuMemAlloc / cuLaunchKernel 等
 *   2. dlsym(RTLD_NEXT, "cuMemAlloc") → 获取 NVIDIA 驱动的原始实现
 *   3. 检查显存配额 / 算力令牌 → 超限返回 CUDA_ERROR_OUT_OF_MEMORY
 *
 *   本 demo = HAMi 的微缩版 (60 行 vs 数千行)，展示核心骨架。
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
        printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        printf("[QUOTA EXCEEDED] malloc(%zu bytes) 被拒绝\n", size);
        printf("  已用: %zu / 配额: %zu (%.1f%%)\n",
                used, quota, 100.0 * used / quota);
        printf("  类比: HAMi 中 cuMemAlloc 超配额 → 返回 CUDA_ERROR_OUT_OF_MEMORY\n");
        printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        fflush(stdout);
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

/* ── hook free (演示简化: 不跟踪单指针大小, 不恢复 used) ── */
void free(void *ptr) {
    static void (*real_free)(void *) = NULL;
    if (!real_free)
        real_free = dlsym(RTLD_NEXT, "free");

    /* 注意: 本 demo 简化了 free — 不递减 used 计数器。
     *      因为 free(void*) 不传 size，要精确跟踪需要额外维护
     *      ptr→size 映射表 (可用 hash table)。这不是本模块的重点。
     *      HAMi 的实际实现会精确跟踪每次 cuMemAlloc/cuMemFree。 */
    real_free(ptr);
}
