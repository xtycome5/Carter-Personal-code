"""
Dreams Routes - 梦境记录 CRUD
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.models import Dream, Generation
from app.schemas.schemas import (
    DreamCreate, DreamUpdate, DreamResponse, DreamListResponse
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/dreams", tags=["dreams"])


@router.post("", response_model=DreamResponse)
async def create_dream(
    data: DreamCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建梦境记录"""
    dream = Dream(
        user_id=UUID(user_id),
        title=data.title,
        content=data.content,
        mood=data.mood,
        tags=data.tags or [],
        is_public=data.is_public or False,
    )
    db.add(dream)
    await db.commit()
    # Re-query with eager loading to avoid MissingGreenlet on serialization
    result = await db.execute(
        select(Dream).where(Dream.id == dream.id).options(selectinload(Dream.generations))
    )
    dream = result.scalar_one()
    return DreamResponse.model_validate(dream)


@router.get("", response_model=DreamListResponse)
async def list_dreams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    mood: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取梦境列表（分页）"""
    query = (
        select(Dream)
        .where(Dream.user_id == UUID(user_id))
        .options(selectinload(Dream.generations))
        .order_by(Dream.created_at.desc())
    )

    if mood:
        query = query.where(Dream.mood == mood)

    # Count total
    count_query = select(func.count()).select_from(Dream).where(Dream.user_id == UUID(user_id))
    if mood:
        count_query = count_query.where(Dream.mood == mood)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    dreams = result.scalars().all()

    return DreamListResponse(
        dreams=[DreamResponse.model_validate(d) for d in dreams],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{dream_id}", response_model=DreamResponse)
async def get_dream(
    dream_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单条梦境详情"""
    result = await db.execute(
        select(Dream)
        .where(Dream.id == dream_id, Dream.user_id == UUID(user_id))
        .options(selectinload(Dream.generations))
    )
    dream = result.scalar_one_or_none()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    return DreamResponse.model_validate(dream)


@router.put("/{dream_id}", response_model=DreamResponse)
async def update_dream(
    dream_id: UUID,
    data: DreamUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新梦境记录"""
    result = await db.execute(
        select(Dream).where(Dream.id == dream_id, Dream.user_id == UUID(user_id))
    )
    dream = result.scalar_one_or_none()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dream, field, value)

    await db.commit()
    # Re-query with eager loading to avoid MissingGreenlet on serialization
    result2 = await db.execute(
        select(Dream).where(Dream.id == dream_id).options(selectinload(Dream.generations))
    )
    dream = result2.scalar_one()
    return DreamResponse.model_validate(dream)


@router.delete("/{dream_id}")
async def delete_dream(
    dream_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除梦境记录"""
    result = await db.execute(
        select(Dream).where(Dream.id == dream_id, Dream.user_id == UUID(user_id))
    )
    dream = result.scalar_one_or_none()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")

    await db.delete(dream)
    await db.commit()
    return {"message": "Dream deleted successfully"}
