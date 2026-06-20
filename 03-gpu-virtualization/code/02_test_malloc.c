/*
 * 模块 3：GPU 虚拟化与容器化实践 — LD_PRELOAD 配额测试程序
 *
 * 编译: gcc 02_test_malloc.c -o test_malloc
 * 运行: LD_PRELOAD=./libmymalloc.so ./test_malloc
 *
 * 预期:
 *   40MB → ✓ (已用 40/100MB)
 *   40MB → ✓ (已用 80/100MB)
 *   30MB → ✗ QUOTA EXCEEDED → 返回 NULL
 */

#include <stdio.h>
#include <stdlib.h>

#define MB (1024 * 1024)

int main() {
    printf("=== 测试 1: 分配 40MB ===\n");
    void *p1 = malloc(40 * MB);
    printf("p1 = %p  %s\n\n", p1, p1 ? "✓" : "✗ FAIL");

    printf("=== 测试 2: 分配 40MB ===\n");
    void *p2 = malloc(40 * MB);
    printf("p2 = %p  %s\n\n", p2, p2 ? "✓" : "✗ FAIL");

    printf("=== 测试 3: 分配 30MB (应超 100MB 配额) ===\n");
    void *p3 = malloc(30 * MB);
    printf("p3 = %p  %s (NULL = 配额生效)\n\n", p3, p3 ? "✗ 配额未生效!" : "✓ 配额生效!");

    free(p1);
    free(p2);
    return p3 ? 1 : 0;
}
