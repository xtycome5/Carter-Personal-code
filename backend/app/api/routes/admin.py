"""
Admin Routes - 后台管理 API

提供 Dashboard 统计、用户管理、内容审核、画家池管理、API调用监控等接口。
Admin 使用独立认证体系，与 C 端用户完全分离。
"""
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, desc, update
from jose import jwt, JWTError
from app.db.session import get_db
from app.models.models import User, Dream, Generation, ApiCallLog, Artist
from app.core.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])

admin_security = HTTPBearer(auto_error=False)

ADMIN_JWT_ALGORITHM = "HS256"
ADMIN_JWT_EXPIRE_HOURS = 72  # Admin token 有效期 3 天


# ===== Independent Admin Auth =====
@router.post("/login")
async def admin_login(data: dict):
    """Admin 独立登录 — 不依赖 C 端用户表"""
    username = data.get("username", "")
    password = data.get("password", "")

    if username != settings.ADMIN_USERNAME or password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    # 签发带 role=admin 的 JWT
    expire = datetime.now(timezone.utc) + timedelta(hours=ADMIN_JWT_EXPIRE_HOURS)
    token = jwt.encode(
        {"sub": username, "role": "admin", "exp": expire},
        settings.SECRET_KEY,
        algorithm=ADMIN_JWT_ALGORITHM,
    )
    return {"access_token": token, "token_type": "bearer", "username": username}


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(admin_security),
):
    """验证 Admin JWT — 检查 role=admin claim"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[ADMIN_JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired admin token")

    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload.get("sub")


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
async def list_artists(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """获取画家池列表（含参考图 URL）"""
    query = select(Artist).order_by(Artist.category, Artist.sort_order, Artist.name)
    if active_only:
        query = query.where(Artist.active == True)
    result = await db.execute(query)
    artists = result.scalars().all()

    items = []
    for a in artists:
        items.append({
            "id": str(a.id),
            "key": a.key,
            "name": a.name,
            "style": a.style,
            "masterwork_url": a.masterwork_url,
            "painting": a.painting,
            "category": a.category,
            "active": a.active,
            "sort_order": a.sort_order,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return {"artists": items, "total": len(items)}


@router.post("/artists")
async def create_artist(
    data: dict,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """新增画家"""
    # 检查 key 唯一性
    existing = await db.scalar(select(Artist).where(Artist.key == data.get("key", "").upper()))
    if existing:
        raise HTTPException(status_code=400, detail=f"Artist key '{data['key']}' already exists")

    artist = Artist(
        key=data["key"].upper(),
        name=data["name"],
        style=data["style"],
        masterwork_url=data.get("masterwork_url"),
        painting=data.get("painting"),
        category=data.get("category"),
        active=data.get("active", True),
        sort_order=data.get("sort_order", 0),
    )
    db.add(artist)
    await db.commit()
    await db.refresh(artist)
    return {"id": str(artist.id), "key": artist.key, "name": artist.name}


@router.put("/artists/{artist_id}")
async def update_artist(
    artist_id: str,
    data: dict,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新画家信息"""
    result = await db.execute(select(Artist).where(Artist.id == UUID(artist_id)))
    artist = result.scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    # 更新允许的字段
    for field in ["name", "style", "masterwork_url", "painting", "category", "active", "sort_order"]:
        if field in data:
            setattr(artist, field, data[field])

    # key 需要检查唯一性
    if "key" in data and data["key"].upper() != artist.key:
        existing = await db.scalar(select(Artist).where(Artist.key == data["key"].upper()))
        if existing:
            raise HTTPException(status_code=400, detail=f"Key '{data['key']}' already in use")
        artist.key = data["key"].upper()

    await db.commit()
    await db.refresh(artist)
    return {"id": str(artist.id), "key": artist.key, "name": artist.name, "active": artist.active}


@router.delete("/artists/{artist_id}")
async def delete_artist(
    artist_id: str,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除画家（软删除 — 标记为 inactive）"""
    result = await db.execute(select(Artist).where(Artist.id == UUID(artist_id)))
    artist = result.scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    artist.active = False
    await db.commit()
    return {"message": f"Artist '{artist.name}' deactivated", "id": str(artist.id)}


# ===== API Call Monitoring =====
@router.get("/api-calls")
async def list_api_calls(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    model: Optional[str] = None,
    status: Optional[str] = None,
    endpoint: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),  # 默认最近24小时，最多7天
    db: AsyncSession = Depends(get_db),
):
    """获取 API 调用日志列表"""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = select(ApiCallLog).where(ApiCallLog.created_at >= since)

    if model:
        query = query.where(ApiCallLog.model == model)
    if status:
        query = query.where(ApiCallLog.status == status)
    if endpoint:
        query = query.where(ApiCallLog.endpoint == endpoint)

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.order_by(desc(ApiCallLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    items = []
    for log in logs:
        items.append({
            "id": str(log.id),
            "model": log.model,
            "endpoint": log.endpoint,
            "status": log.status,
            "duration_ms": log.duration_ms,
            "tokens_input": log.tokens_input,
            "tokens_output": log.tokens_output,
            "error": log.error,
            "request_payload": log.request_payload,
            "response_summary": log.response_summary,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return {"calls": items, "total": total or 0, "page": page, "page_size": page_size}


@router.get("/api-stats")
async def get_api_stats(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """API 调用统计聚合 — RPM, TPM, 平均延迟, 错误率, 按模型分组"""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    # 总体统计
    total_calls = await db.scalar(
        select(func.count()).select_from(ApiCallLog).where(ApiCallLog.created_at >= since)
    ) or 0
    success_calls = await db.scalar(
        select(func.count()).select_from(ApiCallLog).where(
            ApiCallLog.created_at >= since, ApiCallLog.status == "success"
        )
    ) or 0
    failed_calls = total_calls - success_calls

    # 平均延迟（仅成功的）
    avg_latency = await db.scalar(
        select(func.avg(ApiCallLog.duration_ms)).where(
            ApiCallLog.created_at >= since, ApiCallLog.status == "success"
        )
    ) or 0

    # Token 总计
    total_tokens_in = await db.scalar(
        select(func.sum(ApiCallLog.tokens_input)).where(ApiCallLog.created_at >= since)
    ) or 0
    total_tokens_out = await db.scalar(
        select(func.sum(ApiCallLog.tokens_output)).where(ApiCallLog.created_at >= since)
    ) or 0

    # RPM 和 TPM（基于时间窗口）
    minutes = hours * 60
    rpm = round(total_calls / minutes, 2) if minutes > 0 else 0
    tpm = round((total_tokens_in + total_tokens_out) / minutes, 2) if minutes > 0 else 0

    # 按模型分组统计
    model_stats_query = (
        select(
            ApiCallLog.model,
            func.count().label("calls"),
            func.avg(ApiCallLog.duration_ms).label("avg_latency"),
            func.sum(case((ApiCallLog.status == "success", 1), else_=0)).label("successes"),
            func.sum(case((ApiCallLog.status != "success", 1), else_=0)).label("failures"),
            func.sum(ApiCallLog.tokens_input).label("tokens_in"),
            func.sum(ApiCallLog.tokens_output).label("tokens_out"),
        )
        .where(ApiCallLog.created_at >= since)
        .group_by(ApiCallLog.model)
    )
    model_result = await db.execute(model_stats_query)
    model_rows = model_result.all()

    model_breakdown = []
    for row in model_rows:
        model_breakdown.append({
            "model": row.model,
            "calls": row.calls,
            "avg_latency_ms": round(row.avg_latency) if row.avg_latency else 0,
            "successes": int(row.successes or 0),
            "failures": int(row.failures or 0),
            "error_rate": round(int(row.failures or 0) / row.calls * 100, 1) if row.calls > 0 else 0,
            "tokens_in": int(row.tokens_in or 0),
            "tokens_out": int(row.tokens_out or 0),
        })

    # 按 endpoint 分组
    endpoint_stats_query = (
        select(
            ApiCallLog.endpoint,
            func.count().label("calls"),
            func.avg(ApiCallLog.duration_ms).label("avg_latency"),
            func.sum(case((ApiCallLog.status != "success", 1), else_=0)).label("failures"),
        )
        .where(ApiCallLog.created_at >= since)
        .group_by(ApiCallLog.endpoint)
    )
    endpoint_result = await db.execute(endpoint_stats_query)
    endpoint_rows = endpoint_result.all()

    endpoint_breakdown = []
    for row in endpoint_rows:
        endpoint_breakdown.append({
            "endpoint": row.endpoint,
            "calls": row.calls,
            "avg_latency_ms": round(row.avg_latency) if row.avg_latency else 0,
            "failures": int(row.failures or 0),
        })

    return {
        "period_hours": hours,
        "total_calls": total_calls,
        "success_calls": success_calls,
        "failed_calls": failed_calls,
        "error_rate": round(failed_calls / total_calls * 100, 1) if total_calls > 0 else 0,
        "avg_latency_ms": round(avg_latency),
        "rpm": rpm,
        "tpm": tpm,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "model_breakdown": model_breakdown,
        "endpoint_breakdown": endpoint_breakdown,
    }


# ===== Gallery Review (Featured/Approved) =====
@router.get("/gallery/pending")
async def gallery_pending(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取待审核列表 — 已完成但未上架的图片/视频"""
    query = (
        select(Generation)
        .where(
            Generation.status == "completed",
            Generation.featured == False,
            Generation.result_url.isnot(None),
        )
        .order_by(desc(Generation.created_at))
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    generations = result.scalars().all()

    items = []
    for g in generations:
        dream_result = await db.execute(select(Dream.title, Dream.content).where(Dream.id == g.dream_id))
        dream_row = dream_result.one_or_none()
        dream_title = (dream_row.title or dream_row.content[:30]) if dream_row else "Unknown"

        user_result = await db.execute(select(User.email, User.nickname).where(User.id == g.user_id))
        user_row = user_result.one_or_none()
        user_name = (user_row.nickname or user_row.email.split("@")[0]) if user_row else "Unknown"

        items.append({
            "id": str(g.id),
            "type": g.type,
            "dream_title": dream_title,
            "dream_content": dream_row.content[:80] if dream_row else "",
            "user": user_name,
            "result_url": g.result_url,
            "metadata": g.metadata_json,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/gallery/featured")
async def gallery_featured(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取已上架列表"""
    query = (
        select(Generation)
        .where(Generation.featured == True)
        .order_by(desc(Generation.featured_at))
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    generations = result.scalars().all()

    items = []
    for g in generations:
        dream_result = await db.execute(select(Dream.title, Dream.content).where(Dream.id == g.dream_id))
        dream_row = dream_result.one_or_none()
        dream_title = (dream_row.title or dream_row.content[:30]) if dream_row else "Unknown"

        user_result = await db.execute(select(User.email, User.nickname).where(User.id == g.user_id))
        user_row = user_result.one_or_none()
        user_name = (user_row.nickname or user_row.email.split("@")[0]) if user_row else "Unknown"

        items.append({
            "id": str(g.id),
            "type": g.type,
            "dream_title": dream_title,
            "user": user_name,
            "result_url": g.result_url,
            "featured_at": g.featured_at.isoformat() if g.featured_at else None,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/gallery/approve")
async def gallery_approve(
    data: dict,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """批量上架 — 把指定 generation 标记为 featured"""
    ids = data.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="No ids provided")

    now = datetime.now(timezone.utc)
    for gid in ids:
        result = await db.execute(select(Generation).where(Generation.id == UUID(gid)))
        gen = result.scalar_one_or_none()
        if gen and gen.status == "completed":
            gen.featured = True
            gen.featured_at = now

    await db.commit()
    return {"message": f"Approved {len(ids)} items", "ids": ids}


@router.post("/gallery/reject")
async def gallery_reject(
    data: dict,
    admin_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """下架 — 把指定 generation 取消 featured"""
    ids = data.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="No ids provided")

    for gid in ids:
        result = await db.execute(select(Generation).where(Generation.id == UUID(gid)))
        gen = result.scalar_one_or_none()
        if gen:
            gen.featured = False
            gen.featured_at = None

    await db.commit()
    return {"message": f"Rejected {len(ids)} items", "ids": ids}
