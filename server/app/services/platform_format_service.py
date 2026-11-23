"""平台排版服务：把已生成的文章转换成「微信公众号」「小红书」可直接使用的格式。

设计要点：
1. 公众号编辑器会剥离 <style>/class/id，只能用**内联 style**，所以这里逐标签注入。
2. 小红书是短文案形态，需要 LLM 二次改写（标题钩子、短句、emoji、话题标签）。
3. 不涉及任何平台 API 调用——输出的是可复制粘贴的成品。
"""

import json
import logging
import re
from typing import Any, Dict, List

import markdown as md_lib
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# 微信公众号内联样式表（正文 16px / 行高 1.75 是公众号阅读舒适区）
_WECHAT_STYLE: Dict[str, str] = {
    "p": "font-size:16px;line-height:1.75;color:#3f3f3f;margin:0 0 20px;letter-spacing:0.4px;",
    "h1": "font-size:22px;font-weight:bold;color:#1f2d3d;margin:34px 0 18px;text-align:center;line-height:1.4;",
    "h2": "font-size:19px;font-weight:bold;color:#1f2d3d;margin:32px 0 16px;padding-left:12px;"
          "border-left:4px solid #22C55E;line-height:1.5;",
    "h3": "font-size:17px;font-weight:bold;color:#1f2d3d;margin:26px 0 12px;line-height:1.5;",
    "h4": "font-size:16px;font-weight:bold;color:#1f2d3d;margin:20px 0 10px;line-height:1.5;",
    "blockquote": "margin:0 0 20px;padding:14px 18px;border-left:4px solid #22C55E;background:#f7faf8;"
                  "color:#5a6b62;font-size:15px;line-height:1.75;border-radius:0 6px 6px 0;",
    "ul": "margin:0 0 20px;padding-left:22px;",
    "ol": "margin:0 0 20px;padding-left:22px;",
    "li": "font-size:16px;line-height:1.75;color:#3f3f3f;margin:0 0 8px;",
    "img": "display:block;margin:24px auto;max-width:100%;height:auto;border-radius:8px;",
    "pre": "margin:0 0 20px;padding:14px 16px;background:#f6f8fa;border-radius:6px;overflow-x:auto;"
           "font-size:13px;line-height:1.6;",
    "code": "font-family:Consolas,Monaco,Menlo,monospace;font-size:13px;color:#24292e;background:#f6f8fa;"
            "padding:2px 5px;border-radius:3px;",
    "hr": "border:none;border-top:1px solid #e8e8e8;margin:34px 0;",
    "a": "color:#22C55E;text-decoration:none;",
    "strong": "font-weight:bold;color:#1f2d3d;",
    "em": "font-style:normal;color:#22C55E;font-weight:bold;",
}


class PlatformFormatService:
    """文章 → 平台成品格式"""

    def __init__(self):
        self._client = None

    # ------------------------------------------------------------------ #
    # 微信公众号
    # ------------------------------------------------------------------ #
    def markdown_to_wechat_html(self, markdown_text: str) -> str:
        """Markdown → 公众号可直接粘贴的 HTML（内联样式）"""
        html = md_lib.markdown(markdown_text or "", extensions=["extra", "sane_lists", "nl2br"])
        soup = BeautifulSoup(html, "html.parser")

        for tag, style in _WECHAT_STYLE.items():
            for el in soup.find_all(tag):
                # pre 内部的 code 用等宽样式，不要叠加行内 code 的底色
                if tag == "code" and el.parent and el.parent.name == "pre":
                    el["style"] = "font-family:Consolas,Monaco,Menlo,monospace;font-size:13px;color:#24292e;"
                    continue
                el["style"] = style

        section = soup.new_tag("section")
        section["style"] = (
            "font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue','PingFang SC',sans-serif;"
            "font-size:16px;color:#3f3f3f;letter-spacing:0.4px;"
        )
        for child in list(soup.children):
            section.append(child.extract())
        return str(section)

    @staticmethod
    def build_digest(content: str, limit: int = 100) -> str:
        """生成公众号摘要（去掉 Markdown 标记取前 N 字）"""
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", content or "")  # 去图片
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)      # 链接保文字
        text = re.sub(r"[#>*`_~\-]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:limit]

    # ------------------------------------------------------------------ #
    # 小红书
    # ------------------------------------------------------------------ #
    _XHS_PROMPT = """你是小红书笔记操盘手。把下面这篇文章改写成一篇小红书笔记，严格遵守：

1. 标题：20 字以内，带强钩子（数字 / 反差 / 疑问 / 利益点），不要书名号、不要「本文」。
2. 正文：150~400 字，短句为主，每段 1~3 行，段与段之间空一行。
3. emoji：每段 0~2 个，克制使用，不要每句都加。
4. 结构：开头一句戳痛点或抛结论 → 中间 3~5 条干货（用 1️⃣2️⃣3️⃣ 或 ✅ 分点）→ 结尾一句行动号召。
5. 人称：用「我/你/姐妹/朋友」，禁止「文章」「本文」「笔者」这类书面语。
6. 结尾另起一行给 4~6 个话题标签，格式 #标签 ，标签要贴合内容。
7. 不得编造原文没有的数据和事实。

只输出 JSON，不要任何解释：
{{"title": "标题", "body": "正文（不含标签）", "tags": ["#标签1", "#标签2"]}}

原文标题：{title}

原文内容：
{content}
"""

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.dashscope_api_key,
                base_url=settings.dashscope_base_url,
            )
        return self._client

    async def to_xiaohongshu(self, title: str, content: str) -> Dict[str, Any]:
        """调 LLM 把长文改写成小红书笔记"""
        prompt = self._XHS_PROMPT.format(title=title or "", content=(content or "")[:6000])
        resp = await self._get_client().chat.completions.create(
            model=settings.dashscope_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        raw = (resp.choices[0].message.content or "").strip()
        data = self._parse_json(raw)

        tags: List[str] = data.get("tags") or []
        # 兜底：模型没给标签就按标题生成几个
        if not tags:
            keywords = [w for w in re.split(r"[\s,，、:：]+", title or "") if len(w) >= 2][:4]
            tags = [f"#{k}" for k in keywords] or ["#AI", "#效率工具"]

        return {
            "title": (data.get("title") or title or "")[:40],
            "body": data.get("body") or "",
            "tags": [t if str(t).startswith("#") else f"#{t}" for t in tags],
        }

    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        """从模型输出里抠出 JSON（兼容 ```json 包裹 / 前后有废话）"""
        if not raw:
            return {}
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except Exception:
            pass
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                logger.warning("小红书文案 JSON 解析失败，原始输出前 200 字: %s", raw[:200])
        return {}


platform_format_service = PlatformFormatService()
