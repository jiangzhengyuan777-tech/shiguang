"""文章路由"""

import asyncio
from typing import List

from fastapi import APIRouter, Depends
from databases import Database

from app.database import get_db
from app.schemas.common import BaseResponse, DeleteRequest
from app.schemas.article import (
    ArticleAiModifyOutlineRequest,
    ArticleConfirmOutlineRequest,
    ArticleConfirmTitleRequest,
    ArticleCreateRequest,
    ArticleFormatRequest,
    ArticleQueryRequest,
    ArticleVO,
    HotspotFetchRequest,
    HotspotVO,
    TopicSuggestRequest,
    WechatFormatVO,
    XhsFormatVO,
)
from app.schemas.user import LoginUserVO
from app.services.article_service import ArticleService
from app.services.article_agent_service import ArticleAgentService
from app.services.article_async_service import article_async_service
from app.services.platform_format_service import platform_format_service
from app.services.hotspot_service import hotspot_service
from app.services.agent_log_service import AgentLogService
from app.schemas.statistics import AgentExecutionStatsVO
from app.deps import require_login
from app.managers.sse_manager import sse_emitter_manager
from app.exceptions import BusinessException, ErrorCode, throw_if

router = APIRouter(prefix="/article", tags=["文章管理"])


@router.post("/create", response_model=BaseResponse[str])
async def create_article(
    request: ArticleCreateRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """创建文章任务"""
    throw_if(
        not request.topic or not request.topic.strip(),
        ErrorCode.PARAMS_ERROR,
        "选题不能为空"
    )
    
    service = ArticleService(db)
    
    # 检查并消耗配额 + 创建文章任务（在同一事务中）
    task_id = await service.create_article_task_with_quota_check(
        request.topic,
        current_user,
        request.style,
        request.enabled_image_methods,
        request.reference_content,  # 热点素材（可选）
        request.enable_images if request.enable_images is not None else True,  # 是否配图
    )
    
    # 异步执行阶段1：生成标题方案
    asyncio.create_task(
        article_async_service.execute_phase1(
            task_id,
            request.topic,
            request.style,
        )
    )
    
    return BaseResponse.success(data=task_id, message="任务创建成功")


@router.get("/progress/{task_id}")
async def get_progress(
    task_id: str,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """SSE 进度推送"""
    throw_if(
        not task_id or not task_id.strip(),
        ErrorCode.PARAMS_ERROR,
        "任务ID不能为空"
    )
    
    # 校验权限（内部会检查任务是否存在以及用户是否有权限访问）
    service = ArticleService(db)
    await service.get_article_detail(task_id, current_user)
    
    # 创建 SSE Emitter
    return sse_emitter_manager.create_emitter(task_id)


@router.get("/{task_id}", response_model=BaseResponse[ArticleVO])
async def get_article(
    task_id: str,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """获取文章详情"""
    throw_if(
        not task_id or not task_id.strip(),
        ErrorCode.PARAMS_ERROR,
        "任务ID不能为空"
    )
    
    service = ArticleService(db)
    article_vo = await service.get_article_detail(task_id, current_user)
    
    return BaseResponse.success(data=article_vo)


@router.post("/list", response_model=BaseResponse[dict])
async def list_article(
    request: ArticleQueryRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """分页查询文章列表"""
    service = ArticleService(db)
    articles, total = await service.list_article_by_page(request, current_user)
    
    return BaseResponse.success(data={
        "records": articles,
        "total": total,
        "current": request.current,
        "size": request.page_size
    })


@router.post("/delete", response_model=BaseResponse[bool])
async def delete_article(
    request: DeleteRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """删除文章"""
    throw_if(not request.id, ErrorCode.PARAMS_ERROR, "文章ID不能为空")
    
    service = ArticleService(db)
    result = await service.delete_article(request.id, current_user)
    
    return BaseResponse.success(data=result, message="删除成功")


@router.post("/confirm-title", response_model=BaseResponse[None])
async def confirm_title(
    request: ArticleConfirmTitleRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """确认标题并输入补充描述"""
    service = ArticleService(db)
    await service.confirm_title(
        task_id=request.task_id,
        selected_main_title=request.selected_main_title,
        selected_sub_title=request.selected_sub_title,
        user_description=request.user_description,
        login_user=current_user,
    )
    asyncio.create_task(article_async_service.execute_phase2(request.task_id))
    return BaseResponse.success(data=None)


@router.post("/confirm-outline", response_model=BaseResponse[None])
async def confirm_outline(
    request: ArticleConfirmOutlineRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """确认大纲"""
    service = ArticleService(db)
    await service.confirm_outline(
        task_id=request.task_id,
        outline=request.outline,
        login_user=current_user,
    )
    asyncio.create_task(article_async_service.execute_phase3(request.task_id))
    return BaseResponse.success(data=None)


@router.post("/ai-modify-outline", response_model=BaseResponse[list])
async def ai_modify_outline(
    request: ArticleAiModifyOutlineRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """AI 修改大纲"""
    service = ArticleService(db)
    modified_outline = await service.ai_modify_outline(
        task_id=request.task_id,
        modify_suggestion=request.modify_suggestion,
        login_user=current_user,
    )
    return BaseResponse.success(data=[section.model_dump() for section in modified_outline])


@router.get("/execution-logs/{task_id}", response_model=BaseResponse[AgentExecutionStatsVO])
async def get_execution_logs(
    task_id: str,
    db: Database = Depends(get_db),
):
    """获取任务执行日志"""
    throw_if(not task_id or not task_id.strip(), ErrorCode.PARAMS_ERROR, "任务ID不能为空")
    service = AgentLogService(db)
    stats = await service.get_execution_stats(task_id)
    return BaseResponse.success(data=stats)


# ==================== 平台排版（公众号 / 小红书） ====================

@router.post("/format/wechat", response_model=BaseResponse[WechatFormatVO])
async def format_wechat(
    request: ArticleFormatRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login),
):
    """把已生成的文章转成公众号可粘贴的内联样式 HTML"""
    service = ArticleService(db)
    article = await service.get_article_detail(request.task_id, current_user)

    # 图文合成后的 fullContent 带图，优先用它；没有则退回纯正文
    content = article.full_content or article.content or ""
    throw_if(not content.strip(), ErrorCode.OPERATION_ERROR, "文章正文为空，无法排版")

    html = platform_format_service.markdown_to_wechat_html(content)
    return BaseResponse.success(
        data=WechatFormatVO(
            title=article.main_title or article.topic or "未命名文章",
            digest=platform_format_service.build_digest(article.content or content),
            html=html,
        )
    )


@router.post("/format/xiaohongshu", response_model=BaseResponse[XhsFormatVO])
async def format_xiaohongshu(
    request: ArticleFormatRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login),
):
    """把已生成的文章改写成小红书笔记（标题 + 正文 + 话题标签）"""
    service = ArticleService(db)
    article = await service.get_article_detail(request.task_id, current_user)

    content = article.content or ""
    throw_if(not content.strip(), ErrorCode.OPERATION_ERROR, "文章正文为空，无法改写")

    result = await platform_format_service.to_xiaohongshu(
        article.main_title or article.topic or "",
        content,
    )
    return BaseResponse.success(data=XhsFormatVO(**result))


# ==================== 热点链接抓取 ====================

@router.post("/fetch-url", response_model=BaseResponse[HotspotVO])
async def fetch_hotspot_url(
    request: HotspotFetchRequest,
    current_user: LoginUserVO = Depends(require_login),
):
    """抓取热点链接正文，作为文章创作素材"""
    try:
        data = await hotspot_service.fetch(request.url)
    except ValueError as e:
        raise BusinessException(ErrorCode.PARAMS_ERROR, str(e))
    except Exception as e:
        raise BusinessException(
            ErrorCode.OPERATION_ERROR,
            f"抓取失败：{type(e).__name__}（可能是该站点限制访问或需要登录）",
        )
    return BaseResponse.success(data=HotspotVO(**data))


# ==================== 选题建议 ====================

@router.post("/suggest-topics", response_model=BaseResponse[List[str]])
async def suggest_topics(
    request: TopicSuggestRequest,
    current_user: LoginUserVO = Depends(require_login),
):
    """按所选文风推荐候选选题（让 AI 来定写什么）"""
    try:
        service = ArticleAgentService()
        topics = await service.suggest_topics(request.style, request.count)
    except Exception as e:
        raise BusinessException(ErrorCode.OPERATION_ERROR, f"生成选题失败：{e}")
    return BaseResponse.success(data=topics)
