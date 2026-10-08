# -*- coding: utf-8 -*-
"""项目启动入口：python run.py <目标>

把项目根目录加入 sys.path，保证 `from agent import ...` 能正常工作，
然后委托给 agent.main.main 处理命令行参数。
"""

import os
import sys

# 强制 stdout/stderr 使用 UTF-8，避免中文在 Windows 控制台（GBK 代码页）下乱码。
# Python 3.7+ 支持 reconfigure；失败时静默忽略。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.main import main

if __name__ == "__main__":
    sys.exit(main())
