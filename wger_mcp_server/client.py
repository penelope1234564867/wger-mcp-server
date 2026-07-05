"""wger API 异步 HTTP 客户端。

- 复用单个 httpx.AsyncClient
- 统一错误处理：HTTP 错误/网络错误都返回 {"error": ...} 而非抛异常，
  这样 MCP 工具能向 agent 返回可读的错误信息
- 提供轻量内存缓存（用于 exerciseinfo 全量列表）
"""
import time
from typing import Any, Optional

import httpx

from .config import api_base, default_headers, REQUEST_TIMEOUT, CACHE_TTL

_client: Optional[httpx.AsyncClient] = None
_cache: dict[str, tuple[float, Any]] = {}


async def get_client() -> httpx.AsyncClient:
    """获取共享的 AsyncClient（惰性创建，关闭后自动重建）。"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            headers=default_headers(),
        )
    return _client


def _safe_body(resp: httpx.Response) -> Any:
    """尽量解析 JSON，失败则返回截断的文本。"""
    try:
        return resp.json()
    except Exception:
        return resp.text[:500]


async def api_get(path: str, params: Optional[dict] = None) -> Any:
    """GET 请求，返回 JSON 或 {"error": ...}。path 相对于 api_base，如 '/exerciseinfo/9/'。"""
    url = f"{api_base()}{path}"
    client = await get_client()
    try:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP {e.response.status_code}",
            "detail": _safe_body(e.response),
            "url": str(e.request.url),
        }
    except httpx.RequestError as e:
        return {"error": "request_error", "detail": str(e), "url": url}


async def api_post(path: str, json_body: Optional[dict] = None) -> Any:
    """POST 请求，返回 JSON 或 {"error": ...}。"""
    url = f"{api_base()}{path}"
    client = await get_client()
    try:
        resp = await client.post(url, json=json_body)
        resp.raise_for_status()
        if resp.content:
            return resp.json()
        return {"ok": True, "status": resp.status_code}
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP {e.response.status_code}",
            "detail": _safe_body(e.response),
            "url": str(e.request.url),
        }
    except httpx.RequestError as e:
        return {"error": "request_error", "detail": str(e), "url": url}


async def cached_get(key: str, path: str, params: Optional[dict] = None) -> Any:
    """带 TTL 缓存的 GET。仅缓存成功响应（不含 error 键）。"""
    now = time.time()
    entry = _cache.get(key)
    if entry and now - entry[0] < CACHE_TTL:
        return entry[1]
    data = await api_get(path, params)
    if isinstance(data, dict) and "error" not in data:
        _cache[key] = (now, data)
    return data


def clear_cache() -> None:
    """清空缓存。"""
    _cache.clear()
