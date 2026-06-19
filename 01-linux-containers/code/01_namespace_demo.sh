#!/bin/bash
# 实验 1: Namespace 进程隔离演示
# 对应课程: 模块 1 — Linux 基础与容器技术入门
# PPT 页码: 第 14 页 [动手 1]

set -e

echo "========================================="
echo "  实验 1: Linux Namespace 进程隔离"
echo "  模块 1 — Linux 基础与容器技术入门"
echo "========================================="
echo ""

# Step 1: 查看当前进程的 namespace
echo "--- Step 1: 查看当前 Shell 的 namespace ---"
echo "命令: ls -la /proc/self/ns/"
ls -la /proc/self/ns/
echo ""

echo "--- Step 2: 查看系统中所有 namespace ---"
echo "命令: lsns | head -10"
lsns 2>/dev/null | head -10 || echo "lsns 不可用，使用 ls /proc/*/ns/ 替代"
echo ""

# Step 2: 使用 unshare 创建隔离环境
echo "--- Step 3: 使用 unshare 创建 PID + Mount 隔离环境 ---"
echo ""
echo "  在新 namespace 中:"
echo "    - PID 将从 1 开始"
echo "    - 只能看到隔离环境内的进程"
echo "    - 宿主机上的其他进程不可见"
echo ""
echo "  执行命令:"
echo "    sudo unshare --pid --mount --fork --mount-proc /bin/bash"
echo ""
echo "  在隔离环境中执行:"
echo '    echo "容器内 PID: $$"     # 应该显示 1'
echo "    ps aux                     # 只能看到隔离环境内的进程"
echo "    exit                       # 退出隔离环境"
echo ""
echo "  是否现在进入隔离环境? (y/n)"
read -r answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    echo "进入隔离环境... (输入 exit 退出)"
    sudo unshare --pid --mount --fork --mount-proc /bin/bash
    echo "已退出隔离环境"
fi
echo ""

echo "========================================="
echo "  实验 1 完成"
echo "========================================="
