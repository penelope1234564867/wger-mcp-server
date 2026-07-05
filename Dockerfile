# Hugging Face Spaces - Docker SDK
# wger MCP 服务器（SSE 模式），监听 HF 要求的 7860 端口
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 时区（日志可读）
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 先装依赖（利用 Docker 层缓存，代码变动不重装）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝源码
COPY wger_mcp_server/ ./wger_mcp_server/
COPY run_mcp_server.py .

# Hugging Face Spaces 要求应用监听 7860
EXPOSE 7860

# SSE 模式启动。host=0.0.0.0 确保容器内可被 HF 反代访问。
# 如需登录类工具，在 HF Space 的 Settings → Variables and secrets 里
# 配置 WGER_API_TOKEN（以及可选的 WGER_API_URL 等）。
CMD ["python", "run_mcp_server.py", "--port", "7860", "--host", "0.0.0.0"]
