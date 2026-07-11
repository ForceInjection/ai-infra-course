# 模块 5 配套代码 — vLLM 推理框架

## 文件说明

| 文件                | 内容                            | 对应 PPT             |
| ------------------- | ------------------------------- | -------------------- |
| `trace_nanovllm.py` | nano-vllm monkey-patch 追踪脚本 | 第 49–50 页 [动手 2] |

nano-vllm 源码在独立仓库，无需复制到此处: <https://github.com/ForceInjection/nano-vllm>

---

## 环境安装

### 前提

- Linux (Ubuntu 22.04+)
- Python ≥ 3.10
- NVIDIA GPU (Compute Capability ≥ 7.0, ≥ 8 GB 显存)
- NVIDIA Driver ≥ 525 (CUDA 12.x 兼容)

### Step 1: 安装 PyTorch

```bash
# 标准安装 (CUDA 12.4，RTX 3090/4090/A100/H100 通用)
pip3 install torch==2.6.0 -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 验证
python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# → 2.6.0+cu124  True
```

### Step 2: 安装 flash-attn

> **重要**: PyTorch 2.6.0+cu124 的 C++ ABI 与 flash-attn ≥ 2.8.0 不兼容 (PyTorch 在 cu126+ 改了 ABI)。
> 必须使用 **2.7.4.post1**。

```bash
# 从 GitHub Releases 下载预编译 wheel (国内可能需代理)
# 文件名: flash_attn-2.7.4.post1+cu12torch2.5cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
# 下载地址: https://github.com/Dao-AILab/flash-attention/releases/tag/v2.7.4.post1

# 如果服务器能访问 GitHub:
pip3 install https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.5cxx11abiFALSE-cp310-cp310-linux_x86_64.whl

# 如果服务器无法访问 GitHub (国内常见):
# 方案 A: 本机下载 → scp 上传 → 安装 (244 MB)
# 方案 B: 源码编译 (MAX_JOBS=1 避免 CPU 吃满)
CUDA_HOME=/usr/local/cuda MAX_JOBS=1 pip3 install flash_attn==2.7.4.post1 -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 验证
python3 -c "import flash_attn; print('flash-attn OK')"
```

### Step 3: 安装 nano-vllm

```bash
# 克隆或上传 nano-vllm 到服务器
cd /tmp && git clone https://github.com/ForceInjection/nano-vllm.git  # 或 scp 上传

# 安装依赖 (如果 git clone 不可用，pip install 也会自动安装)
pip3 install transformers accelerate tqdm xxhash ray -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 添加到 PYTHONPATH (无需 pip install)
export PYTHONPATH=/tmp/nano-vllm:$PYTHONPATH

# 验证
python3 -c "from nanovllm import LLM; print('nano-vllm OK')"
```

### Step 4: 下载模型

```bash
# 从 ModelScope 下载 (国内推荐，速度快):
pip3 install modelscope -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
modelscope download --model Qwen/Qwen3-0.6B --local_dir ~/huggingface/Qwen3-0.6B

# 或从 HuggingFace 下载 (需要代理):
huggingface-cli download --resume-download Qwen/Qwen3-0.6B --local-dir ~/huggingface/Qwen3-0.6B
```

### Step 5: 验证推理

```bash
cd /tmp/nano-vllm
python3 -c "
from nanovllm import LLM, SamplingParams
llm = LLM('/root/huggingface/Qwen3-0.6B', enforce_eager=True)
outputs = llm.generate(['Hello, my name is'], SamplingParams(temperature=0.6, max_tokens=64))
print(outputs[0]['text'])
"
# 预期输出: Decode ~30 tok/s (RTX 3090), 生成一段英文回复
```

### 环境一览 (RTX 3090 实测)

| 组件       | 版本        | 备注                                 |
| ---------- | ----------- | ------------------------------------ |
| PyTorch    | 2.6.0+cu124 | 阿里云 mirror                        |
| flash-attn | 2.7.4.post1 | **必须 ≤2.7.4**，与 torch cu124 匹配 |
| nano-vllm  | main        | /tmp/nano-vllm                       |
| 模型       | Qwen3-0.6B  | ~1.5 GB，ModelScope 下载             |
| 推理速度   | ~30 tok/s   | enforce_eager=True                   |

## 运行方法

> nano-vllm 安装在 `/tmp/nano-vllm`，需设置 PYTHONPATH。

```bash
# 确保 PYTHONPATH 已在 .bashrc 中 (永久生效):
echo 'export PYTHONPATH=/tmp/nano-vllm:$PYTHONPATH' >> ~/.bashrc
source ~/.bashrc

# 默认追踪 (两个短 prompt)
cd /home/ai-infra/05-vllm-inference/code/
python3 trace_nanovllm.py

# 指定模型和 prompt
python3 trace_nanovllm.py \
    --model ~/huggingface/Qwen3-0.6B/ \
    --prompts "你好" "什么是GPU?" "介绍一下你自己" \
    --max-tokens 128

# 降低显存利用 → 更容易触发 Preemption
python3 trace_nanovllm.py --gpu-memory-utilization 0.3
```

## 预期输出

```text
============================================================
nano-vllm 执行追踪开始
模型: ~/huggingface/Qwen3-0.6B/
显存利用: 60%
prompts: 2 个
============================================================
[SEQ 0] CREATED | num_tokens=5 | num_blocks=1
[SEQ 1] CREATED | num_tokens=8 | num_blocks=1
[BLOCK] ALLOCATE seq=0 | cached=0 | new=1 | block_table=[0] | free_blocks=444
[BLOCK] ALLOCATE seq=1 | cached=0 | new=1 | block_table=[1] | free_blocks=443
[SCHED] STEP seq=0 | phase=PREFILL | token=103929 | num_tokens=5 | cached=0 | status→RUNNING
[SCHED] STEP seq=1 | phase=PREFILL | token=49891 | num_tokens=8 | cached=0 | status→RUNNING
[SCHED] STEP seq=0 | phase=DECODE | token=101419 | num_tokens=6 | cached=5 | status→RUNNING
[SCHED] STEP seq=1 | phase=DECODE | token=33108 | num_tokens=9 | cached=8 | status→RUNNING
...  (每个 token 一行 DECODE，交错执行)
[SCHED] STEP seq=0 | phase=DECODE | token=3837 | num_tokens=63 | cached=62 | status→FINISHED
[BLOCK] DEALLOCATE seq=0 | block_table=[0]
...  (seq=1 继续 DECODE 直到 FINISHED)
[BLOCK] DEALLOCATE seq=1 | block_table=[1]

============================================================
输出结果:

--- Prompt 1 ---
你的名字是李明，性别是男性，年龄是25岁...

--- Prompt 2 ---
GPU和CPU有什么区别？有什么应用场景？...
```

> 注意: `token=103929` 是 tokenizer 的 token ID，不是可读字符。观察重点是 PREFILL/DECODE 交替和 Block 分配回收的时序。
> 调低 `--gpu-memory-utilization 0.3` 可以看到 `[SCHED] PREEMPT` 行——显存不足时 Sequence 被抢占。

## 观察要点

| 日志前缀             | 观察内容                                                                                       |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| `[SEQ] CREATED`      | Sequence 何时创建 (WAITING 状态)，num_tokens/num_blocks                                        |
| `[BLOCK] ALLOCATE`   | Block 分配详情: cached_blocks (Prefix Cache 命中数)、new_blocks、block_table、free_blocks 变化 |
| `[SCHED] STEP`       | Prefill/Decode 交替执行，num_tokens 和 cached 的推进                                           |
| `[BLOCK] DEALLOCATE` | Sequence 完成或 Preemption 时的 Block 回收                                                     |
| `[SCHED] PREEMPT`    | 显存不足时的抢占 (调低 `--gpu-memory-utilization` 更容易观察)                                  |
