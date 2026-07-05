#!/usr/bin/env python3
"""启动 wger MCP 服务器（SSE 模式，独立进程）。

用法:
    python run_mcp_server.py --port 8100

作为独立进程运行后，后端通过 MCP 协议连接。
"""
import sys
import argparse
from wger_mcp_server import mcp


def main():
    parser = argparse.ArgumentParser(description="启动 wger MCP 服务器")
    parser.add_argument("--port", type=int, default=8100, help="监听端口")
    args = parser.parse_args()

    # port 是 FastMCP settings 属性，需要在运行前设置
    mcp.settings.port = args.port
    print(f"wger MCP 服务器启动于 http://localhost:{args.port} (SSE)")
    sys.stdout.flush()

    # FastMCP SSE 模式——独立 HTTP 服务
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
