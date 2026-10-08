# -*- coding: utf-8 -*-
"""简易 Web 界面：用标准库 http.server 实现，无需 Flask/Django。

启动后浏览器打开 http://127.0.0.1:8000，可：
    - 在文本框里直接粘贴代码，或填写本地文件路径；
    - 点击「开始审查」，后台跑一遍 CodeReviewAgent，返回报告。

每次请求都新建一个 Provider 与 Agent，保证 Mock 的步数状态互相独立。
"""

import json
import os
import socketserver
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer


class _SafeHTTPServer(HTTPServer):
    """解决 Windows 中文主机名下 socket.getfqdn 的编码崩溃问题。

    http.server.HTTPServer.server_bind 会调用 socket.getfqdn(host)，
    在中文主机名的 Windows 上 getfqdn 返回 GBK 字节、按 UTF-8 解码会抛
    UnicodeDecodeError。这里直接跳过该调用，用地址本身作为 server_name。
    """

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name = self.server_address[0] or "localhost"
        self.server_port = self.server_address[1]

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>代码审查 Agent</title>
<style>
  body { font-family: "Microsoft YaHei", sans-serif; background: #1e1f26; color: #eee;
         max-width: 860px; margin: 40px auto; padding: 0 20px; }
  h1 { font-size: 22px; }
  .muted { color: #9aa0b0; font-size: 13px; }
  textarea, input[type=text] { width: 100%; box-sizing: border-box; background: #2a2c36;
         color: #eee; border: 1px solid #3a3d4a; border-radius: 8px; padding: 10px;
         font-family: Consolas, monospace; font-size: 13px; }
  textarea { height: 180px; resize: vertical; }
  label { display: block; margin: 14px 0 6px; font-size: 14px; }
  button { background: #5f8cff; color: #fff; border: none; padding: 10px 22px;
           border-radius: 8px; font-size: 15px; cursor: pointer; margin-top: 14px; }
  button:hover { background: #4a74e0; }
  button:disabled { background: #555; cursor: wait; }
  pre { background: #2a2c36; border: 1px solid #3a3d4a; border-radius: 8px;
        padding: 16px; white-space: pre-wrap; word-break: break-word; font-size: 13px;
        line-height: 1.6; }
</style>
</head>
<body>
<h1>🔍 代码审查 Agent</h1>
<p class="muted">粘贴代码，或填写本地文件/目录路径，点击开始审查。</p>

<label>本地文件 / 目录路径（可留空）</label>
<input type="text" id="path" placeholder="例如 examples/bad_code.py">

<label>或直接粘贴代码</label>
<textarea id="code" placeholder="# 在这里粘贴要审查的代码"></textarea>

<button id="run" onclick="review()">开始审查</button>
<p id="status" class="muted"></p>
<pre id="out" style="display:none"></pre>

<script>
async function review() {
  const code = document.getElementById('code').value;
  const path = document.getElementById('path').value;
  const btn = document.getElementById('run');
  const out = document.getElementById('out');
  const status = document.getElementById('status');
  btn.disabled = true;
  status.textContent = '审查中…';
  out.style.display = 'none';
  try {
    const resp = await fetch('/review', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ code: code, path: path })
    });
    const data = await resp.json();
    out.textContent = data.report;
    out.style.display = 'block';
    status.textContent = '完成（推理步数 ' + data.steps + '，调用工具 ' +
      (data.tools || []).join(', ') + '）';
  } catch (e) {
    status.textContent = '出错：' + e;
  } finally {
    btn.disabled = false;
  }
}
</script>
</body>
</html>
"""


def _run_review(provider_factory, code, path):
    """执行一次审查，返回 (report, steps, tools)。"""
    from .core import CodeReviewAgent
    from .memory import Memory

    target = path.strip() if path and path.strip() else None

    # 若用户粘贴了代码且没填路径，写入临时文件再审查
    if code and code.strip():
        fd, tmp = tempfile.mkstemp(suffix=".py", prefix="review_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        target = tmp

    if not target:
        return "请填写文件路径，或粘贴代码。", 0, []

    agent = CodeReviewAgent(provider_factory(), Memory())
    result = agent.run(target)
    return result.answer, result.steps, result.tool_calls


def make_handler(provider_factory):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(HTML.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path != "/review":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8", "replace")
            try:
                data = json.loads(body or "{}")
            except ValueError:
                data = {}
            report, steps, tools = _run_review(
                provider_factory, data.get("code", ""), data.get("path", ""))
            resp = json.dumps(
                {"report": report, "steps": steps, "tools": tools},
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        def log_message(self, *args):
            pass  # 关闭默认访问日志，保持终端清爽

    return Handler


def run_web(provider_factory, port=8000):
    server = _SafeHTTPServer(("127.0.0.1", port), make_handler(provider_factory))
    print("Web 界面已启动：http://127.0.0.1:%d （Ctrl+C 退出）" % port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出。")
    finally:
        server.server_close()
