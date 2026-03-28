#!/usr/bin/env python3
"""
启动 MCP Server

将外部工具封装为 MCP 服务，供 Agent 远程调用

使用示例:
    python scripts/start_mcp_server.py
    python scripts/start_mcp_server.py --port 8080
"""

import argparse
import json
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp.external_tools_full import external_tool_manager


class MCPRequestHandler(BaseHTTPRequestHandler):
    """MCP HTTP 请求处理器"""
    
    def log_message(self, format, *args):
        """自定义日志"""
        print(f"[MCP] {self.address_string()} - {format % args}")
    
    def _send_json(self, data: dict, status: int = 200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/":
            # 服务信息
            info = {
                "name": "CTF Crypto MCP Server",
                "version": "1.0.0",
                "endpoints": [
                    "/tools - 列出可用工具",
                    "/call - 调用工具 (POST)"
                ]
            }
            self._send_json(info)
        
        elif path == "/tools":
            # 列出工具
            tools = external_tool_manager.list_tools()
            self._send_json(tools)
        
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        """处理 POST 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()
        
        try:
            params = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        
        if path == "/call":
            # 调用工具
            tool_name = params.get("tool")
            tool_params = params.get("params", {})
            
            if not tool_name:
                self._send_json({"error": "Missing 'tool' parameter"}, 400)
                return
            
            print(f"[MCP] 调用工具: {tool_name}({tool_params})")
            
            result = external_tool_manager.call(tool_name, **tool_params)
            self._send_json(result)
        
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_OPTIONS(self):
        """处理 OPTIONS 请求 (CORS)"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def start_server(port: int = 8080):
    """启动 MCP Server"""
    server = HTTPServer(("localhost", port), MCPRequestHandler)
    
    print("=" * 60)
    print("🔧 CTF Crypto MCP Server")
    print("=" * 60)
    print(f"服务地址: http://localhost:{port}")
    print()
    print("可用端点:")
    print(f"  GET  http://localhost:{port}/tools     - 列出工具")
    print(f"  POST http://localhost:{port}/call      - 调用工具")
    print()
    print("示例调用:")
    print(f'''  curl -X POST http://localhost:{port}/call \\
    -H "Content-Type: application/json" \\
    -d '{{"tool": "yafu", "params": {{"n": 3233}}}}' ''')
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n停止服务...")
        server.shutdown()


def main():
    parser = argparse.ArgumentParser(description="启动 MCP Server")
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="服务端口 (默认 8080)"
    )
    
    args = parser.parse_args()
    
    start_server(args.port)


if __name__ == "__main__":
    main()
