# 编译 CUDA Hook 共享库 + 测试程序
# libcuda_hook.so: 只需 gcc + libdl, 不需要 CUDA Toolkit (符号由目标进程提供)
# test_hook:       需要 nvcc (CUDA Toolkit)

CC = gcc
CFLAGS = -shared -fPIC -Wall -O2
LDFLAGS = -ldl
TARGET = libcuda_hook.so
SRC = cuda_hook.c

NVCC = nvcc
NVCC_FLAGS = --cudart=shared  # 必须动态链接 libcudart, LD_PRELOAD 才能拦截 CUDA 符号
TEST_SRC = test_hook.cu
TEST_BIN = test_hook

.PHONY: all clean test test-gpu

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)
	@echo "[OK] $@ built"

# 快速自检: hook ls 命令 (不需要 GPU, 验证 hook 加载不崩溃)
test: $(TARGET)
	@echo "=== 测试: 无 GPU 模式 (验证 hook 加载 + 初始化日志) ==="
	LD_PRELOAD=./$(TARGET) CUDA_MEM_QUOTA_MB=100 CUDA_CORE_RATE=20 CUDA_CORE_CAPACITY=5 ls / > /dev/null 2>&1 && echo "[OK] Hook loaded, no crash" || echo "[FAIL] Hook crashed"

# 编译并运行 GPU 测试 (需要 nvcc + GPU)
test-gpu: $(TARGET) $(TEST_BIN)
	@echo "=== 测试: GPU 模式 (验证显存配额 + 算力限速) ==="
	LD_PRELOAD=./$(TARGET) CUDA_MEM_QUOTA_MB=128 CUDA_CORE_RATE=5 CUDA_CORE_CAPACITY=3 ./$(TEST_BIN)

$(TEST_BIN): $(TEST_SRC)
	$(NVCC) $(NVCC_FLAGS) -o $@ $<
	@echo "[OK] $@ built"

clean:
	rm -f $(TARGET) $(TEST_BIN)
