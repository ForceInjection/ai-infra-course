# 模块 3：GPU 虚拟化与容器化实践 — 课后练习

## 题目：LD_PRELOAD 原理验证 + GPU 虚拟化方案分析

### 截止时间

模块 4 课前

### 环境要求

| 任务          | 需要硬件/软件 | 说明                                             |
| ------------- | ------------- | ------------------------------------------------ |
| 任务 1 (必做) | GCC           | 编译运行 malloc hook，观察输出后答题             |
| 任务 2 (必做) | 无            | 基于 PPT 完成方案分析和场景选型                  |
| 任务 3 (选做) | HAMi 源码     | `git clone https://github.com/Project-HAMi/HAMi` |
| 任务 4 (选做) | Docker + GPU  | 多阶段镜像构建，需要 `nvidia/cuda:12.8.0`        |

---

## 任务 1: 从 malloc hook 到 CUDA API 拦截 (必做)

课堂的 `01_mymalloc.c` 演示了 `LD_PRELOAD` → hook `malloc` → 配额检查的基本原理。HAMi 把这个思路搬到了 CUDA API 上。

**动手**: 编译并运行课堂代码，观察 hook 输出和配额超限行为：

```bash
cd code/
gcc -shared -fPIC 01_mymalloc.c -o libmymalloc.so -ldl
gcc 02_test_malloc.c -o test_malloc
LD_PRELOAD=./libmymalloc.so ./test_malloc
```

基于你的运行结果和 PPT 内容，回答：

1. 对比 `malloc` 和 `cuMemAlloc` 的函数签名，课堂的 hook 需要哪些修改才能拦截 `cuMemAlloc`？列出至少 3 处差异。
2. 除了 `cuMemAlloc`，HAMi 还可以拦截哪些 CUDA API 来实现 GPU 资源共享？（至少列出 2 个，说明各自的作用。提示: PPT 第 14-16 页）
3. 观察你的运行输出: `free(p1)` 和 `free(p2)` 之后，hook 的 `used` 计数器有没有减少？为什么 `free` hook 不递减 `used`？如果要精确跟踪配额释放，需要增加什么机制？
4. 画出 LD_PRELOAD → dlsym(RTLD_NEXT) → hook 函数 → 原始函数 的调用流程图，标注 `__thread in_hook` 递归守卫的位置。

## 任务 2: GPU 虚拟化方案对比分析 (必做)

基于课堂 PPT 第 4-9 页的内容，完成:

1. 画出 MIG、Time-Slicing、HAMi-core、MPS 四种方案的「隔离级别 × 灵活性」象限图（参考 PPT 第 9 页对比矩阵）
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

- 课堂代码: `code/01_mymalloc.c`、`code/02_test_malloc.c`
- 课堂 PPT: 第 4-9 页 (GPU 虚拟化方案)、第 11-16 页 (HAMi 架构)
- [AI-fundamentals](https://github.com/ForceInjection/AI-fundamentals/blob/main/04_cloud_native_ai_platform/gpu_manager/) — GPU 虚拟化深入阅读 (选读)
- [HAMi GitHub](https://github.com/Project-HAMi/HAMi) — HAMi 源码 (任务 3)
