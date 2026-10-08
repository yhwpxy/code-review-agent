# -*- coding: utf-8 -*-
"""命令行入口。

用法示例：
    python run.py examples/bad_code.py              # Mock 模式，离线演示
    python run.py examples/bad_code.py --verbose    # 打印每一步推理与工具调用
    python run.py examples/bad_code.py -o report.md # 保存报告
    python run.py . --config config.json            # 用真实 API 审查整个目录
    python run.py examples/bad_code.py --web        # 启动简易 Web 界面
"""

import argparse
import json
import os
import sys

from .core import CodeReviewAgent
from .llm import create_provider
from .memory import Memory


def load_config(path):
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except ValueError as e:
        print("警告：配置文件解析失败（%s），已忽略。" % e)
        return {}


def build_parser():
    p = argparse.ArgumentParser(
        prog="code-review-agent",
        description="代码审查 Agent（Code Review Agent）：分析代码质量、找出潜在 Bug、给出改进建议。",
    )
    p.add_argument("target", help="要审查的文件或目录")
    p.add_argument("--mock", action="store_true", help="使用离线 Mock（无需 API key）")
    p.add_argument("--config", help="配置文件路径（默认 config.json）")
    p.add_argument("--provider", choices=["mock", "openai", "dashscope"],
                   help="LLM 服务商：mock / openai / dashscope(通义千问)")
    p.add_argument("--model", help="覆盖配置文件里的模型名")
    p.add_argument("--output", "-o", help="把审查报告写入指定文件")
    p.add_argument("--memory-file", help="会话记忆持久化文件路径")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="打印每一步推理与工具调用")
    p.add_argument("--web", action="store_true", help="启动简易 Web 界面（默认 127.0.0.1:8000）")
    p.add_argument("--port", type=int, default=8000, help="Web 界面端口")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    # Web 界面模式
    if args.web:
        from .webapp import run_web
        config = load_config(args.config or "config.json")
        provider_factory = lambda: create_provider(args, config)
        run_web(provider_factory, port=args.port)
        return 0

    config = load_config(args.config or "config.json")
    provider = create_provider(args, config)

    memory = Memory()
    if args.memory_file and os.path.exists(args.memory_file):
        memory.load(args.memory_file)

    agent = CodeReviewAgent(provider, memory, verbose=args.verbose)
    result = agent.run(args.target)

    print()
    print(result.answer)
    print()
    print("（推理步数：%d，调用工具：%s，Provider：%s）"
          % (result.steps, result.tool_calls or "无", provider.name))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.answer + "\n")
        print("[已保存报告] %s" % args.output)
    if args.memory_file:
        memory.save(args.memory_file)
        print("[已保存记忆] %s" % args.memory_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())
