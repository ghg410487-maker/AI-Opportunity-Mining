# -*- coding: utf-8 -*-
"""
AI 教育工作台 · 本地文件服务
- 提供项目文件树浏览、文件读取、文件保存接口
- 静态托管 workbench/index.html 前端页面
- 仅监听 127.0.0.1，只允许访问项目根目录内的文件
零依赖：只使用 Python 标准库。

启动：python workbench/server.py   然后浏览器打开 http://127.0.0.1:8765
"""
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # E:/AIjiaoyu
STATIC_DIR = os.path.join(ROOT, "workbench")
PORT = 8765

IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules",
               ".idea", ".vscode", "__MACOSX"}
IGNORE_EXT = {".pyc", ".pyo", ".pyd", ".so", ".exe", ".dll"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 单文件读取上限 2MB
MAX_ENTRIES_PER_DIR = 200
MAX_DEPTH = 8


def safe_path(rel: str):
    """把相对路径解析为项目根目录内的绝对路径，越界返回 None"""
    if not rel:
        return None
    rel = rel.lstrip("/\\").replace("\\", "/")
    p = os.path.abspath(os.path.join(ROOT, rel))
    if p != ROOT and not p.startswith(ROOT + os.sep):
        return None
    return p


def build_tree(path: str, rel: str, depth: int):
    """递归构建目录树，超限截断"""
    if depth > MAX_DEPTH:
        return {"name": os.path.basename(path) or rel, "type": "dir", "truncated": True, "children": []}
    try:
        entries = os.listdir(path)
    except OSError:
        return {"name": os.path.basename(path), "type": "dir", "children": []}
    dirs, files = [], []
    for name in sorted(entries):
        if name in IGNORE_DIRS or os.path.splitext(name)[1].lower() in IGNORE_EXT:
            continue
        full = os.path.join(path, name)
        if os.path.isdir(full):
            dirs.append({"name": name, "type": "dir",
                         "children": build_tree(full, f"{rel}/{name}", depth + 1)["children"]})
        else:
            try:
                size = os.path.getsize(full)
            except OSError:
                size = 0
            files.append({"name": name, "type": "file", "size": size})
        if len(dirs) + len(files) >= MAX_ENTRIES_PER_DIR:
            files.append({"name": "…（已截断）", "type": "file", "size": 0})
            break
    return {"name": os.path.basename(path) or rel, "type": "dir",
            "children": dirs + files}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass  # 安静模式

    # ---------- 基础 ----------
    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def send_error_json(self, code, msg):
        self.send_json({"ok": False, "error": msg}, code)

    def do_OPTIONS(self):
        self._send(204, b"", "text/plain")

    # ---------- 路由 ----------
    def do_GET(self):
        parsed = urlparse(self.path)
        route = unquote(parsed.path)

        if route == "/api/tree":
            tree = build_tree(ROOT, "", 0)
            self.send_json({"ok": True, "root": ROOT, "tree": tree})

        elif route == "/api/file":
            qs = parse_qs(parsed.query)
            rel = (qs.get("path") or [""])[0]
            p = safe_path(rel)
            if not p or not os.path.isfile(p):
                return self.send_error_json(404, f"文件不存在: {rel}")
            size = os.path.getsize(p)
            if size > MAX_FILE_SIZE:
                return self.send_error_json(413, f"文件过大（{size} 字节），超过 2MB 上限，请用 VS Code 打开")
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except OSError as e:
                return self.send_error_json(500, f"读取失败: {e}")
            self.send_json({"ok": True, "path": rel.replace("\\", "/"),
                            "content": content, "size": size})

        elif route == "/api/health":
            self.send_json({"ok": True, "root": ROOT})

        elif route in ("/", "/index.html"):
            self.serve_static("index.html")

        elif not route.startswith("/api/"):
            self.serve_static(route.lstrip("/"))

        else:
            self.send_error_json(404, f"未知接口: {route}")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/save":
            return self.send_error_json(404, "未知接口")
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as e:
            return self.send_error_json(400, f"请求体解析失败: {e}")
        rel, content = data.get("path", ""), data.get("content", "")
        p = safe_path(rel)
        if not p or not os.path.isfile(p):
            return self.send_error_json(404, f"只能保存已存在的文件: {rel}")
        try:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(content)
        except OSError as e:
            return self.send_error_json(500, f"保存失败: {e}")
        self.send_json({"ok": True, "path": rel.replace("\\", "/")})

    # ---------- 静态文件 ----------
    def serve_static(self, rel):
        p = os.path.abspath(os.path.join(STATIC_DIR, rel))
        if not p.startswith(STATIC_DIR + os.sep) and p != STATIC_DIR:
            return self.send_error_json(404, "页面不存在")
        if not os.path.isfile(p):
            return self.send_error_json(404, "页面不存在")
        ext = os.path.splitext(p)[1].lower()
        ctype = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8", ".png": "image/png",
                 ".svg": "image/svg+xml", ".ico": "image/x-icon"}.get(ext, "text/plain; charset=utf-8")
        with open(p, "rb") as f:
            self._send(200, f.read(), ctype)


def main():
    print(f"项目根目录: {ROOT}")
    print(f"工作台地址: http://127.0.0.1:{PORT}")
    print("按 Ctrl+C 停止服务")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")


if __name__ == "__main__":
    main()
