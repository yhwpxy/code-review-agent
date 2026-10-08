# -*- coding: utf-8 -*-
"""单元测试：覆盖工具与 Agent 核心循环。

运行方式（在项目根目录）：
    python -m unittest discover -s tests -v
或：
    python tests/test_agent.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.core import CodeReviewAgent
from agent.llm import MockProvider
from agent.memory import Memory
from agent.tools import run_tool, tool_analyze, tool_read_file, tool_check_syntax

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "examples", "bad_code.py")


class TestTools(unittest.TestCase):
    def test_read_file(self):
        out = run_tool("read_file", {"path": SAMPLE})
        self.assertIn("bad_code.py", out)
        self.assertIn("password", out)

    def test_check_syntax(self):
        out = run_tool("check_syntax", {"path": SAMPLE})
        self.assertIn("通过", out)

    def test_analyze_finds_issues(self):
        out = run_tool("analyze", {"path": SAMPLE})
        self.assertIn("eval", out)              # eval 安全风险
        self.assertIn("可变默认参数", out)        # 可变默认参数
        self.assertIn("硬编码", out)             # 硬编码密钥
        self.assertIn("裸 except", out)          # 裸 except
        self.assertIn("is None", out)            # == None 建议

    def test_unknown_tool_raises(self):
        with self.assertRaises(ValueError):
            run_tool("not_exist", {})


class TestMemory(unittest.TestCase):
    def test_add_and_trim(self):
        m = Memory(max_turns=3)
        for i in range(10):
            m.add("user", "msg %d" % i)
        self.assertLessEqual(len(m.history), 6)

    def test_save_load(self):
        m = Memory()
        m.add_user("hello")
        m.remember("k", "v")
        path = os.path.join(tempfile_getdir(), "mem_test.json")
        m.save(path)
        m2 = Memory()
        m2.load(path)
        self.assertEqual(m2.recall("k"), "v")
        os.remove(path)


class TestAgentLoop(unittest.TestCase):
    def test_mock_agent_runs_end_to_end(self):
        agent = CodeReviewAgent(MockProvider(), Memory(), max_iterations=5)
        result = agent.run(SAMPLE)
        self.assertTrue(result.answer)
        self.assertIn("read_file", result.tool_calls)
        self.assertIn("analyze", result.tool_calls)
        self.assertLessEqual(result.steps, 5)


def tempfile_getdir():
    import tempfile
    return tempfile.gettempdir()


if __name__ == "__main__":
    unittest.main()
