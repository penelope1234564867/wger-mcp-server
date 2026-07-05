"""营养/食材相关 MCP 工具 —— 公开只读，无需 Token。

wger 食材库含 300 万+ 条记录，数据来自 Open Food Facts。
注意 v2 不支持服务端模糊搜索，?name= 为精确/包含匹配，故本模块在 API 过滤
基础上再做一次客户端子串过滤，提升准确度。
"""
from typing import Annotated

from fastmcp import FastMCP

from .client import api_get, cached_get


def register(mcp: FastMCP) -> None:

    @mcp.tool
    async def search_ingredients(
        term: Annotated[str, "食材名称关键词（英文，如 banana、chicken breast）"],
        limit: Annotated[int, "最多返回条数，默认 20，上限 50"] = 20,
    ) -> dict:
        """搜索食材并返回每 100g 的营养成分（热量/蛋白质/碳水/脂肪等）。

        数据来源 Open Food Facts（经 wger 索引）。由于库很大（300 万+），匹配以名称为主。
        """
        limit = max(1, min(int(limit), 50))
        term_l = term.strip().lower()
        if not term_l:
            return {"error": "term 不能为空"}

        data = await api_get("/ingredient/", {"name": term_l, "limit": limit * 3})
        if isinstance(data, dict) and "error" in data:
            return data

        results = []
        for ing in (data.get("results") or []):
            name = (ing.get("name") or "").strip()
            # 客户端二次过滤，确保返回的真的包含关键词
            if term_l not in name.lower() and term_l not in (ing.get("common_name") or "").lower():
                continue
            results.append(_summarize_ingredient(ing))
            if len(results) >= limit:
                break

        return {
            "query": term,
            "total_matches": len(results),
            "results": results,
        }

    @mcp.tool
    async def get_ingredient_details(
        ingredient_id: Annotated[int, "食材 ID（可从 search_ingredients 获取）"],
    ) -> dict:
        """获取食材详细营养成分（每 100g）与来源信息。"""
        data = await api_get(f"/ingredient/{ingredient_id}/")
        if isinstance(data, dict) and "error" in data:
            return data
        return _summarize_ingredient(data, full=True)

    @mcp.tool
    async def list_weight_units() -> dict:
        """列出可用重量单位（如 克、杯、片 等，含克数换算）。"""
        data = await cached_get("weightunits", "/weightunit/", {"limit": 100})
        if isinstance(data, dict) and "error" in data:
            return data
        return {
            "count": data.get("count"),
            "results": [
                {
                    "id": u.get("id"),
                    "name": u.get("name"),
                    "gram": u.get("amount"),  # 该单位对应的克数
                }
                for u in (data.get("results") or [])
            ],
        }


def _summarize_ingredient(ing: dict, full: bool = False) -> dict:
    """把食材对象整理成简洁结构。营养值均为每 100g。"""
    summary = {
        "id": ing.get("id"),
        "name": ing.get("name"),
        "common_name": ing.get("common_name"),
        "brand": ing.get("brand"),
        "barcode": ing.get("code"),
        "energy_kcal_per_100g": ing.get("energy"),
        "protein_g": _num(ing.get("protein")),
        "carbohydrates_g": _num(ing.get("carbohydrates")),
        "carbohydrates_sugar_g": _num(ing.get("carbohydrates_sugar")),
        "fat_g": _num(ing.get("fat")),
        "fat_saturated_g": _num(ing.get("fat_saturated")),
        "fiber_g": _num(ing.get("fiber")),
        "sodium_g": _num(ing.get("sodium")),
    }
    if full:
        summary.update({
            "uuid": ing.get("uuid"),
            "source_name": ing.get("source_name"),
            "source_url": ing.get("source_url"),
            "remote_id": ing.get("remote_id"),
            "created": ing.get("created"),
            "last_update": ing.get("last_update"),
        })
    return summary


def _num(v):
    """尽量转成 float，失败原样返回。"""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return v
