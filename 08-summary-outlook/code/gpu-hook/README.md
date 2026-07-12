# 方向 A: GPU 资源拦截 — 从显存到算力

**难度**: ★★★☆ &nbsp;|&nbsp; **覆盖模块**: 3 (GPU 虚拟化) &nbsp;|&nbsp; **需要 GPU + CUDA Toolkit**

## 快速开始

```bash
# 1. 编译 hook 库 (只需 gcc)
make

# 2. 无 GPU 快速自检 — 验证 hook 加载不崩溃
make test

# 3. 编译测试程序 + 运行 (需要 nvcc + GPU)
make test-gpu

# 或手动:
nvcc --cudart=shared test_hook.cu -o test_hook
#      ↑ 必须是 shared — 静态链接的 CUDA 符号无法被 LD_PRELOAD 拦截
LD_PRELOAD=./libcuda_hook.so \
  CUDA_MEM_QUOTA_MB=128 \
  CUDA_CORE_RATE=5 \
  CUDA_CORE_CAPACITY=3 \
  ./test_hook
```

## 文件说明

| 文件           | 说明                                                           |
| -------------- | -------------------------------------------------------------- |
| `cuda_hook.c`  | LD_PRELOAD CUDA hook 骨架 — 搜索 `TODO` 完成显存+算力双拦截    |
| `test_hook.cu` | 统一测试程序，3 个测试验证拦截效果，**不需要修改**             |
| `Makefile`     | `make` 编译 hook (gcc)，`make test-gpu` 编译 (nvcc) 并运行测试 |

## TODO 清单

| TODO          | 函数               | 难度 | 对应课上内容                                                   |
| ------------- | ------------------ | ---- | -------------------------------------------------------------- |
| TODO 1        | `cudaMalloc`       | ★★☆  | 模块 3 `01_mymalloc.c` — LD_PRELOAD 三步模式 + 配额检查        |
| TODO 2        | `cudaLaunchKernel` | ★★★  | 模块 3 `03_token_bucket.py` — 令牌桶 `_refill()` + `acquire()` |
| TODO 3 (选做) | `cudaFree`         | ★★☆  | 模块 3 `01_mymalloc.c` `free()` — 简化释放跟踪                 |

### TODO 与模块 3 代码的对应关系

每个 TODO 都是模块 3 课上代码的**逐行翻译**：

| 模块 3 代码                | 语言   | 功能                    | → TODO | C 语言对应                                 |
| -------------------------- | ------ | ----------------------- | ------ | ------------------------------------------ |
| `01_mymalloc.c:63-95`      | C      | `malloc` 拦截 + 配额    | TODO 1 | `cudaMalloc` — 函数签名不同、逻辑完全相同  |
| `03_token_bucket.py:39-56` | Python | `TokenBucket.acquire()` | TODO 2 | 令牌桶变 C 全局变量 + `clock_gettime` 计时 |
| `01_mymalloc.c:98-108`     | C      | `free` 简化拦截         | TODO 3 | `cudaFree` — 同样不跟踪释放大小            |

骨架代码已提供完整的基础设施（`dim3` 类型、`launch_refill()` 函数、递归守卫、懒加载），学生只需填充 `// TODO` 注释区的 ~15 行代码。

## 测试程序说明

`test_hook.cu` 包含 3 个独立测试，按顺序运行：

| 测试   | 验证内容                  | 预期结果                                                                      |
| ------ | ------------------------- | ----------------------------------------------------------------------------- |
| Test 1 | `cudaMalloc` 配额         | 64MB 分配成功；2048MB 返回 `cudaErrorMemoryAllocation` (2)                    |
| Test 2 | `cudaLaunchKernel` 令牌桶 | 连续 10 个 kernel: 前 3 个通过 (burst=3)，7 个被拒绝；等待 1.5s refill 后恢复 |
| Test 3 | Grid/Block 维度记录       | 不同维度 kernel 正常启动，hook 日志输出正确的维度信息                         |

### 预期输出 (RTX 3090 实测)

**stdout** (测试程序):

```text
═════════════════════════════════════════
  CUDA Hook 验证测试
  CUDA_MEM_QUOTA_MB=128
  CUDA_CORE_RATE=5
  CUDA_CORE_CAPACITY=3
═════════════════════════════════════════

--- Test 1: cudaMalloc 配额 ---
  [OK] cudaMalloc(64MB) 成功
  [OK] cudaMalloc(2048MB) 正确返回 cudaErrorMemoryAllocation
  [PASS]
--- Test 2: cudaLaunchKernel 令牌桶 ---
  [Phase 1] 通过=3, 拒绝=7
  [Phase 2] 等待后通过=3
  [PASS]
--- Test 3: Grid/Block 维度记录 ---
  [OK] Prefill-like: grid=(1,1,1) block=(256,1,1)
  [OK] Decode-like:  grid=(16,1,1) block=(32,1,1)
  [OK] 3D:           grid=(2,2,2) block=(64,1,1)
  [PASS]
═════════════════════════════════════════
  全部测试通过!  Hook 拦截生效.
═════════════════════════════════════════
```

**stderr** (hook 日志，前 10 行):

```text
[HOOK] 显存配额: 128 MB (134217728 bytes)
[HOOK] 算力限速: 5 tokens/s, burst 3
[HOOK] cudaMalloc(67108864) -> 0x... | total: 64.0 MB
[HOOK] cudaMalloc(2147483648) DENIED | total: 64.0 / 128.0 MB
[HOOK] cudaLaunchKernel(grid=1,1,1 block=32,1,1) -> 0 | tokens=2.0
[HOOK] cudaLaunchKernel(grid=1,1,1 block=32,1,1) -> 0 | tokens=1.0
[HOOK] cudaLaunchKernel(grid=1,1,1 block=32,1,1) -> 0 | tokens=0.0
[HOOK] cudaLaunchKernel(grid=1,1,1 block=32,1,1) DENIED | tokens=0.0
```

## 实验流程

1. `make test` → 确认 hook 加载、初始化日志 (stderr) 正常
2. `make test-gpu` → 看测试程序输出，确认 3 个测试全部 PASS
3. 收集 stderr 日志: `make test-gpu 2> hook.log`
4. 用 Python 解析 `hook.log`，统计拦截次数、画出时间线
5. 撰写报告

## 无 GPU 替代方案

将 `cudaMalloc` 替换为 `malloc`、`cudaLaunchKernel` 替换为普通函数调用，用模块 3 的 `01_mymalloc.c` + `03_token_bucket.py` 组合验证拦截和限速逻辑。

---

## FAQ

### Q1: 为什么 `make test` 用 `ls` 能验证 hook 不崩溃？

`ls` 不调用任何 CUDA API，所以 hook 的三个拦截函数不会被触发。但 hook 的 `constructor` 会在 `LD_PRELOAD` 加载时执行——读环境变量 + 打印配置日志。如果 `make test` 能看到 stderr 输出 `[HOOK] 显存配额...` 且不崩溃，说明骨架代码的 constructor 和懒加载机制正常。

### Q2: 为什么编译 test_hook 必须加 `--cudart=shared`？

nvcc 默认**静态链接** `libcudart`，即 `cudaMalloc` 等符号在编译时已被解析为静态库地址。LD_PRELOAD 只能拦截动态链接的符号——如果符号是静态链接的，Hook 函数永远不会被调用。

`--cudart=shared` 强制使用动态库 `libcudart.so`，确保符号在运行时由 `ld.so` 解析，Hook 才能插入。

**验证方法**: `ldd test_hook | grep cuda` — 应该看到 `libcudart.so.12 => ...`。

### Q3: 为什么用懒加载而不是在 constructor 里 resolve CUDA 符号？

模块 3 的 `01_mymalloc.c` 用的就是懒加载：

```c
void *malloc(size_t size) {
    static void *(*real_malloc)(size_t) = NULL;
    if (!real_malloc)
        real_malloc = dlsym(RTLD_NEXT, "malloc");
    ...
}
```

如果在 constructor 里 `dlsym(RTLD_NEXT, "cudaMalloc")`，非 CUDA 程序（如 `ls`）会因找不到符号而 crash。懒加载意味着只有第一次真正调用 `cudaMalloc` 时才 resolve——非 CUDA 程序永远不触发，不会崩溃。

### Q4: `cudaFree` 为什么不递减 `allocated_bytes`？

`cudaFree` 的函数签名是 `cudaError_t cudaFree(void* devPtr)`——只传指针，不传大小。要精确跟踪已释放的字节数，需要维护一个指针到大小的映射表（Hash Table），这超出了本次作业的范围。

与模块 3 `01_mymalloc.c` 的 `free()` 一样，采用"只记录释放事件"的简化方案。

### Q5: CUDA context 占用显存，配额设太小会怎样？

CUDA Runtime 第一次调用时会自动创建 CUDA Context，占用约 200-300 MB 显存（取决于 GPU 型号和驱动版本）。如果 `CUDA_MEM_QUOTA_MB` 设得太小（如 64MB），Hook 会在 CUDA Runtime 自身的初始化分配时就直接拒绝，导致程序崩溃。

建议 `CUDA_MEM_QUOTA_MB ≥ 256`，给 CUDA context 留足空间。`test_hook.cu` 的 Test 1 先用 64MB 测试正常分配，再用 2048MB 测试超配额拒绝——两段之间 CUDA context 已经初始化完毕。

### Q6: `test_hook.cu` 的 Test 3 全被 DENIED 了，这正常吗？

正常。Test 2 的 Phase 2 耗尽了令牌桶，Test 3 紧跟着启动（没有 refill 间隔），此时 `launch_tokens ≈ 0`，三个 kernel 都被拒绝。

但 Hook 日志仍然正确记录了 Grid/Block 维度——这就是 Test 3 的目的：验证维度日志输出正确，而不是验证 kernel 能否启动。学生在分析 hook 日志时应注意到 DENIED 消息中包含了正确的维度信息。
