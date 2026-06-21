# 模块 8 — 课程大作业骨架代码

每个方向提供可运行的骨架框架，关键位置标注 `# TODO:`。学生只需填充核心逻辑。

## 目录结构

```text
code/
├── README.md
├── gpu-container-hook/    # 方向 A: 容器+拦截 (3 files + README)
│   ├── README.md
│   ├── cuda_hook.c
│   ├── Makefile
│   └── Dockerfile
├── k8s-gateway/           # 方向 B: K8s 调度 (6 files + README)
│   ├── README.md
│   ├── app.py
│   ├── mock_vllm.py
│   ├── docker-compose.yml
│   ├── k8s-backend.yaml
│   ├── k8s-gateway.yaml
│   ├── k8s-configmap.yaml
│   └── k8s-hpa.yaml
└── kvcache-simulator/     # 方向 C: KV Cache (4 files + README)
    ├── README.md
    ├── calculator.py
    ├── simulator.py
    ├── lru_cache.py
    └── visualize.py
```

## 使用方法

1. 选择方向，进入对应目录
2. 搜索所有 `# TODO:` 注释
3. 根据课程知识和注释提示完成代码
4. 运行验证，收集实验数据
5. 撰写技术报告
