# 模块 1 配套代码 — Linux 基础与容器技术入门

本目录包含 4 个实验脚本，对应 PPT 中的 5 个课堂动手环节。

## 环境要求

- Ubuntu 22.04 LTS (x86_64)
- Docker Engine ≥ 24.0
- `cgroup-tools`、`stress`
- 部分实验需要 `sudo`

## 实验列表

| 脚本                      | 对应 PPT          | 内容                                      | 时长   |
| ------------------------- | ----------------- | ----------------------------------------- | ------ |
| `01_namespace_demo.sh`    | 第 14 页 [动手 1] | 查看 namespace，使用 unshare 创建隔离环境 | ~5 min |
| `02_cgroup_demo.sh`       | 第 15 页 [动手 2] | cgroup 内存限制 50MB，验证资源隔离        | ~4 min |
| `03_overlayfs_demo.sh`    | 第 22 页 [动手 3] | 手动创建 OverlayFS，验证 Copy-on-Write    | ~5 min |
| `04_docker_layer_demo.sh` | 第 25 页 [动手 4] | Docker 镜像分层分析，缓存机制演示         | ~5 min |

## 运行方法

```bash
# 给脚本添加执行权限
chmod +x *.sh

# 按 PPT 顺序执行
./01_namespace_demo.sh
./02_cgroup_demo.sh
./03_overlayfs_demo.sh
./04_docker_layer_demo.sh
```

所有脚本都是交互式的，运行后按提示操作即可。部分步骤需要 `sudo`，会提示输入密码。

---

## 实验 1: Namespace 进程隔离

**运行**: `./01_namespace_demo.sh`

**预期输出**:

```text
--- Step 1: 查看当前 Shell 的 namespace ---
命令: ls -la /proc/self/ns/
lrwxrwxrwx ... ipc -> ipc:[4026531839]
lrwxrwxrwx ... mnt -> mnt:[4026531841]
lrwxrwxrwx ... net -> net:[4026532000]
lrwxrwxrwx ... pid -> pid:[4026531836]
lrwxrwxrwx ... uts -> uts:[4026531838]
```

**核心操作**:

```bash
sudo unshare --pid --mount --fork --mount-proc /bin/bash
# 在隔离环境中:
echo "容器内 PID: $$"     # 应该显示 1
ps aux                     # 只能看到隔离环境内的进程
exit                       # 退出
```

---

## 实验 2: Cgroup 内存限制

**运行**: `./02_cgroup_demo.sh`

**预期输出**:

```text
检测到 cgroup v2
已创建: /sys/fs/cgroup/demo
已设置: memory.max = 52428800 bytes (50 MB)
当前 Shell (PID=12345) 已加入 cgroup demo
memory.max:    52428800 bytes
memory.current: 1234567 bytes
```

**核心验证**: 尝试 `stress --vm 1 --vm-bytes 100M`（在 50MB 限制下会触发 OOM killer）。如果没有 `stress`，脚本设置的限制仅对当前 shell 及其子进程生效。

---

## 实验 3: OverlayFS 分层存储

**运行**: `./03_overlayfs_demo.sh`

**预期输出**:

```text
=== lower 层 (只读，不变) ===
原始配置: debug=false

=== upper 层 (可写，包含修改) ===
  .../upper/config.txt: 修改后配置: debug=true
  .../upper/runtime.log: 这是容器运行时新建的文件

=== merged 层 (统一视图) ===
修改后配置: debug=true
这是容器运行时新建的文件

关键观察:
  - lower 层的 config.txt 没变
  - 修改出现在 upper 层
  - 这就是 Docker 的 Copy-on-Write 机制!
```

---

## 实验 4: Docker 镜像分层分析

**运行**: `./04_docker_layer_demo.sh`

**预期输出**:

```text
--- Step 1: 查看 ubuntu:22.04 镜像的分层 ---
IMAGE          CREATED       CREATED BY                                      SIZE
ubuntu:22.04   ...           /bin/sh -c #(nop) CMD ["/bin/bash"]            0B
...            ...           /bin/sh -c #(nop) ADD file:...                  77.8MB

--- Step 3: 分析镜像分层 ---
layer-demo:v1
IMAGE          CREATED BY                                      SIZE
...            /bin/sh -c apt-get clean && rm -rf ...          0B
...            /bin/sh -c apt-get install -y -qq vim           67MB
...            /bin/sh -c apt-get install -y -qq curl          15MB
...            /bin/sh -c apt-get update -qq                   40MB
...            /bin/sh -c #(nop) CMD ["/bin/bash"]             0B

--- Step 5: 镜像缓存演示 ---
重新构建（应该全部 CACHED）:
Step 1/5 : FROM ubuntu:22.04
 ---> Using cache
Step 2/5 : RUN apt-get update -qq
 ---> Using cache
...

修改 Dockerfile 中间行后重新构建:
Step 3/5 : RUN apt-get install -y -qq curl wget
 ---> Running in ...   ← 缓存失效，重新执行!
```

**缓存规则**: 从第一个发生变化的指令开始，后续所有层都需要重建。

---

## 清理

每个脚本在结束时都会询问是否清理，选择 `y` 即可。或者手动清理：

```bash
# 清理 cgroup (如果未自动清理)
sudo rmdir /sys/fs/cgroup/demo 2>/dev/null

# 清理 overlay 演示文件 (如果未自动清理)
sudo umount ~/overlay-demo/merged 2>/dev/null
rm -rf ~/overlay-demo

# 清理 Docker 镜像
docker rmi layer-demo:v1 layer-demo:v2 2>/dev/null
```
