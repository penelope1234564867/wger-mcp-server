"""个人数据相关 MCP 工具 —— 需 wger API Token。

涉及体重记录、营养计划、用户档案等登录后才能访问的资源。
Token 通过环境变量 WGER_API_TOKEN 配置；未配置时工具会返回提示信息。
"""
from datetime import date
from typing import Annotated

from fastmcp import FastMCP

from .client import api_get, api_post
from .config import WGER_API_TOKEN


def _no_token() -> dict:
    return {
        "error": "unauthorized",
        "detail": "未配置 wger API Token。请在 wger.de 登录后到 "
                  "https://wger.de/en/user/api-key 生成 key，"
                  "并设置环境变量 WGER_API_TOKEN。",
    }


def register(mcp: FastMCP) -> None:

    @mcp.tool
    async def list_weight_entries(
        limit: Annotated[int, "最多返回条数，默认 20"] = 20,
    ) -> dict:
        """列出当前用户的体重记录（日期+体重，按时间倒序）。"""
        if not WGER_API_TOKEN:
            return _no_token()
        data = await api_get("/weightentry/", {"limit": max(1, min(int(limit), 200))})
        if isinstance(data, dict) and "error" in data:
            return data
        return {
            "count": data.get("count"),
            "results": [
                {"id": e.get("id"), "date": e.get("date"),
                 "weight": e.get("weight"), "unit": e.get("unit")}
                for e in (data.get("results") or [])
            ],
        }

    @mcp.tool
    async def add_weight_entry(
        weight: Annotated[float, "体重数值（单位 kg，如 75.5）"],
        entry_date: Annotated[str, "日期 YYYY-MM-DD，默认今天"] = "",
    ) -> dict:
        """记录一条体重数据。需 Token。"""
        if not WGER_API_TOKEN:
            return _no_token()
        day = entry_date.strip() or date.today().isoformat()
        body = {"weight": float(weight), "date": day}
        return await api_post("/weightentry/", body)

    @mcp.tool
    async def get_user_profile() -> dict:
        """获取当前用户的档案（昵称、单位偏好、生日等）。"""
        if not WGER_API_TOKEN:
            return _no_token()
        data = await api_get("/userprofile/")
        if isinstance(data, dict) and "error" in data:
            # 可能是列表式端点，取第一条
            if "results" in data and data["results"]:
                return data["results"][0]
            return data
        # userprofile 有时返回列表
        if isinstance(data, list) and data:
            return data[0]
        return data

    @mcp.tool
    async def list_nutrition_plans(
        limit: Annotated[int, "最多返回条数，默认 20"] = 20,
    ) -> dict:
        """列出当前用户的营养计划。"""
        if not WGER_API_TOKEN:
            return _no_token()
        data = await api_get("/nutritionplan/", {"limit": max(1, min(int(limit), 100))})
        if isinstance(data, dict) and "error" in data:
            return data
        return {
            "count": data.get("count"),
            "results": [
                {"id": p.get("id"), "description": p.get("description"),
                 "creation_date": p.get("creation_date")}
                for p in (data.get("results") or [])
            ],
        }

    @mcp.tool
    async def get_nutrition_plan_values(
        plan_id: Annotated[int, "营养计划 ID"],
    ) -> dict:
        """获取某营养计划的营养汇总（总热量/蛋白质/碳水/脂肪/纤维等）。"""
        if not WGER_API_TOKEN:
            return _no_token()
        return await api_get(f"/nutritionplan/{plan_id}/nutritional_values/")

    @mcp.tool
    async def list_workout_sessions(
        limit: Annotated[int, "最多返回条数，默认 20"] = 20,
    ) -> dict:
        """列出当前用户的训练记录/会话。"""
        if not WGER_API_TOKEN:
            return _no_token()
        data = await api_get("/workoutsession/", {"limit": max(1, min(int(limit), 100))})
        if isinstance(data, dict) and "error" in data:
            return data
        return {
            "count": data.get("count"),
            "results": [
                {"id": s.get("id"), "date": s.get("date"),
                 "notes": s.get("notes"), "impression": s.get("impression")}
                for s in (data.get("results") or [])
            ],
        }
