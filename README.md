# 代码审查 Agent（Code Review Agent）

一个用 **纯 Python 标准库** 实现的「代码助手 Agent」，用于自动分析代码质量、发现潜在 Bug、给出改进建议。


## 一、项目简介

本项目选择作业的 **「代码审查 Agent」** 方向，实现了：

- ✅ **基本 Agent 循环**：输入 → 推理 → 工具调用 → 输出（ReAct 模式）
- ✅ **多种工具**：文件读取、目录列举、语法检查、基于 AST 的静态分析
- ✅ **命令行 + 简易 Web 界面** 两种交互方式
- ✅ **上下文记忆**：对话历史 + 会话持久化
- ✅ **错误处理与重试**：异常分类、指数退避、工具出错反馈
- ✅ **离线 Mock 模式**：不填 API key 也能完整跑通整个 Agent 循环

## 二、目录结构

```
code-review-agent/
├── run.py                  # 启动入口：python run.py <目标>
├── config.example.json     # 配置文件示例（填 API key 后改名 config.json）
├── requirements.txt        # 零第三方依赖说明
├── README.md               # 本文件：项目说明与使用手册
├── Design.md               # 设计文档：架构、Agent 循环、关键决策
├── agent/
│   ├── __init__.py
│   ├── prompts.py          # prompt 设计（系统提示/任务构造/输出解析）
│   ├── llm.py              # LLM Provider 抽象（Mock + OpenAI 兼容实现）
│   ├── tools.py            # 工具集（读取/列举/语法检查/AST 分析）
│   ├── memory.py           # 上下文记忆
│   ├── core.py             # Agent 核心循环（ReAct）
│   ├── main.py             # 命令行入口
│   └── webapp.py           # 简易 Web 界面
├── examples/
│   └── bad_code.py         # 含多处问题的示例代码（用于演示）
└── tests/
    └── test_agent.py       # 单元测试
```

## 三、快速开始（离线演示，无需 API key）

环境要求：**Python 3.6+**（推荐 3.8+），无需安装任何第三方库。

```bash
# 进入项目目录
cd code-review-agent

# 审查示例代码（内置 Mock 模式，离线即可运行）
python run.py examples/bad_code.py

# 打印每一步推理与工具调用过程
python run.py examples/bad_code.py --verbose

# 审查整个目录
python run.py . 

# 把报告保存为文件
python run.py examples/bad_code.py -o report.md
```

运行 `--verbose` 时可以看到完整的 Agent 循环：

```
  [step 1] 思考：开始审查前，先读取目标文件的源代码，了解要审什么。
  [step 1] 动作：read_file
  [step 2] 思考：已拿到代码，接下来做静态分析。
  [step 2] 动作：analyze
  [step 3] 动作：answer
```

## 四、接入真实 LLM

框架内置了 **OpenAI 兼容接口**，支持 OpenAI、通义千问（DashScope）等。

1. 复制配置模板：

   ```bash
   cp config.example.json config.json
   ```

2. 填入你的 API key，并设置 `provider`：

   ```json
   {
     "provider": "dashscope",
     "dashscope": {
       "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
       "api_key": "sk-你的通义千问密钥",
       "model": "qwen-plus"
     }
   }
   ```

3. 运行：

   ```bash
   python run.py examples/bad_code.py --config config.json
   ```

也支持用环境变量传入密钥（`OPENAI_API_KEY` / `DASHSCOPE_API_KEY`），
或命令行指定：`--provider dashscope --model qwen-plus`。

> 未配置 key 时会自动回退到 Mock 模式，保证任何时候都能跑。

## 五、Web 界面

```bash
python run.py examples/bad_code.py --web
# 浏览器打开 http://127.0.0.1:8000
```

在文本框粘贴代码（或填本地文件路径），点击「开始审查」即可。

## 六、单元测试

```bash
python -m unittest discover -s tests -v
```

## 七、Agent 工作原理（简述）

1. **输入**：用户指定要审查的文件/目录；
2. **推理**：LLM 根据系统提示与历史，决定下一步（调用工具 or 给出结论）；
3. **工具调用**：执行 `read_file` / `analyze` 等工具，结果写回上下文；
4. **输出**：LLM 判断信息足够后，输出最终审查报告。

详细的架构与设计决策见 [Design.md](./Design.md)。
