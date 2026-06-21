# 编译 CUDA Hook 共享库
# 只需 gcc + libdl, 不需要 CUDA Toolkit (符号由目标进程提供)

CC = gcc
CFLAGS = -shared -fPIC -Wall -O2
LDFLAGS = -ldl
TARGET = libcuda_hook.so
SRC = cuda_hook.c

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)
	@echo "[OK] $@ built"

# 快速测试: hook ls 命令 (不需要 GPU, 验证 LD_PRELOAD 和递归守卫)
test: $(TARGET)
	@echo "=== 测试: 无 GPU 模式 (拦截 ls 的 cudaMalloc 调用 — 不会发生, 但验证 hook 加载) ==="
	LD_PRELOAD=./$(TARGET) CUDA_MEM_QUOTA_MB=100 ls / > /dev/null 2>&1 && echo "[OK] Hook loaded, no crash" || echo "[FAIL] Hook crashed"
	@echo "=== 测试: 有 GPU 模式 (需要 CUDA) ==="
	@echo "    LD_PRELOAD=./$(TARGET) CUDA_MEM_QUOTA_MB=512 python3 -c 'import torch; t=torch.zeros(1000,1000).cuda(); print(t.sum())'"

clean:
	rm -f $(TARGET)
