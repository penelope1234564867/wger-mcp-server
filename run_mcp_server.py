#!/usr/bin/env python3
"""启动 wger MCP 服务器（SSE 模式，独立进程）。

用法:
    python run_mcp_server.py --port 8100

作为独立进程运行后，后端通过 MCP 协议连接。
"""
import argparse
from wger_mcp_server import mcp


def main():
    parser = argparse.ArgumentParser(description="启动 wger MCP 服务器")
    parser.add_argument("--port", type=int, default=8100, help="监听端口")
    parser.add_argument("--host", default="0.0.0.0",
                        help="监听地址，默认 0.0.0.0（容器/HF Spaces 必须）")
    args = parser.parse_args()

    print(f"wger MCP 服务器启动于 http://{args.host}:{args.port} (SSE)", flush=True)

    # FastMCP 3.x：host/port 通过 transport_kwargs 传入。
    # host=0.0.0.0 确保容器（Hugging Face Spaces）内可被外部访问。
    mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
