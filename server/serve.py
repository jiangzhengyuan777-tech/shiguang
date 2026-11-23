"""拾光 · 后端启动入口

修复项：
1. 系统 no_proxy 含 "[::1]"，httpx 解析会抛 InvalidURL，这里重设；
2. 固定工作目录到 server/，保证 app 包可导入。
"""

import os
import sys

import uvicorn

for key in ("no_proxy", "NO_PROXY"):
    os.environ[key] = "localhost,127.0.0.1,::1"

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

uvicorn.run("app.main:app", host="127.0.0.1", port=8667)
