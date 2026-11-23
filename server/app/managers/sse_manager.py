"""SSE Emitter 管理器"""

import logging
import asyncio
from typing import Dict
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class SseEmitterManager:
    """SSE Emitter 管理器"""
    
    def __init__(self):
        # 存储所有的队列
        self._queues: Dict[str, asyncio.Queue] = {}
    
    def create_emitter(self, task_id: str) -> StreamingResponse:
        """
        创建 SSE Emitter
        
        Args:
            task_id: 任务ID
            
        Returns:
            StreamingResponse
        """
        # 创建队列
        queue = asyncio.Queue()
        self._queues[task_id] = queue
        
        logger.info(f"SSE 连接已创建, taskId={task_id}")
        
        # 创建事件流生成器
        async def event_generator():
            try:
                while True:
                    try:
                        # 15 秒无消息时发一次心跳注释行，避免代理/浏览器
                        # 把长时间空闲的 SSE 连接判为死连接而断开
                        message = await asyncio.wait_for(queue.get(), timeout=15)
                    except asyncio.TimeoutError:
                        yield ": ping\n\n"
                        continue

                    # 如果是完成信号，结束流
                    if message == "__COMPLETE__":
                        break

                    # 格式化为 SSE 格式
                    yield f"data: {message}\n\n"
            except asyncio.CancelledError:
                logger.info(f"SSE 连接被取消, taskId={task_id}")
            except Exception as e:
                logger.error(f"SSE 连接错误, taskId={task_id}, error={e}")
            finally:
                # 只清理自己创建的那个队列：
                # 前端断线重连会新建队列覆盖旧的，这里若无条件删除
                # 会把重连后的新队列也删掉，导致后续消息全部丢失
                if self._queues.get(task_id) is queue:
                    del self._queues[task_id]
                logger.info(f"SSE 连接已关闭, taskId={task_id}")
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    def send(self, task_id: str, message: str):
        """
        发送消息
        
        Args:
            task_id: 任务ID
            message: 消息内容
        """
        queue = self._queues.get(task_id)
        if queue is None:
            logger.warning(f"SSE Emitter 不存在, taskId={task_id}")
            return
        
        try:
            queue.put_nowait(message)
            logger.debug(f"SSE 消息发送成功, taskId={task_id}")
        except Exception as e:
            logger.error(f"SSE 消息发送失败, taskId={task_id}, error={e}")
    
    def complete(self, task_id: str):
        """
        完成连接
        
        Args:
            task_id: 任务ID
        """
        queue = self._queues.get(task_id)
        if queue is None:
            logger.warning(f"SSE Emitter 不存在, taskId={task_id}")
            return
        
        try:
            queue.put_nowait("__COMPLETE__")
            logger.info(f"SSE 连接已完成, taskId={task_id}")
        except Exception as e:
            logger.error(f"SSE 连接完成失败, taskId={task_id}, error={e}")
    
    def exists(self, task_id: str) -> bool:
        """
        检查 Emitter 是否存在
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否存在
        """
        return task_id in self._queues


# 全局单例
sse_emitter_manager = SseEmitterManager()
