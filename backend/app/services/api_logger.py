"""
API Call Logger — 异步记录每次 DashScope API 调用到数据库

设计原则：
- 火后即忘(fire-and-forget)：日志记录失败不应影响主流程
- 自带 session：不依赖外部 db session，避免事务冲突
- 自动计算耗时：提供 context manager 风格的计时器
"""
import time
import logging
import asyncio
from typing import Optional
from uuid import UUID

from app.db.session import async_session
from app.models.models import ApiCallLog

logger = logging.getLogger(__name__)


class ApiCallTimer:
    """计时器上下文，记录调用开始/结束时间"""

    def __init__(self):
        self.start_time: float = 0
        self.end_time: float = 0

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    @property
    def duration_ms(self) -> int:
        if self.end_time and self.start_time:
            return int((self.end_time - self.start_time) * 1000)
        return 0


async def log_api_call(
    model: str,
    endpoint: str,
    status: str,
    duration_ms: int = 0,
    tokens_input: int = 0,
    tokens_output: int = 0,
    error: Optional[str] = None,
    request_payload: Optional[dict] = None,
    response_summary: Optional[dict] = None,
    user_id: Optional[str] = None,
    generation_id: Optional[str] = None,
):
    """
    异步记录一次 API 调用到数据库

    fire-and-forget: 任何异常只打日志不抛出
    """
    try:
        async with async_session() as db:
            log_entry = ApiCallLog(
                model=model,
                endpoint=endpoint,
                status=status,
                duration_ms=duration_ms,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                error=error,
                request_payload=request_payload,
                response_summary=response_summary,
                user_id=UUID(user_id) if user_id else None,
                generation_id=UUID(generation_id) if generation_id else None,
            )
            db.add(log_entry)
            await db.commit()
    except Exception as e:
        logger.warning(f"[ApiLogger] Failed to log API call: {e}")


def fire_and_forget(coro):
    """将协程作为后台任务执行，不等待结果"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop — skip logging
        pass
