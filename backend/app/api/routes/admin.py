"""
Admin Routes - 后台管理 API

提供 Dashboard 统计、用户管理、内容审核、画家池管理等接口。
当前用硬编码 admin 账号验证（后续可改为 role-based）。
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from app.db.session import get_db
from app.models.models import User, Dream, Generation
from app.core.security import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ===== Simple Admin Auth (hardcoded for now) =====
ADMIN_EMAILS = ["carter@dreamrecorder.xyz", "admin@dreamrecorder.xyz"]


async def require_admin(user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """验证当前用户是管理员"""
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


# ===== Dashboard Stats =====
@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Dashboard 统计数据"""
    # 用户总数
    user_count = await db.scalar(select(func.count()).select_from(User))
    # 梦境总数
    dream_count = await db.scalar(select(func.count()).select_from(Dream))
    # 图片生成数
    image_count = await db.scalar(
        select(func.count()).select_from(Generation).where(Generation.type == "image")
    )
    # 视频生成数
    video_count = await db.scalar(
        select(func.count()).select_from(Generation).where(Generation.type == "video")
    )
    # 成功数
    completed_count = await db.scalar(
        select(func.count()).select_from(Generation).where(Generation.status == "completed")
    )
    # 失败数
    failed_count = await db.scalar(
        select(func.count()).select_from(Generation).where(Generation.status == "failed")
    )
    total_gens = (image_count or 0) + (video_count or 0)
    success_rate = round((completed_count or 0) / total_gens * 100, 1) if total_gens > 0 else 0

    return {
        "total_users": user_count or 0,
        "total_dreams": dream_count or 0,
        "total_images": image_count or 0,
        "total_videos": video_count or 0,
        "completed": completed_count or 0,
        "failed": failed_count or 0,
        "success_rate": success_rate,
    }


# ===== Users =====
@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表 + 统计"""
    query = select(User)
    if search:
        query = query.where(
            User.email.ilike(f"%{search}%") | User.nickname.ilike(f"%{search}%")
        )
    query = query.order_by(User.created_at.desc())

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    # Get generation counts per user
    user_data = []
    for u in users:
        gen_stats = await db.execute(
            select(
                func.count().label("total"),
                func.sum(case((Generation.type == "image", 1), else_=0)).label("images"),
                func.sum(case((Generation.type == "video", 1), else_=0)).label("videos"),
            ).where(Generation.user_id == u.id)
        )
        stats = gen_stats.one()
        dream_count = await db.scalar(
            select(func.count()).select_from(Dream).where(Dream.user_id == u.id)
        )
        user_data.append({
            "id": str(u.id),
            "email": u.email,
            "nickname": u.nickname or u.email.split("@")[0],
            "avatar_url": u.avatar_url,
            "oauth_provider": u.oauth_provider,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "dreams_count": dream_count or 0,
            "images_count": int(stats.images or 0),
            "videos_count": int(stats.videos or 0),
        })

    return {"users": user_data, "total": total or 0, "page": page, "page_size": page_size}


# ===== Generations (Content Review) =====
@router.get("/generations")
async def list_generations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    gen_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取所有生成记录（用于内容审核）"""
    query = select(Generation)
    if status:
        query = query.where(Generation.status == status)
    if gen_type:
        query = query.where(Generation.type == gen_type)
    query = query.order_by(Generation.created_at.desc())

    # Total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    generations = result.scalars().all()

    items = []
    for g in generations:
        # Get dream title
        dream_result = await db.execute(select(Dream.title, Dream.content).where(Dream.id == g.dream_id))
        dream_row = dream_result.one_or_none()
        dream_title = (dream_row.title or dream_row.content[:20]) if dream_row else "Unknown"

        # Get user email
        user_result = await db.execute(select(User.email, User.nickname).where(User.id == g.user_id))
        user_row = user_result.one_or_none()
        user_name = (user_row.nickname or user_row.email.split("@")[0]) if user_row else "Unknown"

        items.append({
            "id": str(g.id),
            "type": g.type,
            "status": g.status,
            "dream_title": dream_title,
            "user": user_name,
            "prompt": g.prompt[:100] if g.prompt else "",
            "result_url": g.result_url,
            "task_id": g.task_id,
            "metadata": g.metadata_json,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })

    return {"generations": items, "total": total or 0, "page": page, "page_size": page_size}


# ===== Recent Generations (for Dashboard) =====
@router.get("/recent-generations")
async def recent_generations(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """最近的生成记录"""
    result = await db.execute(
        select(Generation).order_by(Generation.created_at.desc()).limit(limit)
    )
    generations = result.scalars().all()

    items = []
    for g in generations:
        user_result = await db.execute(select(User.nickname, User.email).where(User.id == g.user_id))
        user_row = user_result.one_or_none()
        user_name = (user_row.nickname or user_row.email.split("@")[0]) if user_row else "Unknown"

        items.append({
            "id": str(g.id),
            "type": g.type,
            "status": g.status,
            "user": user_name,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })

    return {"generations": items}


# ===== Artist Pool =====
@router.get("/artists")
async def list_artists():
    """获取当前画家池配置"""
    from app.services.prompt_expansion import ARTIST_POOL
    return {"artists": ARTIST_POOL, "total": len(ARTIST_POOL)}
