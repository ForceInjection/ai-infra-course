# 模块 3：GPU 虚拟化与容器化实践 — 课后练习

## 题目：LD_PRELOAD 原理验证 + GPU 虚拟化方案分析

### 截止时间

模块 4 课前

---

## 任务 1: 从 malloc hook 到 CUDA API 拦截 (必做)

课堂的 `01_mymalloc.c` 演示了 `LD_PRELOAD` → hook `malloc` → 配额检查的基本原理。HAMi 把这个思路搬到了 CUDA API 上。阅读以下材料：

- 课堂代码: `code/01_mymalloc.c`
- HAMi 参考: AI-fundamentals `04_cloud_native_ai_platform/gpu_manager/code/virtualization/cuda_api_intercept.c`

回答以下问题：

1. 课堂的 `malloc` hook 需要哪些修改才能拦截 `cuMemAlloc`？列出至少 3 处差异。
2. HAMi 还拦截了哪些 CUDA API？（至少列出 3 个，说明各自的作用）
3. 我们的 `01_mymalloc.c` 缺少什么关键机制？从以下角度分析：**(a)** 配额释放（什么时候释放已用的配额？） **(b)** 多进程支持（不同进程的配额如何隔离？） **(c)** 容错（如果 hooked 程序 crash 了，配额会怎样？）
4. 画出 HAMi 拦截 `cuMemAlloc` 的完整流程图（从应用程序调用到返回结果），标注配额检查、令牌桶检查的位置。

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

1. 提交任务 1 的 4 个问题回答 + 拦截流程图 (≤ 2 页)
2. 提交 GPU 虚拟化方案对比分析 (≤ 2 页)
3. (选做) HAMi 源码分析 或 多阶段构建对比

---

## 评分标准

| 维度                       | 权重 | 要求                              |
| -------------------------- | ---- | --------------------------------- |
| 任务 1 (CUDA API 拦截分析) | 40%  | 4 个问题回答准确 + 流程图正确     |
| 任务 2 (方案分析)          | 35%  | 象限图清晰 + 三个场景选型有理有据 |
| 文档质量                   | 15%  | 描述完整、逻辑清晰                |
| 进阶任务                   | 10%  | 完成至少一项                      |

---

## 参考资料

- AI-fundamentals: `04_cloud_native_ai_platform/gpu_manager/code/virtualization/cuda_api_intercept.c` — CUDA API 拦截参考实现
- AI-fundamentals: `04_cloud_native_ai_platform/gpu_manager/第一部分：基础理论篇.md` — 概念与选型
- AI-fundamentals: `04_cloud_native_ai_platform/gpu_manager/第二部分：虚拟化技术篇.md` — 三种虚拟化实现
- AI-fundamentals: `04_cloud_native_ai_platform/gpu_manager/hami/hmai-gpu-resources-guide.md` — HAMi 手册
- AI-fundamentals: `04_cloud_native_ai_platform/gpu_manager/hami/KAI_vs_HAMi_Comparison.md` — KAI vs HAMi
- [HAMi GitHub](https://github.com/Project-HAMi/HAMi)
