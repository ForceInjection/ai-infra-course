# 模块2 高级：GPU 内存管理 — 实验环境说明

## 环境要求

| 项目         | 最低配置                              |
| ------------ | ------------------------------------- |
| GPU          | NVIDIA GPU (Compute Capability ≥ 7.0) |
| CUDA Toolkit | ≥ 12.0                                |
| Python       | ≥ 3.8                                 |
| 操作系统     | Linux (需要 `libcudart.so`)           |

## 环境搭建

```bash
# 01_dma_bandwidth.py 使用 ctypes 直接调用 CUDA API，无需额外依赖
python3 -c "import ctypes; print('OK')"
```

## 实验脚本

```bash
# 带宽测试 (pageable vs pinned)
python3 code/01_dma_bandwidth.py

# 指定不同数据大小
python3 code/01_dma_bandwidth.py --sizes 0.1 0.5 1 2 4
```
