# Makefile — 模块 2: GPU 硬件架构与 CUDA 编程入门
# 用法: make all       编译所有程序
#       make run       编译并运行
#       make clean     清理
#       make profile   使用 Nsight Compute 分析

NVCC = nvcc
# GPU 架构: 自动检测 (nvidia-smi) 或手动覆盖 (make SM=89)。
# 无 GPU 时默认 sm_70，编译产物仅用于语法检查，无法在本机运行。
SM_DETECT := $(shell nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null | head -1 | tr -d '.')
ifeq ($(SM_DETECT),)
  SM = 70
else
  SM = $(SM_DETECT)
endif
NVCCFLAGS = -O2 -arch=sm_$(SM)
LDFLAGS =

TARGETS = vec_add matmul_naive matmul_tiled device_query

.PHONY: all run clean profile

all: $(TARGETS)

vec_add: 01_vec_add.cu
	$(NVCC) $(NVCCFLAGS) $< -o $@

matmul_naive: 02_matmul_naive.cu
	$(NVCC) $(NVCCFLAGS) $< -o $@

matmul_tiled: 03_matmul_tiled.cu
	$(NVCC) $(NVCCFLAGS) $< -o $@

device_query: 04_device_query.cu
	$(NVCC) $(NVCCFLAGS) $< -o $@

run: all
	@echo "========================================="
	@echo "  1. GPU 设备查询"
	@echo "========================================="
	./device_query
	@echo ""
	@echo "========================================="
	@echo "  2. 向量加法 (CPU vs GPU)"
	@echo "========================================="
	./vec_add
	@echo ""
	@echo "========================================="
	@echo "  3. 矩阵乘法 — Naive (Global Memory)"
	@echo "========================================="
	./matmul_naive
	@echo ""
	@echo "========================================="
	@echo "  4. 矩阵乘法 — Tiled (Shared Memory)"
	@echo "========================================="
	./matmul_tiled
	@echo ""

profile:
	@echo "使用 Nsight Compute 分析 tiled 版本..."
	ncu --set full -o matmul_tiled_report ./matmul_tiled
	@echo "报告已生成: matmul_tiled_report.ncu-rep"

clean:
	rm -f $(TARGETS) *.ncu-rep
