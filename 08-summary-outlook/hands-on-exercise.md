# 模块 8：课程总结与 AI Infra 前沿展望 — 课堂动手题

## 题目：搭建 Agent + 推理服务端到端 Demo

### 题目描述

使用 Python 实现一个简化的代码问答 Agent 系统，结合 vLLM 推理后端，展示 Agent Infra 与 AI Infra 的融合。

### 预计时间
15–20 分钟

---

## Step 1: 启动推理后端 (3 min)

```bash
# 如果有 GPU
vllm serve Qwen/Qwen2.5-0.5B-Instruct --port 8000 &

# 或使用 OpenAI 兼容的 API (需要 API Key)
# export OPENAI_API_KEY=sk-xxx
# export OPENAI_BASE_URL=https://api.openai.com/v1
```

```bash
# 验证
curl http://localhost:8000/v1/models
```

---

## Step 2: 实现简化的 Agent 框架 (10 min)

```python
# simple_agent.py
"""
一个极简的代码问答 Agent，展示:
1. Agent 循环 (Plan → Act → Observe → Reflect)
2. 工具调用 (执行 Python 代码)
3. 记忆 (对话历史)
"""
import subprocess
import json
from openai import OpenAI

# 配置
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)
MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

# =========== 工具定义 ===========
def execute_python(code: str) -> str:
    """在沙箱中执行 Python 代码并返回结果"""
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return f"执行成功:\n{result.stdout}"
        else:
            return f"执行错误:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "执行超时 (10s)"

TOOLS = {
    "execute_python": {
        "function": execute_python,
        "description": "执行 Python 代码并返回结果。参数: code (str)"
    }
}

# =========== Agent 主循环 ===========
SYSTEM_PROMPT = """你是一个代码助手 Agent。你可以:
1. 分析用户的代码问题
2. 使用 execute_python 工具执行代码验证你的答案
3. 根据执行结果调整你的回答

当需要执行代码时，请严格按以下 JSON 格式输出:
{"action": "execute_python", "code": "print('hello world')"}

当不需要再执行代码时，直接回答用户的问题。"""

class SimpleAgent:
    def __init__(self, max_steps=5):
        self.max_steps = max_steps
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def step(self, user_input=None):
        if user_input:
            self.messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model=MODEL,
            messages=self.messages,
            max_tokens=500,
            temperature=0.1
        )
        answer = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": answer})
        return answer

    def run(self, question: str):
        print(f"🤔 问题: {question}\n")
        self.messages.append({"role": "user", "content": question})

        for step in range(self.max_steps):
            print(f"--- Step {step+1} ---")
            response = self.step()

            # 检查是否有工具调用
            try:
                if '{"action"' in response:
                    # 提取 JSON
                    start = response.index('{"action"')
                    end = response.index('}', start) + 1
                    action_json = json.loads(response[start:end])

                    if action_json.get("action") == "execute_python":
                        code = action_json["code"]
                        print(f"🔧 执行代码:\n{code}")
                        result = execute_python(code)
                        print(f"📋 结果:\n{result}\n")
                        # 将结果作为观察反馈给 Agent
                        self.messages.append({
                            "role": "user",
                            "content": f"代码执行结果:\n{result}\n\n请根据结果继续回答。"
                        })
                        continue
            except (json.JSONDecodeError, ValueError):
                pass

            # 没有工具调用，输出最终答案
            print(f"✅ 最终回答:\n{response}")
            return response

        print("⚠️ 达到最大步数限制")
        return self.messages[-1]["content"]

# =========== 测试 ===========
if __name__ == "__main__":
    agent = SimpleAgent(max_steps=3)

    # 问题 1: 简单代码问题
    agent.run("请编写 Python 代码计算斐波那契数列的前 10 项，并验证结果")
    print("\n" + "="*60 + "\n")

    # 问题 2: 调试问题
    agent2 = SimpleAgent(max_steps=3)
    agent2.run("以下代码有什么问题？请修复并验证:\n"
               "def add(a, b): return a + b\n"
               "print(add('1', 2))")
```

---

## Step 3: 运行与分析 (5 min)

```bash
python simple_agent.py
```

观察:
1. **Agent 循环**: Plan (理解问题) → Act (执行代码) → Observe (读取结果) → Reflect (调整回答)
2. **工具调用**: Agent 何时决定执行代码而不是直接回答？
3. **推理后端**: Agent 的每一步都需要调用推理服务 → 这就是 AI Infra + Agent Infra 的结合点

---

## 讲解要点

### 1. Agent 与 AI Infra 的关系
- 推理引擎 (vLLM) 提供每次推理的能力
- Agent 框架在此基础上添加: 工具调用 + 记忆 + 多步规划 + 安全执行
- "AI Infra 提供算力，Agent Infra 提供行动力"

### 2. Agent 对推理的新需求
- **超长上下文**: Agent 历史 + 工具结果 + 系统 Prompt → 轻松超过 10K tokens
- **Prefix Caching 极有价值**: 系统 Prompt + 工具定义固定，反复命中
- **低延迟要求**: Agent 多步推理 → 每步的延迟都会被放大

### 3. Agent 基础设施的四大支柱
- **Harness**: 上下文窗口管理 + 工具调度 (OpenHarness/Agent Harness)
- **Memory**: 持久化记忆 + 自动检索 (Mem0/MemMachine/文件级记忆)
- **Sandbox**: 安全执行代码/Shell (Bubblewrap/Docker/Firecracker)
- **Protocol**: 标准化的工具调用协议 (MCP/Function Calling)

### 4. 课程技术栈在 Agent 中的应用
- 模块 1 (容器): Sandbox 隔离
- 模块 3 (GPU 虚拟化): 多 Agent 共享 GPU
- 模块 4 (K8s): Agent 服务的编排和调度
- 模块 5 (vLLM): Agent 的推理引擎
- 模块 6 (KV Cache): 长上下文 Prefix Caching
- 模块 7 (MaaS): Agent 推理的 API 化管理
