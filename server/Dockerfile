# ========================================
# 拾光 · 后端镜像（FastAPI）
# ========================================

FROM python:3.12-slim

# 国内 PyPI 镜像
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_TRUSTED_HOST=mirrors.aliyun.com \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    NO_PROXY=localhost,127.0.0.1,::1 \
    no_proxy=localhost,127.0.0.1,::1

WORKDIR /app

# 先装依赖，利用镜像层缓存
COPY pyproject.toml ./
RUN pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir \
        fastapi==0.115.0 \
        "uvicorn[standard]==0.32.0" \
        python-multipart==0.0.12 \
        sqlalchemy==2.0.36 \
        pymysql==1.1.1 \
        cryptography==43.0.3 \
        "databases[mysql]==0.9.0" \
        redis==5.2.0 \
        pydantic==2.10.2 \
        pydantic-settings==2.6.1 \
        python-dotenv==1.0.1 \
        "passlib[bcrypt]==1.7.4" \
        python-dateutil==2.9.0.post0 \
        openai==1.58.1 \
        httpx==0.28.1 \
        cos-python-sdk-v5==1.9.32 \
        google-genai==1.35.0 \
        beautifulsoup4==4.12.3 \
        lxml==5.3.0 \
        "stripe>=14.3.0" \
        markdown==3.7

# 再复制源码
COPY app ./app

# 运行时配置全部由 compose 的环境变量注入，镜像内不带 .env
EXPOSE 8667

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8667/api/health', timeout=3).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8667"]
