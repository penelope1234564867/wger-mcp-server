---
title: Wger MCP Server
emoji: 💪
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: mit
tags:
  - mcp
  - fitness
  - wger
  - mcp-server
---

# wger MCP Server 💪

把 [wger](https://wger.de)（开源健身/营养管理平台）的能力封装成 **MCP (Model Context Protocol) 服务器**，以 SSE 方式对外提供服务。任何支持 MCP 的 AI agent（Claude Desktop、Cursor、Cline、自研 agent 等）都能连接，查询动作库、肌肉/器械、食材营养，以及管理体重记录、营养计划等。

## ✨ 提供的工具（共 15 个）

### 公开只读（无需 Token）

| 工具 | 说明 |
|------|------|
| `search_exercises` | 按名称搜索健身动作（支持多语言、别名匹配） |
| `get_exercise_details` | 获取动作详情：描述、目标肌群、器械、图片、别名 |
| `list_exercise_categories` | 列出动作分类（Abs/Arms/Back/Legs…） |
| `list_muscles` | 列出肌肉群（含中英文名、前后侧、示意图） |
| `list_equipment` | 列出器械类型（Barbell/Dumbbell/Kettlebell…） |
| `get_exercise_images` | 获取动作示意图 |
| `search_ingredients` | 搜索食材，返回每 100g 营养成分（300 万+ 条，来自 Open Food Facts） |
| `get_ingredient_details` | 获取食材详细营养信息 |
| `list_weight_units` | 列出可用重量单位（含克数换算） |

### 登录类（需 `WGER_API_TOKEN`）

| 工具 | 说明 |
|------|------|
| `list_weight_entries` | 列出体重记录 |
| `add_weight_entry` | 记录一条体重数据 |
| `get_user_profile` | 获取用户档案 |
| `list_nutrition_plans` | 列出营养计划 |
| `get_nutrition_plan_values` | 获取营养计划汇总 |
| `list_workout_sessions` | 列出训练记录 |

## 🚀 在 Hugging Face Spaces 上部署

本仓库已配置 Docker SDK，直接推到 HF Space 即可：

1. 在 [huggingface.co/new-space](https://huggingface.co/new-space) 新建 Space，**SDK 选 Docker**。
2. 把本仓库文件推到该 Space 的 Git 仓库。
3. Space 会自动构建并启动，监听 `7860` 端口。
4. （可选）如需登录类工具：Space 的 **Settings → Variables and secrets** 里添加 `WGER_API_TOKEN`。

部署后，MCP 端点为：
```
https://<你的用户名>-<space名>.hf.space/sse
```

## 🔌 Agent 连接配置

### Claude Desktop / Cursor / Cline（SSE）

```json
{
  "mcpServers": {
    "wger": {
      "url": "https://<你的用户名>-<space名>.hf.space/sse"
    }
  }
}
```

### 自研 agent（fastmcp 客户端）

```python
from fastmcp import Client

async with Client("https://<user>-<space>.hf.space/sse") as client:
    tools = await client.list_tools()
    result = await client.call_tool("search_exercises",
                                    {"term": "bench", "language": "English", "limit": 5})
```

## 🏠 本地运行

```bash
pip install -r requirements.txt
python run_mcp_server.py --port 8100
# 默认监听 0.0.0.0:8100，SSE 端点 http://localhost:8100/sse
```

配置（环境变量，均可选）：

| 变量 | 默认 | 说明 |
|------|------|------|
| `WGER_API_URL` | `https://wger.de` | wger 实例地址，自托管可改 |
| `WGER_API_VERSION` | `v2` | API 版本 |
| `WGER_API_TOKEN` | （空） | 登录类工具需要 |
| `WGER_TIMEOUT` | `30` | 请求超时秒数 |
| `WGER_CACHE_TTL` | `3600` | 动作库列表缓存秒数 |

## ⚠️ 关于 wger.de 的反爬（重要）

wger.de 官方实例在前端部署了 **Anubis** 反爬代理：

- `/api/v1/*` 会被挑战拦截，程序化访问会拿到 PoW 挑战页而非数据
- `/api/v2/*` 被显式放行（供移动端与 API 客户端使用）

因此本服务器**默认使用 v2 API**。若你自托管 wger 且未启用 Anubis，可将 `WGER_API_VERSION` 改为 `v1`。

## 📦 项目结构

```
wger-mcp-server/
├── run_mcp_server.py          # 启动器（SSE 模式）
├── wger_mcp_server/
│   ├── __init__.py            # FastMCP 实例 + 工具注册
│   ├── config.py              # 配置（URL/Token/语言映射）
│   ├── client.py              # 异步 HTTP 客户端 + 缓存
│   ├── tools_exercises.py     # 动作相关工具
│   ├── tools_nutrition.py     # 营养/食材工具
│   └── tools_tracking.py      # 登录类工具（需 Token）
├── requirements.txt
├── Dockerfile                 # HF Spaces 部署
└── .env.example
```

## 🔑 获取 wger API Token

1. 注册并登录 [wger.de](https://wger.de)
2. 访问 `https://wger.de/en/user/api-key`
3. 生成 key，填入 `WGER_API_TOKEN`

## 📄 许可

MIT。wger 动作数据遵循 CC-BY-SA 4.0（来自 wger 社区）。
