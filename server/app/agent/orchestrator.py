"""文章多智能体编排器"""

import logging
import re
from typing import TYPE_CHECKING

from app.agent.agents.content_generator import ContentGeneratorAgent
from app.agent.agents.content_merger import ContentMergerAgent
from app.agent.agents.image_analyzer import ImageAnalyzerAgent
from app.agent.agents.outline_generator import OutlineGeneratorAgent
from app.agent.agents.title_generator import TitleGeneratorAgent
from app.agent.context.stream_handler import StreamHandlerContext
from app.models.enums import SseMessageTypeEnum
from app.schemas.article import ArticleState

if TYPE_CHECKING:
    from app.services.article_agent_service import ArticleAgentService

logger = logging.getLogger(__name__)

_PLACEHOLDER_PATTERN = re.compile(r"\{\{[A-Z_]+_\d+\}\}")


def _strip_placeholders(text: str) -> str:
    """清掉配图降级后残留的占位符，避免正文里露出 {{IMAGE_PLACEHOLDER_x}}"""
    return _PLACEHOLDER_PATTERN.sub("", text).strip()


class ArticleAgentOrchestrator:
    """多智能体编排器"""

    def __init__(self):
        self.title_agent = TitleGeneratorAgent()
        self.outline_agent = OutlineGeneratorAgent()
        self.content_agent = ContentGeneratorAgent()
        self.image_analyzer_agent = ImageAnalyzerAgent()
        self.content_merger_agent = ContentMergerAgent()

    async def execute_phase1(
        self,
        service: "ArticleAgentService",
        state: ArticleState,
        stream_handler,
    ):
        stream_context = StreamHandlerContext(stream_handler)
        logger.info("阶段1：开始生成标题方案, taskId=%s", state.task_id)
        await self.title_agent.run(service, state)
        stream_context.emit(SseMessageTypeEnum.AGENT1_COMPLETE.value)
        logger.info(
            "阶段1：标题方案生成成功, taskId=%s, optionsCount=%s",
            state.task_id,
            len(state.title_options or []),
        )

    async def execute_phase2(
        self,
        service: "ArticleAgentService",
        state: ArticleState,
        stream_handler,
    ):
        stream_context = StreamHandlerContext(stream_handler)
        logger.info("阶段2：开始生成大纲, taskId=%s", state.task_id)
        await self.outline_agent.run(service, state, stream_context.emit)
        stream_context.emit(SseMessageTypeEnum.AGENT2_COMPLETE.value)
        logger.info("阶段2：大纲生成成功, taskId=%s", state.task_id)

    async def execute_phase3(
        self,
        service: "ArticleAgentService",
        state: ArticleState,
        stream_handler,
    ):
        stream_context = StreamHandlerContext(stream_handler)
        logger.info("阶段3：开始生成正文, taskId=%s", state.task_id)
        await self.content_agent.run(service, state, stream_context.emit)
        stream_context.emit(SseMessageTypeEnum.AGENT3_COMPLETE.value)

        # 用户选择「纯文字」时直接跳过整个配图阶段
        if not getattr(state, "enable_images", True):
            logger.info("阶段3：用户选择不配图，跳过分图阶段, taskId=%s", state.task_id)
            self.content_merger_agent.run(service, state)
            stream_context.emit(SseMessageTypeEnum.MERGE_COMPLETE.value)
            return

        logger.info("阶段3：开始分析配图需求, taskId=%s", state.task_id)
        try:
            await self.image_analyzer_agent.run(service, state)
            stream_context.emit(SseMessageTypeEnum.AGENT4_COMPLETE.value)
        except Exception as e:
            # 配图属于增强能力，分析失败不应连累整篇文章
            logger.warning(
                "阶段3：配图需求分析失败，降级为无配图继续, taskId=%s, error=%s",
                state.task_id, e,
            )
            state.image_requirements = []
            state.content = _strip_placeholders(state.content or "")

        logger.info("阶段3：开始生成配图, taskId=%s", state.task_id)
        try:
            await service.agent5_generate_images(state, stream_context.emit)
            stream_context.emit(SseMessageTypeEnum.AGENT5_COMPLETE.value)
        except Exception as e:
            logger.warning(
                "阶段3：配图生成失败，使用已成功的配图继续, taskId=%s, error=%s",
                state.task_id, e,
            )
            state.images = state.images or []
            if not state.images:
                state.content = _strip_placeholders(state.content or "")

        logger.info("阶段3：开始图文合成, taskId=%s", state.task_id)
        self.content_merger_agent.run(service, state)
        stream_context.emit(SseMessageTypeEnum.MERGE_COMPLETE.value)

