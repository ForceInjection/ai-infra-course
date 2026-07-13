# 课程大作业：编写一个 GPU 资源拦截器

> [HTML 展示版](course-project-2026.html) (适合课堂投影)

## 一、你要做什么

用 LD_PRELOAD 技术写一个共享库 `libcuda_hook.so`，拦截 CUDA 程序的 GPU 调用，实现两个功能：

1. **显存配额** — 限制程序最多能用多少 MB 显存，超了就报错
2. **算力限速** — 用令牌桶控制程序每秒最多启动几次 GPU Kernel

做完之后，运行我们提供的测试程序，你的 Hook 应该能让它：

- 64MB 显存分配成功，2048MB 被拒绝
- 连续 10 个 Kernel 只有前 3 个通过（burst），后面全部被限速拒绝

> **为什么拦截 Runtime API (`cudaMalloc`) 而不是 Driver API (`cuMemAlloc_v2`)？**
>
> HAMi-core 拦截的是更底层的 CUDA Driver API（`cu*` 函数），但我们选了 Runtime API（`cuda*` 函数），是一个有意为之的简化。
>
> 模块 3 的 `01_mymalloc.c` 拦截 `malloc(void*, size_t)`，而 `cudaMalloc` 的签名是 `cudaMalloc(void**, size_t)`——几乎一样，一行翻译。`cuMemAlloc_v2(CUdeviceptr*, size_t)` 则需要额外引入 `CUdeviceptr`、`CUresult`、`cuInit` 等新概念，分散了对核心模式（Hook → 检查 → 转发）的注意力。测试程序也会从三行变成十几行样板代码。
>
> Runtime API 底层就是调 Driver API——HAMi-core 的做法和你写的只是**拦截的层级不同，模式完全一样**。做完作业再看延伸阅读，一眼就能看懂。

---

## 二、脚手架

所有文件在 [`gpu-hook/`](code/gpu-hook/)：

| 文件                                         | 你要做什么                               |
| -------------------------------------------- | ---------------------------------------- |
| [`cuda_hook.c`](code/gpu-hook/cuda_hook.c)   | **搜索 `TODO`，填代码**                  |
| [`test_hook.cu`](code/gpu-hook/test_hook.cu) | 不用改，用来验证你的 Hook                |
| [`Makefile`](code/gpu-hook/Makefile)         | `make` 编译 Hook，`make test-gpu` 跑测试 |

**TODO 地图：**

打开 `cuda_hook.c`，找到这三处 `TODO`：

| 位置                       | 做什么                         | 抄哪里                                                                                                                                     | 难度 |
| -------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ | ---- |
| `TODO 1: cudaMalloc`       | 配额检查 + 调用原始函数 + 日志 | [`01_mymalloc.c:63-95`](../03-gpu-virtualization/code/01_mymalloc.c)                                                                       | ★★   |
| `TODO 2: cudaLaunchKernel` | 令牌桶检查 + 转发 + 记录维度   | [`03_token_bucket.py:39-56`](../03-gpu-virtualization/code/03_token_bucket.py)                                                             | ★★★  |
| `TODO 3: cudaFree` (选做)  | ptr→size 映射表 + 精确跟踪释放 | HAMi-core [`allocator.c:179`](https://github.com/Project-HAMi/HAMi-core/blob/main/src/allocator/allocator.c) `remove_chunk()` — 数组简化版 | ★★★  |

> 更多细节（预期输出、FAQ）见 [`gpu-hook/README.md`](code/gpu-hook/README.md)。
>
> 预计完成时间：**3-6 小时**（TODO 1: 30 分钟，TODO 2: 1 小时，TODO 3: 1-2 小时，实验分析: 1-2 小时）。

---

## 三、评分标准

| 维度                    | 权重 | 满分长什么样                                                             |
| ----------------------- | ---- | ------------------------------------------------------------------------ |
| `cudaMalloc` 拦截       | 35%  | 配额检查正确，超限返回 `cudaErrorMemoryAllocation`，日志 + 映射表写入    |
| `cudaLaunchKernel` 拦截 | 30%  | 令牌桶逻辑正确，burst 耗尽后拒绝，refill 后恢复，Grid/Block 维度日志正确 |
| `cudaFree` 映射表       | 10%  | ptr→size 查表正确，精确递减 allocated_bytes，条目删除无误                |
| 实验日志 + 分析         | 15%  | 跑出 hook 日志，用 Python 统计拦截次数并画出时间线                       |
| README + 代码可运行     | 10%  | `make && make test-gpu` 一键跑通，有简要说明                             |

> TODO 1 + TODO 2 做到满分 = 75 分。TODO 3 完成再加 10 分。三个全做好 = 85 + 实验日志 15 = 100。

---

## 四、提交

1. **代码**: `cuda_hook.c` + 其他你认为需要的文件，确保 `make && make test-gpu` 能跑通
2. **实验日志**: `hook.log` — `make test-gpu 2> hook.log` 的输出
3. **分析脚本 + 结果**: Python 脚本 + 跑出来的统计结果或图表，至少回答：
   - 一共拦截了多少次 `cudaMalloc`？多少被拒绝？
   - `cudaLaunchKernel` 的令牌数随时间怎么变化？（从 `hook.log` 提取 `tokens=` 画折线图；matplotlib / Excel / 手绘截屏都行，能用就行）
4. **README**: 一句话说怎么跑 + 你遇到的问题（如果有）

打包成 `学号_姓名.zip`，发送到 <wang.tianqing.cn@outlook.com>。

**截止时间**: 2026 年 7 月 31 日

---

## 五、会踩的坑（FAQ）

### 1. 编译 test_hook 必须加 `--cudart=shared`

nvcc 默认把 CUDA 库静态链接进程序——这会让 LD_PRELOAD 失效（符号已在编译时写死，运行时不会走你的 Hook）。Makefile 已经帮你加了这个参数，手动编译的话注意别漏掉。

验证：`ldd test_hook | grep cuda`，应该看到 `libcudart.so.12 => ...`。

### 2. 不要在 constructor 里 resolve CUDA 符号

骨架代码用的是**懒加载**——第一次调用 `cudaMalloc` 时才 `dlsym(RTLD_NEXT, "cudaMalloc")`。这和 `01_mymalloc.c` 的做法完全一致。如果改成 constructor 里 eager resolve，`ls` 这种非 CUDA 程序一加载 Hook 就会 crash。

### 3. CUDA context 会占用 ~200-300 MB 显存

第一次调用任何 CUDA API 时，驱动会自动创建 CUDA Context，这个 Context 本身就占显存。所以 `CUDA_MEM_QUOTA_MB` 不要设太小，建议 ≥ 256 MB。测试程序默认用 128 MB（小配额是为了更容易触发 DENIED），但 CUDA Context 的 ~200 MB 不计入你的 Hook 跟踪——你只跟踪程序自己调的 `cudaMalloc`。

### 4. `cudaFree` 的 ptr→size 查表怎么做？

`cudaFree(void* devPtr)` 只传指针不传大小，所以需要在 TODO 1 的 `cudaMalloc` 成功时把 `(ptr, size)` 存进 `alloc_table[]`，TODO 3 的 `cudaFree` 用 `devPtr` 去表里线性搜索，找到对应的 size 后从 `allocated_bytes` 中减去，并将该条目从表中移除。删除时不必保持顺序——想想怎么最快地把一个元素从数组里拿掉。

### 5. Test 3 全被 DENIED 是正常的

Test 2 耗尽令牌桶后，Test 3 紧接着启动（没有 refill 间隔），此时令牌数 ≈ 0，三个 Kernel 都会被拒绝。这不影响 Test 3 的目的——验证 Hook 日志里 Grid/Block 维度的输出是否正确。

### 6. Hook 没生效？按这个顺序排查

如果 `make test-gpu` 跑完了但所有 kernel 都通过、没有任何 DENIED（或完全没有 `[HOOK]` 日志），按顺序检查：

1. **stderr 有没有 `[HOOK] 显存配额...`？** 没有 → Hook 根本没加载。检查 `LD_PRELOAD` 路径是否正确、`.so` 是否编译成功。
2. **`ldd test_hook | grep cuda`** → 应该看到 `libcudart.so.12`。没看到 → 编译时漏了 `--cudart=shared`（Makefile 已经帮你加了，手动编译的话注意）。
3. **先不加配额跑一次**：`LD_PRELOAD=./libcuda_hook.so ./test_hook`（不设 `CUDA_MEM_QUOTA_MB`），确认 Hook 起码能记录日志、不崩溃。
4. **再加配额验证拦截**：加上 `CUDA_MEM_QUOTA_MB=128 CUDA_CORE_RATE=5 CUDA_CORE_CAPACITY=3`，确认 DENIED 出现。
5. 还是不行 → 检查 Hook 编译时有没有 warning（`gcc -Wall` 会提示未初始化的变量、类型不匹配等）。

---

## 六、延伸阅读

你写的 `cuda_hook.c` 拦截了 2 个 CUDA Runtime API（`cudaMalloc` + `cudaLaunchKernel`），约 15 行核心逻辑。工业级的 HAMi-core 拦截了 **100+ 个 CUDA Driver API** + **~20 个 NVML API**（`nvidia-smi` 依赖），核心代码约 2500 行。

关键区别：你拦截的是 Runtime API（`cuda*`），HAMi-core 拦截的是更底层的 **Driver API**（`cu*`）。所有框架（PyTorch、TensorFlow、vLLM）最终都通过 Driver API 访问 GPU，所以在 Driver 层拦截一次，所有框架全部受控。你的 `cudaMalloc` 底层也是调 `cuMemAlloc_v2`。

HAMi-core 拦截了哪些你熟悉的 API：

| 分类         | 你做的             | HAMi-core 对应                                                                     | 区别                                                    |
| ------------ | ------------------ | ---------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 显存分配     | `cudaMalloc`       | `cuMemAlloc_v2`, `cuMemAllocManaged`, `cuMemAllocAsync` 等 30+                     | 你只拦截一种分配方式，HAMi 堵住了所有入口               |
| 显存释放     | `cudaFree`         | `cuMemFree_v2`, `cuMemFreeHost`, `cuMemFreeAsync`                                  | 同上，且精确跟踪 ptr→size                               |
| 算力限速     | `cudaLaunchKernel` | `cuLaunchKernel`, `cuLaunchKernelEx`, `cuLaunchCooperativeKernel`, `cuGraphLaunch` | 你的实现用令牌桶，HAMi 的多进程版用共享内存协调         |
| 设备伪造     | —                  | `cuDeviceGetCount`, `cuDeviceGetName`, `cuDeviceTotalMem_v2`                       | 让容器以为 GPU 数量、型号、显存大小都是自己独占的       |
| Context 限制 | —                  | `cuCtxCreate_v2/v3/v4`, `cuCtxDestroy_v2`                                          | 限制每容器能创建几个 CUDA Context                       |
| NVML 拦截    | —                  | `nvmlDeviceGetMemoryInfo`, `nvmlDeviceGetUtilizationRates` 等 ~20 个               | `nvidia-smi` 在容器内显示"该容器的"显存用量，而不是整卡 |

还有一个你做了但 HAMi-core 比你更狠的设计：**连 `dlsym` 本身也被拦截了**。你的 Hook 用 `dlsym(RTLD_NEXT)` 拿原始函数指针——如果有恶意程序也调 `dlsym(RTLD_NEXT, "cuMemAlloc_v2")`，就能绕过 Hook 直接调原始函数。HAMi-core 把自己的 `dlsym` 也注入了符号表，任何 `dlsym` 调用都优先返回 Hook 版本的函数指针。

→ [HAMi-core 源码](https://github.com/Project-HAMi/HAMi-core) — 建议从 `src/cuda/hook.c`（函数注册表）和 `src/libvgpu.c`（dlsym 劫持入口）开始看。

---

## 七、如果你没有 GPU

把 `cudaMalloc` 换成 `malloc`、`cudaLaunchKernel` 换成一个普通函数调用，用模块 3 的 `01_mymalloc.c` + `03_token_bucket.py` 组合来验证拦截和限速逻辑。提交时说明你用的是无 GPU 方案。
