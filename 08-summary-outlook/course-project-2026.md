# 课程大作业：编写一个 GPU 资源拦截器

## 一、你要做什么

用 LD_PRELOAD 技术写一个共享库 `libcuda_hook.so`，拦截 CUDA 程序的 GPU 调用，实现两个功能：

1. **显存配额** — 限制程序最多能用多少 MB 显存，超了就报错
2. **算力限速** — 用令牌桶控制程序每秒最多启动几次 GPU Kernel

做完之后，运行我们提供的测试程序，你的 Hook 应该能让它：

- 64MB 显存分配成功，2048MB 被拒绝
- 连续 10 个 Kernel 只有前 3 个通过（burst），后面全部被限速拒绝

---

## 二、脚手架

所有文件在 `08-summary-outlook/code/gpu-hook/`：

| 文件           | 你要做什么                               |
| -------------- | ---------------------------------------- |
| `cuda_hook.c`  | **搜索 `TODO`，填代码**                  |
| `test_hook.cu` | 不用改，用来验证你的 Hook                |
| `Makefile`     | `make` 编译 Hook，`make test-gpu` 跑测试 |

**TODO 地图：**

打开 `cuda_hook.c`，找到这三处 `TODO`：

| 位置                       | 做什么                         | 抄哪里                                                      | 难度 |
| -------------------------- | ------------------------------ | ----------------------------------------------------------- | ---- |
| `TODO 1: cudaMalloc`       | 配额检查 + 调用原始函数 + 日志 | `03-gpu-virtualization/code/01_mymalloc.c` 第 63-95 行      | ★★   |
| `TODO 2: cudaLaunchKernel` | 令牌桶检查 + 转发 + 记录维度   | `03-gpu-virtualization/code/03_token_bucket.py` 第 39-56 行 | ★★★  |
| `TODO 3: cudaFree` (选做)  | 释放记录                       | `03-gpu-virtualization/code/01_mymalloc.c` 第 98-108 行     | ★    |

> 更多细节（预期输出、FAQ）见 `gpu-hook/README.md`。

---

## 三、评分标准

| 维度                    | 权重 | 满分长什么样                                                             |
| ----------------------- | ---- | ------------------------------------------------------------------------ |
| `cudaMalloc` 拦截       | 40%  | 配额检查正确，超限返回 `cudaErrorMemoryAllocation`，日志格式符合预期     |
| `cudaLaunchKernel` 拦截 | 35%  | 令牌桶逻辑正确，burst 耗尽后拒绝，refill 后恢复，Grid/Block 维度日志正确 |
| 实验日志 + 分析         | 15%  | 跑出 hook 日志，用 Python 统计拦截次数并画出时间线                       |
| README + 代码可运行     | 10%  | `make && make test-gpu` 一键跑通，有简要说明                             |

> `cudaFree` (TODO 3) 做对了加 5 分额外奖励，不做不扣分。

---

## 四、提交

1. **代码**: `cuda_hook.c` + 其他你认为需要的文件，确保 `make && make test-gpu` 能跑通
2. **实验日志**: `hook.log` — `make test-gpu 2> hook.log` 的输出
3. **分析脚本 + 结果**: Python 脚本 + 跑出来的统计结果或图表，至少回答：
   - 一共拦截了多少次 `cudaMalloc`？多少被拒绝？
   - `cudaLaunchKernel` 的令牌数随时间怎么变化？（抄 `hook.log` 里的 `tokens=` 画个折线图就行）
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

### 4. `cudaFree` 无法精确跟踪释放量

`cudaFree(void* devPtr)` 只传指针不传大小。要知道释放了多少字节需要额外维护指针→大小映射表（Hash Table），太复杂，不做。和课上 `01_mymalloc.c` 的 `free()` 一样，只记录释放事件即可。

### 5. Test 3 全被 DENIED 是正常的

Test 2 耗尽令牌桶后，Test 3 紧接着启动（没有 refill 间隔），此时令牌数 ≈ 0，三个 Kernel 都会被拒绝。这不影响 Test 3 的目的——验证 Hook 日志里 Grid/Block 维度的输出是否正确。

---

## 六、如果你没有 GPU

把 `cudaMalloc` 换成 `malloc`、`cudaLaunchKernel` 换成一个普通函数调用，用模块 3 的 `01_mymalloc.c` + `03_token_bucket.py` 组合来验证拦截和限速逻辑。提交时说明你用的是无 GPU 方案。
