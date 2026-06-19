#!/bin/bash
# 实验 4: Docker 镜像分层分析
# 对应课程: 模块 1 — Linux 基础与容器技术入门
# PPT 页码: 第 25 页 [动手 4]

set -e

echo "========================================="
echo "  实验 4: Docker 镜像分层分析"
echo "  模块 1 — Linux 基础与容器技术入门"
echo "========================================="
echo ""

# Step 1: 查看已有镜像的分层
echo "--- Step 1: 查看 ubuntu:22.04 镜像的分层 ---"
echo "命令: docker history ubuntu:22.04"
docker history ubuntu:22.04 2>/dev/null || {
    echo "拉取 ubuntu:22.04..."
    docker pull ubuntu:22.04
    docker history ubuntu:22.04
}
echo ""

# Step 2: 构建多层镜像
echo "--- Step 2: 构建多层演示镜像 ---"
BUILD_DIR=$(mktemp -d)
cd "$BUILD_DIR"

cat > Dockerfile << 'EOF'
FROM ubuntu:22.04
# 第 2 层: 更新包索引
RUN apt-get update -qq
# 第 3 层: 安装 curl
RUN apt-get install -y -qq curl
# 第 4 层: 安装 vim
RUN apt-get install -y -qq vim
# 第 5 层: 清理 (减小镜像体积)
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
EOF

echo "Dockerfile 内容:"
cat Dockerfile
echo ""

echo "构建镜像..."
docker build -t layer-demo:v1 . 2>&1 | grep -E "Step|Successfully"
echo ""

# Step 3: 分析分层
echo "--- Step 3: 分析镜像分层 ---"
echo "命令: docker history layer-demo:v1"
docker history layer-demo:v1
echo ""

# Step 4: 查看镜像层详情
echo "--- Step 4: 查看镜像层详细信息 ---"
echo "层数量:"
docker image inspect layer-demo:v1 --format '{{len .RootFS.Layers}} 个层'
echo ""

# Step 5: 演示缓存
echo "--- Step 5: 镜像缓存演示 ---"
echo "重新构建（应该全部 CACHED）:"
docker build -t layer-demo:v1 . 2>&1 | grep -E "CACHED|Step"
echo ""

echo "修改 Dockerfile 中间行后重新构建..."
cat > Dockerfile << 'EOF'
FROM ubuntu:22.04
RUN apt-get update -qq
RUN apt-get install -y -qq curl wget
RUN apt-get install -y -qq vim
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
EOF

echo "重新构建（注意缓存从哪一行开始失效）:"
docker build -t layer-demo:v2 . 2>&1 | grep -E "CACHED|Step|--->"
echo ""

# 清理
echo "清理构建目录和镜像..."
cd /
rm -rf "$BUILD_DIR"
docker rmi layer-demo:v1 layer-demo:v2 2>/dev/null || true

echo ""
echo "========================================="
echo "  实验 4 完成"
echo "========================================="
