"""wger MCP 服务器配置。

所有配置通过环境变量传入，方便容器化部署（Hugging Face Spaces 等）。
默认使用 wger.de 官方实例的 **v2 API**，因为 wger.de 在 v1 前面部署了
Anubis 反爬代理（会拦截 /api/v1/* 的程序化访问），而 /api/v2/* 被显式放行
（供移动端与 API 客户端使用）。
"""
import os

# wger 实例地址。默认官方实例；自托管时改成自己的地址即可。
WGER_API_URL = os.environ.get("WGER_API_URL", "https://wger.de").rstrip("/")

# API 版本。默认 v2（v1 被 Anubis 拦截）。自托管且未启用 Anubis 时可改 v1。
WGER_API_VERSION = os.environ.get("WGER_API_VERSION", "v2")

# wger API Token（可选）。登录类工具（体重记录/营养计划/用户档案）需要。
# 在 https://wger.de/<lang>/user/api-key 登录后生成。仅设置后才可调用登录类工具。
WGER_API_TOKEN = os.environ.get("WGER_API_TOKEN", "").strip()

# 客户端 User-Agent。wger 建议程序化访问带上可识别的 UA。
USER_AGENT = os.environ.get(
    "WGER_USER_AGENT",
    "wger-mcp-server/1.0 (MCP server for wger fitness API)",
)

# 请求超时（秒）
REQUEST_TIMEOUT = float(os.environ.get("WGER_TIMEOUT", "30"))

# 列表缓存 TTL（秒）。exerciseinfo 全量拉取后缓存，避免反复请求 818 条。
CACHE_TTL = int(os.environ.get("WGER_CACHE_TTL", "3600"))


def api_base() -> str:
    """返回 API 根路径，例如 https://wger.de/api/v2"""
    return f"{WGER_API_URL}/api/{WGER_API_VERSION}"


def default_headers() -> dict:
    """构造请求头。带 Token 时附加 Authorization。"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if WGER_API_TOKEN:
        # wger 使用 Django REST Framework Token 认证
        headers["Authorization"] = f"Token {WGER_API_TOKEN}"
    return headers


# wger 语言 ID 映射。动作翻译按语言区分。
LANGUAGE_MAP = {
    "english": 2, "en": 2,
    "german": 1, "de": 1,
    "bulgarian": 3, "bg": 3,
    "greek": 4, "el": 4,
    "spanish": 5, "es": 5,
    "french": 6, "fr": 6,
    "italian": 7, "it": 7,
    "dutch": 8, "nl": 8,
    "portuguese": 9, "pt": 9,
    "russian": 10, "ru": 10,
    "czech": 11, "cs": 11,
    "turkish": 12, "tr": 12,
    "chinese": 13, "zh": 13, "zh-cn": 13, "zh-tw": 14,
}


def resolve_language(language) -> int:
    """把语言名称/缩写解析成 wger 语言 ID。无法识别时回退到 2（English）。"""
    if language is None:
        return 2
    if isinstance(language, int):
        return language
    s = str(language).strip().lower()
    if s.isdigit():
        return int(s)
    return LANGUAGE_MAP.get(s, 2)
