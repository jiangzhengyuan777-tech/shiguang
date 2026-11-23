"""热点链接抓取：把一篇网页/公众号文章的正文抽出来，作为创作素材。

设计要点：
1. 只抽正文，去掉导航、评论、广告、脚本等噪音；
2. 针对微信公众号文章做特判（正文在 #js_content 里，且大量使用 <section> 而非 <p>）；
3. 输出截断到 MAX_LENGTH，避免把超长页面整体塞进 Prompt 撑爆上下文。
"""

import logging
import re
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HotspotService:
    """网页正文抽取"""

    MAX_LENGTH = 6000        # 注入 Prompt 的正文上限
    MAX_HTML_BYTES = 5 * 1024 * 1024

    _UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    _NOISE_TAGS = [
        "script", "style", "noscript", "iframe", "nav", "header", "footer",
        "aside", "form", "svg", "button", "input", "select",
    ]
    _NOISE_PATTERN = re.compile(
        r"(comment|share|related|recommend|advert|sidebar|foot|nav|menu|toolbar|qrcode|breadcrumb)",
        re.I,
    )

    async def fetch(self, url: str) -> Dict[str, object]:
        """抓取网页并抽取标题 + 正文"""
        if not url or not re.match(r"^https?://", url.strip()):
            raise ValueError("链接格式不正确，需要以 http:// 或 https:// 开头")
        url = url.strip()

        html, final_url = await self._download(url)
        soup = BeautifulSoup(html, "lxml")

        title = self._extract_title(soup)
        content = self._extract_content(soup, final_url)

        if len(content) < 50:
            raise ValueError("没能从该页面提取到有效正文（可能是动态渲染或需要登录）")
        if self._looks_like_anti_bot(content):
            raise ValueError("该站点有反爬限制（需要人机验证），请手动复制正文后作为素材")

        truncated = content[: self.MAX_LENGTH]
        return {
            "url": final_url,
            "title": title or "未命名素材",
            "content": truncated,
            "wordCount": len(truncated),
            "truncated": len(content) > self.MAX_LENGTH,
            "source": self._detect_source(final_url),
        }

    # ------------------------------------------------------------------ #
    async def _download(self, url: str) -> tuple[str, str]:
        headers = {
            "User-Agent": self._UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        async with httpx.AsyncClient(
            timeout=25, follow_redirects=True, headers=headers, verify=False
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            raw = resp.content
            if len(raw) > self.MAX_HTML_BYTES:
                raw = raw[: self.MAX_HTML_BYTES]
            # 中文站点常见 GBK/GB2312，httpx 的编码推断偶发失灵，这里兜底
            encoding = resp.encoding or "utf-8"
            if encoding.lower() in ("iso-8859-1", "ascii"):
                encoding = self._guess_encoding(raw)
            html = raw.decode(encoding, errors="ignore")
            return html, str(resp.url)

    @staticmethod
    def _guess_encoding(raw: bytes) -> str:
        head = raw[:2048].decode("ascii", errors="ignore").lower()
        match = re.search(r'charset=["\']?([\w-]+)', head)
        if match:
            enc = match.group(1).lower()
            return "gb18030" if enc in ("gb2312", "gbk") else enc
        return "utf-8"

    # ------------------------------------------------------------------ #
    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        for selector in [
            "meta[property='og:title']",
            "meta[name='og:title']",
            "#activity-name",      # 微信公众号
            "h1",
            "title",
        ]:
            node = soup.select_one(selector)
            if not node:
                continue
            text = node.get("content") if node.name == "meta" else node.get_text(strip=True)
            if text and len(str(text).strip()) > 2:
                return re.sub(r"\s+", " ", str(text).strip())[:120]
        return ""

    def _extract_content(self, soup: BeautifulSoup, url: str) -> str:
        # 微信公众号特判
        if "mp.weixin.qq.com" in url:
            box = soup.select_one("#js_content") or soup.select_one(".rich_media_content")
            if box:
                return self._clean(self._collect_text(box))

        # 通用：先删噪音
        for tag in soup(self._NOISE_TAGS):
            tag.decompose()
        # 按 class/id 关键字删噪音容器，但要保护正文所在的外层容器：
        # 站点常把正文包在 class 含 "menu"/"nav"/"foot" 的外层 div 里，盲删会清空全文
        for tag in soup.find_all(attrs={"class": self._NOISE_PATTERN}):
            if tag.name in ("body", "html", "main", "article"):
                continue
            if len(tag.get_text(strip=True)) > 600:
                continue
            tag.decompose()
        for tag in soup.find_all(attrs={"id": self._NOISE_PATTERN}):
            if tag.name in ("body", "html", "main", "article"):
                continue
            if len(tag.get_text(strip=True)) > 600:
                continue
            tag.decompose()

        # 优先语义化容器
        for selector in ["article", "main", "[role='main']", "#content", ".content",
                         "#article", ".article", "#js_content"]:
            node = soup.select_one(selector)
            if node:
                text = self._collect_text(node)
                if len(text) > 120:
                    return self._clean(text)

        # 兜底：找出包含最多 <p> 文本的容器
        best_node, best_len = None, 0
        for node in soup.find_all(["div", "section", "td"]):
            paragraphs = node.find_all("p", recursive=False)
            if not paragraphs:
                continue
            length = sum(len(p.get_text(strip=True)) for p in paragraphs)
            if length > best_len:
                best_node, best_len = node, length
        if best_node is not None:
            return self._clean(self._collect_text(best_node))

        # 最后兜底：全文段落
        return self._clean(self._collect_text(soup.body or soup))

    @staticmethod
    def _collect_text(node) -> str:
        """按段落收集文本，保留段落换行"""
        blocks: List[str] = []
        for el in node.find_all(["p", "h1", "h2", "h3", "h4", "li", "blockquote", "section"]):
            text = el.get_text(" ", strip=True)
            # 过滤掉只含少量字的 section 包裹层（会与子节点重复）
            if text and len(text) >= 8:
                blocks.append(text)
        if not blocks:
            return node.get_text("\n", strip=True)
        # 去重相邻重复（section 嵌套会重复采集）
        deduped: List[str] = []
        for b in blocks:
            if not deduped or deduped[-1] != b:
                deduped.append(b)
        return "\n".join(deduped)

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"[ \t\u00a0]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _looks_like_anti_bot(content: str) -> bool:
        """识别被反爬拦截后返回的验证页"""
        markers = [
            "正在进行安全检测", "安全检测", "访问过于频繁", "请输入验证码", "滑动验证",
            "人机验证", "环境异常", "Just a moment", "Access denied", "Access Denied",
            "请开启JavaScript", "请开启 JavaScript",
        ]
        if len(content) < 300:
            return any(m in content for m in markers)
        # 正文很长时只看开头，避免误判正文里提到"验证码"之类的词
        return any(m in content[:200] for m in markers)

    @staticmethod
    def _detect_source(url: str) -> str:
        for domain, name in [
            ("mp.weixin.qq.com", "微信公众号"),
            ("zhihu.com", "知乎"),
            ("toutiao.com", "今日头条"),
            ("weibo.com", "微博"),
            ("36kr.com", "36氪"),
            ("thepaper.cn", "澎湃新闻"),
            ("xinhuanet.com", "新华网"),
            ("people.com.cn", "人民网"),
        ]:
            if domain in url:
                return name
        return "网页"


hotspot_service = HotspotService()
