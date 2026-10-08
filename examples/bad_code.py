# -*- coding: utf-8 -*-
"""示例：一个"问题多多"的小脚本，用于演示代码审查 Agent 的发现能力。

本文件刻意包含多处常见问题（未使用导入、硬编码密钥、可变默认参数、
裸 except、吞异常、eval、== None、过深嵌套等）。

请运行：
    python run.py examples/bad_code.py
看看 Agent 能否把它们全部找出来。
"""

import os
import math
import sys

password = "admin123"                 # 硬编码口令
API_KEY = "sk-1234567890abcdef"       # 硬编码密钥


def connect(user, pwd, host="localhost", opts=[]):
    # 可变默认参数：多次调用会共享同一个 opts 列表，造成隐蔽 bug
    print("连接 %s@%s" % (user, host))
    opts.append(pwd)
    return True


def load_config(path):
    try:
        with open(path) as f:
            return f.read()
    except:
        pass                           # 裸 except + 静默吞异常


def run_snippet(code):
    return eval(code)                  # eval 安全风险


def matrix(data):
    out = []
    for i in range(len(data)):
        for j in range(len(data)):
            for k in range(len(data)):
                for m in range(len(data)):
                    out.append(data[i] + data[j] + data[k] + data[m])
    return out


def is_valid(x):
    if x == None:                      # 应为 is None
        return False
    return True


class Conn:
    def __init__(self, url):
        self.url = url

    def open(self):
        print("open", self.url)
        return self
