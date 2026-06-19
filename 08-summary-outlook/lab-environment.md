# 模块 8：课程总结与 AI Infra 前沿展望 — 实验环境说明

## 环境要求

本模块的动手实验以 Python 为主，不需要 GPU。只需要能运行 Python 3.10+ 的环境。

### 软件要求

| 软件 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.10 | Agent Demo |
| pip | latest | 包安装 |
| requests / openai | latest | API 调用 |

---

## 环境搭建

```bash
python3 -m venv agent-demo
source agent-demo/bin/activate
pip install openai requests
```

---

## 可选环境

如果想体验完整的 Agent 系统，可安装：

```bash
# Claude Code (如果已安装)
# 已集成 Agent + Reasoning 能力

# 或使用 openhands (开源的 AI 编程 Agent)
pip install openhands
```

---

## 环境验证

```bash
python -c "import openai; print('OK')"
```
