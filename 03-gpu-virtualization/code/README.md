# 模块 3 配套代码 — GPU 虚拟化与容器化实践

## 文件说明

| 文件               | 内容                      | 对应 PPT                     |
| ------------------ | ------------------------- | ---------------------------- |
| `01_mymalloc.c`    | LD_PRELOAD malloc hook 库 | 第 12 页 + 第 33 页 [动手 1] |
| `02_test_malloc.c` | 配额测试程序              | 第 33 页 [动手 1] 测试用     |

## 环境要求

- Linux (需要 `ld.so` 支持 LD_PRELOAD)
- GCC

## 实验：LD_PRELOAD malloc hook

### 编译

```bash
gcc -shared -fPIC 01_mymalloc.c -o libmymalloc.so -ldl
```

### 运行

```bash
# Step 1: 编译 hook 库
gcc -shared -fPIC 01_mymalloc.c -o libmymalloc.so -ldl

# Step 2: 快速验证 — 拦截 ls
LD_PRELOAD=./libmymalloc.so ls /tmp

# Step 3: 编译并运行配额测试
gcc 02_test_malloc.c -o test_malloc
LD_PRELOAD=./libmymalloc.so ./test_malloc
```

### 预期输出 (H100 实测)

```text
--- 分配 40MB ---
[HOOK] malloc(41943040) → 0x7f...  (已用 41947136 / 104857600, 40.0%)
p1 = 0x7f...

--- 分配 40MB ---
[HOOK] malloc(41943040) → 0x7f...  (已用 83890176 / 104857600, 80.0%)
p2 = 0x7f...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[QUOTA EXCEEDED] malloc(31457280 bytes) 被拒绝
  已用: 83890176 / 配额: 104857600 (80.0%)
  类比: HAMi 中 cuMemAlloc 超配额 → 返回 CUDA_ERROR_OUT_OF_MEMORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

--- 分配 30MB (应超 100MB 配额) ---
p3 = (nil) (NULL=配额生效)
```

### 关键理解

HAMi 的 `libvgpu.so` 拦截 `cuMemAlloc` 的原理与此完全相同：

```c
// 我们的 demo
void *malloc(size_t size) {
    real_malloc = dlsym(RTLD_NEXT, "malloc");
    if (used + size > quota) return NULL;  // 超配额
    void *p = real_malloc(size);
    used += size;
    return p;
}

// HAMi 的做法 (伪代码)
CUresult cuMemAlloc(CUdeviceptr *ptr, size_t size) {
    real_cuMemAlloc = dlsym(RTLD_NEXT, "cuMemAlloc");
    if (used_vram + size > vram_quota) return CUDA_ERROR_OUT_OF_MEMORY;
    CUresult r = real_cuMemAlloc(ptr, size);
    used_vram += size;
    return r;
}
```
