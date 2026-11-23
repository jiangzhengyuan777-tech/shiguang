"""并行配图生成执行器"""

import asyncio
import logging
from typing import List, Tuple

from app.schemas.article import ImageRequirement
from app.schemas.image import ImageRequest

logger = logging.getLogger(__name__)


class ParallelImageGenerator:
    """并行配图生成器"""

    def __init__(self, image_service_strategy, max_concurrency: int, fail_fast: bool):
        self.image_service_strategy = image_service_strategy
        self.max_concurrency = max(1, max_concurrency)
        self.fail_fast = fail_fast

    async def generate(
        self,
        requirements: List[ImageRequirement],
        on_image_ready=None,
    ) -> List[Tuple[ImageRequirement, object]]:
        """并行生成图片，按输入顺序返回结果

        on_image_ready: 可选回调 (requirement, result)，每张图生成完成就立刻触发，
                        用于向上层推送逐张进度，而不是等全部完成。
        """
        if not requirements:
            return []

        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def _generate_single(requirement: ImageRequirement):
            async with semaphore:
                image_request = ImageRequest(
                    keywords=requirement.keywords,
                    prompt=requirement.prompt,
                    position=requirement.position,
                    type=requirement.type,
                )
                result = await self.image_service_strategy.get_image_and_upload(
                    requirement.image_source,
                    image_request,
                )
                # 生成一张就回调一次，实现逐张进度
                if on_image_ready is not None:
                    try:
                        on_image_ready(requirement, result)
                    except Exception as cb_error:  # 回调异常不影响主流程
                        logger.warning("单张配图回调失败: %s", cb_error)
                return requirement, result

        results = await asyncio.gather(
            *[_generate_single(requirement) for requirement in requirements],
            return_exceptions=True,
        )

        generated_pairs: List[Tuple[ImageRequirement, object]] = []
        first_error = None
        for item in results:
            if isinstance(item, Exception):
                if first_error is None:
                    first_error = item
                continue
            generated_pairs.append(item)

        if first_error and (self.fail_fast or not generated_pairs):
            raise first_error
        return generated_pairs

