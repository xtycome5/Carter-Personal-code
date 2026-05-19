"""
Gallery Routes - 公共 Gallery API（无需登录）

提供首页和 Explore 页面展示审核通过的精选作品。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.db.session import get_db
from app.models.models import Dream, Generation, User

router = APIRouter(prefix="/api/gallery", tags=["gallery"])


@router.get("")
async def get_gallery(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    gen_type: str = Query(None, description="Filter by type: image or video"),
    db: AsyncSession = Depends(get_db),
):
    """
    公共 Gallery — 返回已审核上架的作品列表
    按 featured_at 倒序排列（最新上架的排前面）
    无需登录即可访问
    """
    query = (
        select(Generation)
        .where(
            Generation.featured == True,
            Generation.status == "completed",
            Generation.result_url.isnot(None),
        )
        .order_by(desc(Generation.featured_at))
    )

    if gen_type:
        query = query.where(Generation.type == gen_type)

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    generations = result.scalars().all()

    items = []
    for g in generations:
        # Get dream info
        dream_result = await db.execute(
            select(Dream.title, Dream.content).where(Dream.id == g.dream_id)
        )
        dream_row = dream_result.one_or_none()
        dream_title = (dream_row.title or dream_row.content[:40]) if dream_row else ""

        # Get user display name
        user_result = await db.execute(
            select(User.nickname, User.email, User.avatar_url).where(User.id == g.user_id)
        )
        user_row = user_result.one_or_none()
        user_name = (user_row.nickname or user_row.email.split("@")[0]) if user_row else "Anonymous"
        avatar_url = user_row.avatar_url if user_row else None

        items.append({
            "id": str(g.id),
            "type": g.type,
            "result_url": g.result_url,
            "dream_title": dream_title,
            "user": user_name,
            "avatar_url": avatar_url,
            "featured_at": g.featured_at.isoformat() if g.featured_at else None,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}
