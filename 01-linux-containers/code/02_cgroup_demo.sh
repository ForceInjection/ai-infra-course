#!/bin/bash
# 实验 2: Cgroup 资源限制演示
# 对应课程: 模块 1 — Linux 基础与容器技术入门
# PPT 页码: 第 15 页 [动手 2]

set -e

echo "========================================="
echo "  实验 2: Cgroup 内存限制演示"
echo "  模块 1 — Linux 基础与容器技术入门"
echo "========================================="
echo ""

# 检测 cgroup 版本
CGROUP_V2=0
if [ -f /sys/fs/cgroup/cgroup.controllers ]; then
    CGROUP_V2=1
    echo "检测到 cgroup v2"
else
    echo "检测到 cgroup v1"
fi
echo ""

if [ $CGROUP_V2 -eq 1 ]; then
    # === cgroup v2 (Ubuntu 22.04+) ===
    CGROUP_PATH="/sys/fs/cgroup/demo"
    MEMORY_LIMIT=$((50 * 1024 * 1024))  # 50 MB

    echo "--- Step 1: 创建 cgroup (v2) ---"
    sudo mkdir -p "$CGROUP_PATH"
    echo "+memory" | sudo tee /sys/fs/cgroup/cgroup.subtree_control > /dev/null 2>&1 || true
    echo "已创建: $CGROUP_PATH"

    echo ""
    echo "--- Step 2: 设置内存限制为 50 MB ---"
    echo "$MEMORY_LIMIT" | sudo tee "$CGROUP_PATH/memory.max"
    echo "已设置: memory.max = $MEMORY_LIMIT bytes (50 MB)"

    echo ""
    echo "--- Step 3: 将当前 Shell 加入 cgroup ---"
    echo $$ | sudo tee "$CGROUP_PATH/cgroup.procs"
    echo "当前 Shell (PID=$$) 已加入 cgroup demo"

    echo ""
    echo "--- Step 4: 查看限制效果 ---"
    echo "memory.max:    $(cat $CGROUP_PATH/memory.max) bytes"
    echo "memory.current: $(cat $CGROUP_PATH/memory.current) bytes"
else
    # === cgroup v1 ===
    CGROUP_PATH="/sys/fs/cgroup/memory/demo"
    MEMORY_LIMIT=$((50 * 1024 * 1024))

    echo "--- Step 1: 创建 cgroup (v1) ---"
    sudo mkdir -p "$CGROUP_PATH"
    echo "已创建: $CGROUP_PATH"

    echo ""
    echo "--- Step 2: 设置内存限制为 50 MB ---"
    echo "$MEMORY_LIMIT" | sudo tee "$CGROUP_PATH/memory.limit_in_bytes"
    echo "已设置: memory.limit_in_bytes = $MEMORY_LIMIT bytes (50 MB)"

    echo ""
    echo "--- Step 3: 将当前 Shell 加入 cgroup ---"
    echo $$ | sudo tee "$CGROUP_PATH/cgroup.procs"
    echo "当前 Shell (PID=$$) 已加入 cgroup demo"

    echo ""
    echo "--- Step 4: 查看限制效果 ---"
    echo "memory.limit_in_bytes: $(cat $CGROUP_PATH/memory.limit_in_bytes) bytes"
    echo "memory.usage_in_bytes:  $(cat $CGROUP_PATH/memory.usage_in_bytes) bytes"
fi

echo ""
echo "========================================="
echo "  限制已生效。尝试分配超过 50MB 内存将被 OOM killer 终止。"
echo "  stress 测试: stress --vm 1 --vm-bytes 100M"
echo "========================================="
echo ""

# 清理选项
echo "是否清理 cgroup? (y/n)"
read -r answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    # 先将进程移出
    echo $$ | sudo tee /sys/fs/cgroup/cgroup.procs 2>/dev/null || true
    sudo rmdir "$CGROUP_PATH" 2>/dev/null || true
    echo "已清理 cgroup"
fi
