#!/bin/bash
# 实验 3: OverlayFS 分层存储演示
# 对应课程: 模块 1 — Linux 基础与容器技术入门
# PPT 页码: 第 22 页 [动手 3]

set -e

DEMO_DIR="$HOME/overlay-demo"

echo "========================================="
echo "  实验 3: OverlayFS 分层存储演示"
echo "  模块 1 — Linux 基础与容器技术入门"
echo "========================================="
echo ""

# Step 1: 创建目录结构
echo "--- Step 1: 创建底层 (lowerdir) 文件 ---"
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"/{lower,upper,work,merged}

# 在 lower 层创建文件（模拟镜像只读层）
echo "这是基础镜像层的文件" > "$DEMO_DIR/lower/base.txt"
echo "原始配置: debug=false"  > "$DEMO_DIR/lower/config.txt"
mkdir -p "$DEMO_DIR/lower/app"
echo "v1.0" > "$DEMO_DIR/lower/app/version.txt"

echo "lower 层内容:"
find "$DEMO_DIR/lower" -type f -exec echo "  {}: $(cat {})" \;
echo ""

# Step 2: 挂载 OverlayFS
echo "--- Step 2: 挂载 OverlayFS ---"
echo "命令: mount -t overlay overlay -o lowerdir=lower,upperdir=upper,workdir=work merged"
sudo mount -t overlay overlay \
    -o lowerdir="$DEMO_DIR/lower",upperdir="$DEMO_DIR/upper",workdir="$DEMO_DIR/work" \
    "$DEMO_DIR/merged"
echo "已挂载到 $DEMO_DIR/merged"
echo ""

# Step 3: 查看合并视图
echo "--- Step 3: 查看合并视图 (merged) ---"
echo "merged 层内容 (lower + upper 的合并视图):"
find "$DEMO_DIR/merged" -type f -exec echo "  {}: $(cat {})" \;
echo ""

# Step 4: 写操作 — 验证 Copy-on-Write
echo "--- Step 4: 写操作 — 验证 Copy-on-Write ---"
echo "修改 config.txt..."
echo "修改后配置: debug=true" > "$DEMO_DIR/merged/config.txt"
echo "创建新文件..."
echo "这是容器运行时新建的文件" > "$DEMO_DIR/merged/runtime.log"
echo ""

# Step 5: 观察各层变化
echo "=== lower 层 (只读，不变) ==="
cat "$DEMO_DIR/lower/config.txt"
echo ""
echo "=== upper 层 (可写，包含修改) ==="
find "$DEMO_DIR/upper" -type f -exec echo "  {}: $(cat {})" \;
echo ""
echo "=== merged 层 (统一视图) ==="
cat "$DEMO_DIR/merged/config.txt"
cat "$DEMO_DIR/merged/runtime.log"
echo ""

echo "========================================="
echo "  关键观察:"
echo "  - lower 层的 config.txt 没变"
echo "  - 修改出现在 upper 层"
echo "  - 新文件出现在 upper 层"
echo "  - 这就是 Docker 的 Copy-on-Write 机制!"
echo "========================================="
echo ""

# 清理
echo "是否卸载并清理? (y/n)"
read -r answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    sudo umount "$DEMO_DIR/merged"
    rm -rf "$DEMO_DIR"
    echo "已清理"
fi
