"""wger MCP 服务器包。

对外暴露 `mcp`（FastMCP 实例），由 run_mcp_server.py 启动。
工具按域拆分到 tools_*.py，通过 register(mcp) 注册。

导入路径：from wger_mcp_server import mcp
"""
from fastmcp import FastMCP

# 创建 FastMCP 实例（SSE 模式由启动器决定）
mcp = FastMCP("wger-mcp-server")

# 注册各域工具。必须在 mcp 创建之后导入，工具模块通过 register(mcp) 挂载。
from . import tools_exercises, tools_nutrition, tools_tracking  # noqa: E402

tools_exercises.register(mcp)
tools_nutrition.register(mcp)
tools_tracking.register(mcp)

__all__ = ["mcp"]
__version__ = "1.0.0"
