# 模块 3：GPU 虚拟化与容器化实践 — 课后练习

## 题目：LD_PRELOAD 原理验证 + GPU 虚拟化方案分析

### 截止时间

模块 4 课前

---

## 任务 1: 扩展 LD_PRELOAD hook (必做)

在课堂 `malloc` hook 的基础上，增加**配额限制**逻辑：

```c
// quota_malloc.c
#define _GNU_SOURCE
#include <stdio.h>
#include <dlfcn.h>
#include <stdlib.h>

#define QUOTA 1024  // 配额: 1024 bytes

static size_t used = 0;

void *malloc(size_t size) {
    static void *(*real_malloc)(size_t) = NULL;
    if (!real_malloc)
        real_malloc = dlsym(RTLD_NEXT, "malloc");

    if (used + size > QUOTA) {
        fprintf(stderr, "[QUOTA] malloc(%zu) 超配额! (已用 %zu / 配额 %d)\n",
                size, used, QUOTA);
        return NULL;  // 模拟 CUDA_ERROR_OUT_OF_MEMORY
    }

    void *p = real_malloc(size);
    used += size;
    printf("[OK] malloc(%zu) → %p, 已用 %zu/%d\n", size, p, used, QUOTA);
    return p;
}
```

要求:

1. 编写测试程序，依次分配 200、400、500、200 bytes
2. 预期: 前三个分配成功，第四个返回 NULL（超配额）
3. 讨论: 这和 HAMi 的 `cuMemAlloc` 拦截逻辑有什么异同？

## 任务 2: GPU 虚拟化方案对比分析 (必做)

阅读 AI-fundamentals `04_cloud_native_ai_platform/gpu_manager/` 中的四部分教程，完成:

1. 画出 MIG、Time-Slicing、HAMi-core、MPS 四种方案的「隔离级别 × 灵活性」象限图
2. 对于以下三个场景，分别推荐哪种方案？说明理由:
   - 场景 A: 医疗影像 AI，对数据安全要求极高，需要硬件级隔离
   - 场景 B: 互联网公司推理集群，运行 20+ 个小模型，需要灵活资源切分
   - 场景 C: 高校实验室，学生共享少量 GPU 做课程实验

---

## 进阶任务 (选做)

### 任务 3: 深入 HAMi 源码

阅读 HAMi 的 `libvgpu.so` 相关源码，找到 `cuMemAlloc` 和 `cuLaunchKernel` 的拦截实现。画出拦截流程图。

### 任务 4: 多阶段构建优化

构建两个版本的 vLLM 镜像:

- 版本 A: 单阶段 (FROM devel，编译+运行都在一个镜像)
- 版本 B: 多阶段 (devel 编译 → runtime 运行)

对比两个版本的大小，记录优化效果。

---

## 提交要求

1. 提交 `quota_malloc.c` + 测试程序 + 运行结果截图
2. 提交 GPU 虚拟化方案对比分析 (≤ 2 页)
3. (选做) HAMi 源码分析 或 多阶段构建对比

---

## 评分标准

| 维度                | 权重 | 要求                              |
| ------------------- | ---- | --------------------------------- |
| 任务 1 (LD_PRELOAD) | 30%  | 正确实现配额限制，测例通过        |
| 任务 2 (方案分析)   | 45%  | 象限图清晰 + 三个场景选型有理有据 |
| 文档质量            | 15%  | 截图清晰、描述完整                |
| 进阶任务            | 10%  | 完成至少一项                      |

---

## 参考资料

- AI-fundamentals: `04_cloud_native_ai_platform/gpu_manager/第一部分：基础理论篇.md` — 概念与选型
- AI-fundamentals: `04_cloud_native_ai_platform/gpu_manager/第二部分：虚拟化技术篇.md` — 三种虚拟化实现
- AI-fundamentals: `04_cloud_native_ai_platform/gpu_manager/hami/hmai-gpu-resources-guide.md` — HAMi 手册
- AI-fundamentals: `04_cloud_native_ai_platform/gpu_manager/hami/KAI_vs_HAMi_Comparison.md` — KAI vs HAMi
- [HAMi GitHub](https://github.com/Project-HAMi/HAMi)
