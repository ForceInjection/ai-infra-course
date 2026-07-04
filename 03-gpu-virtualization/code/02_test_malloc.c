/*
 * 模块 3：GPU 虚拟化与容器化实践 — LD_PRELOAD 配额测试程序
 * PPT 第 33 页 [动手 1] 配套测试
 *
 * 编译: gcc 02_test_malloc.c -o test_malloc
 * 运行: LD_PRELOAD=./libmymalloc.so ./test_malloc
 *
 * 测试设计:
 *   hook 中配额设为 100MB (见 01_mymalloc.c 第 22 行)。
 *   三次 malloc: 40MB + 40MB + 30MB = 110MB > 100MB 配额。
 *   前两次成功 (累计 80MB)，第三次触发配额拒绝，返回 NULL。
 *
 * 注意:
 *   - fflush(stdout): hook 的 printf 和本程序的 printf 都输出到 stdout，
 *     需要先刷新本程序的输出，保证 "=== 测试 3 ===" 出现在 hook 日志之前。
 *   - free(p1) 和 free(p2) 不会恢复配额: hook 的 free 是简化版，
 *     不跟踪每块内存的大小，因此 used 计数器不递减。
 *     这是有意为之的简化，让学生思考 "真正的配额管理需要什么"。
 *   - return p3 ? 1 : 0: p3==NULL 时返回 0 (正常退出)，
 *     p3!=NULL 时返回 1 (说明配额没生效，hook 有 bug)。
 */

#include <stdio.h>
#include <stdlib.h>

#define MB (1024 * 1024)

int main() {
    // 测试 1+2: 累计 80MB，在 100MB 配额内，均应成功
    printf("=== 测试 1: 分配 40MB ===\n");
    void *p1 = malloc(40 * MB);
    printf("p1 = %p  %s\n\n", p1, p1 ? "✓" : "✗ FAIL");

    printf("=== 测试 2: 分配 40MB ===\n");
    void *p2 = malloc(40 * MB);
    printf("p2 = %p  %s\n\n", p2, p2 ? "✓" : "✗ FAIL");

    // 测试 3: 累计将超 100MB，hook 应返回 NULL
    printf("=== 测试 3: 分配 30MB (应超 100MB 配额) ===\n");
    fflush(stdout);  // 确保本行出现在 hook 的配额日志之前
    void *p3 = malloc(30 * MB);
    printf("p3 = %p  %s (NULL = 配额生效)\n\n", p3, p3 ? "✗ 配额未生效!" : "✓ 配额生效!");

    // 释放 (注意: hook 的 used 计数器不会减少 — 有意简化)
    free(p1);
    free(p2);

    // p3==NULL 说明配额生效 → 返回 0 (正常); 否则 hook 有 bug → 返回 1
    return p3 ? 1 : 0;
}
