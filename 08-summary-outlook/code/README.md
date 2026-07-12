# 模块 8 — 配套代码

## 目录

```text
code/
├── README.md
├── REPORT_TEMPLATE.md     # 技术报告模板
├── gpu-hook/              # GPU 资源拦截: LD_PRELOAD CUDA hook (显存配额 + 算力限速)
├── k8s-gateway/           # K8s GPU 调度: Flask 网关 + vLLM 后端 + HPA 弹性伸缩
└── kvcache-simulator/     # KV Cache 显存管理: 计算工具 + 碎片模拟器 + LRU Cache
```

每个子目录内含独立的 `README.md`。
