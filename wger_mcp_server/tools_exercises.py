"""动作（Exercise）相关 MCP 工具 —— 公开只读，无需 Token。

wger v2 的动作数据模型：
- exercise：结构信息（分类/肌肉/器械 ID），不含名字
- exerciseinfo/<id>/：富端点，含 translations（名字+描述，按语言）、肌肉、器械、图片
- 动作名字在 translations 表里，v2 不支持服务端按名搜索，
  因此 search_exercises 采用「拉全量(818 条) + 客户端过滤 + 缓存」策略
"""
from typing import Annotated, Optional

from fastmcp import FastMCP

from .client import api_get, cached_get
from .config import resolve_language


def register(mcp: FastMCP) -> None:
    """把本模块的工具注册到 FastMCP 实例上。"""

    @mcp.tool
    async def search_exercises(
        term: Annotated[str, "搜索关键词（动作名或别名，不区分大小写）"],
        language: Annotated[str, "语言，如 English/German/Chinese 或语言 ID，默认 English"] = "English",
        limit: Annotated[int, "最多返回条数，默认 20，上限 100"] = 20,
    ) -> dict:
        """按名称搜索健身动作。返回匹配的动作列表（id、名称、分类、目标肌肉、器械）。

        数据来源 wger.de 开源动作库（CC-BY-SA 4）。结果在指定语言下按关键词匹配动作名与别名。
        """
        lang_id = resolve_language(language)
        limit = max(1, min(int(limit), 100))
        term_l = term.strip().lower()
        if not term_l:
            return {"error": "term 不能为空"}

        # 一次性拉全量 exerciseinfo（约 818 条，含所有语言的 translations），缓存 1 小时
        payload = await cached_get(
            "exerciseinfo:all",
            "/exerciseinfo/",
            {"limit": 1000},
        )
        if isinstance(payload, dict) and "error" in payload:
            return payload

        results = payload.get("results", []) if isinstance(payload, dict) else []
        matches = []
        for ex in results:
            translations = ex.get("translations") or []
            # 选出目标语言的翻译；找不到则保留全部用于匹配
            in_lang = [t for t in translations if t.get("language") == lang_id]
            pool = in_lang if in_lang else translations
            name = ""
            matched_alias = ""
            for t in pool:
                tname = (t.get("name") or "").strip()
                aliases = [a.get("alias", "") if isinstance(a, dict) else str(a)
                           for a in (t.get("aliases") or [])]
                if tname and term_l in tname.lower():
                    name = tname
                    matched_alias = ""
                    break
                for a in aliases:
                    if a and term_l in a.lower():
                        name = tname
                        matched_alias = a
                        break
                if name:
                    break
            if not name:
                continue
            matches.append({
                "id": ex.get("id"),
                "name": name,
                "matched_alias": matched_alias or None,
                "category": (ex.get("category") or {}).get("name"),
                "category_id": (ex.get("category") or {}).get("id"),
                "muscles": [m.get("name") for m in (ex.get("muscles") or []) if isinstance(m, dict)],
                "equipment": [e.get("name") for e in (ex.get("equipment") or []) if isinstance(e, dict)],
                "language": lang_id,
                "variations": ex.get("variations") if isinstance(ex.get("variations"), (int, float)) else 0,
            })
            if len(matches) >= limit:
                break

        return {
            "query": term,
            "language": lang_id,
            "total_matches": len(matches),
            "results": matches,
        }

    @mcp.tool
    async def get_exercise_details(
        exercise_id: Annotated[int, "动作 ID（可从 search_exercises 获取）"],
    ) -> dict:
        """获取动作详情：描述、目标肌群、次级肌群、器械、图片、别名、备注、许可信息。"""
        data = await api_get(f"/exerciseinfo/{exercise_id}/")
        if isinstance(data, dict) and "error" in data:
            return data

        translations = data.get("translations") or []
        # 提取每种语言的名称与描述
        trans_summary = [
            {
                "language": t.get("language"),
                "name": t.get("name"),
                "description": t.get("description"),
                "aliases": [a.get("alias") if isinstance(a, dict) else a
                            for a in (t.get("aliases") or [])],
                "notes": [n.get("comment") if isinstance(n, dict) else n
                          for n in (t.get("notes") or [])],
            }
            for t in translations
        ]
        return {
            "id": data.get("id"),
            "uuid": data.get("uuid"),
            "category": (data.get("category") or {}).get("name"),
            "muscles": [{"id": m.get("id"), "name": m.get("name"),
                         "name_en": m.get("name_en"), "is_front": m.get("is_front")}
                        for m in (data.get("muscles") or []) if isinstance(m, dict)],
            "muscles_secondary": [{"id": m.get("id"), "name": m.get("name")}
                                   for m in (data.get("muscles_secondary") or []) if isinstance(m, dict)],
            "equipment": [{"id": e.get("id"), "name": e.get("name")}
                          for e in (data.get("equipment") or []) if isinstance(e, dict)],
            "translations": trans_summary,
            "images": [img.get("image") for img in (data.get("images") or []) if isinstance(img, dict)],
            "videos": [v.get("video") for v in (data.get("videos") or []) if isinstance(v, dict)],
            "variations": data.get("variations") if isinstance(data.get("variations"), (int, float)) else 0,
            "license": (data.get("license") or {}).get("short_name") if isinstance(data.get("license"), dict) else None,
            "license_author": data.get("license_author"),
        }

    @mcp.tool
    async def list_exercise_categories() -> dict:
        """列出所有动作分类（如 Abs、Arms、Back、Legs 等）。"""
        data = await cached_get("categories", "/exercisecategory/", {"limit": 100})
        if isinstance(data, dict) and "error" in data:
            return data
        return {
            "count": data.get("count"),
            "results": [{"id": c.get("id"), "name": c.get("name")}
                        for c in (data.get("results") or [])],
        }

    @mcp.tool
    async def list_muscles() -> dict:
        """列出所有肌肉群（含中英文名、前后侧、示意图 URL）。"""
        data = await cached_get("muscles", "/muscle/", {"limit": 100})
        if isinstance(data, dict) and "error" in data:
            return data
        return {
            "count": data.get("count"),
            "results": [
                {
                    "id": m.get("id"),
                    "name": m.get("name"),
                    "name_en": m.get("name_en"),
                    "is_front": m.get("is_front"),
                    "image_url": m.get("image_url_main"),
                }
                for m in (data.get("results") or [])
            ],
        }

    @mcp.tool
    async def list_equipment() -> dict:
        """列出所有器械类型（如 Barbell、Dumbbell、Kettlebell 等）。"""
        data = await cached_get("equipment", "/equipment/", {"limit": 100})
        if isinstance(data, dict) and "error" in data:
            return data
        return {
            "count": data.get("count"),
            "results": [{"id": e.get("id"), "name": e.get("name")}
                        for e in (data.get("results") or [])],
        }

    @mcp.tool
    async def get_exercise_images(
        exercise_id: Annotated[int, "动作 ID"],
    ) -> dict:
        """获取某动作的示意图（含缩略图 URL）。"""
        data = await api_get("/exerciseimage/", {"exercise": exercise_id, "limit": 50})
        if isinstance(data, dict) and "error" in data:
            return data
        results = []
        for img in (data.get("results") or []):
            thumbs = img.get("thumbnails") or {}
            results.append({
                "id": img.get("id"),
                "image": img.get("image"),
                "is_main": img.get("is_main"),
                "thumbnail_small": thumbs.get("small"),
                "thumbnail_medium": thumbs.get("medium"),
            })
        return {"exercise_id": exercise_id, "count": len(results), "results": results}
