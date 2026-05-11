"""
Generate Routes - AI 生成（提示词扩写 + 图片 + 视频）

调用链路：
  用户梦境描述 → [Prompt Expansion: LLM 智能扩写] → [生图/生视频 API]
  
提示词扩写在每次生成前自动执行，无需前端额外调用 enhance 接口。
enhance 接口仍保留，用于用户手动预览扩写效果。
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import Dream, Generation
from app.schemas.schemas import (
    GenerateImageRequest, GenerateVideoRequest, EnhanceRequest,
    GenerationResponse, TaskStatusResponse
)
from app.core.security import get_current_user
from app.services.ai_service import dashscope_service

router = APIRouter(prefix="/api/generate", tags=["generate"])


@router.post("/enhance")
async def enhance_description(
    data: EnhanceRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI 提示词扩写（预览）
    
    用户可以先调用此接口预览扩写效果，再决定是否生成。
    扩写结果会保存到 dream.enhanced_content。
    """
    result = await db.execute(
        select(Dream).where(Dream.id == data.dream_id, Dream.user_id == UUID(user_id))
    )
    dream = result.scalar_one_or_none()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")

    try:
        # 调用 Prompt Expansion Service
        enhanced = await dashscope_service.expand_prompt(
            content=dream.content,
            gen_type="image",
            style=data.style,
            mood=dream.mood,
        )
        # 保存扩写结果
        dream.enhanced_content = enhanced
        await db.commit()
        await db.refresh(dream)

        return {
            "enhanced_content": enhanced,
            "dream_id": str(dream.id),
            "original_content": dream.content,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt expansion failed: {str(e)}")


@router.post("/image", response_model=GenerationResponse)
async def generate_image(
    data: GenerateImageRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    生成梦境图片
    
    流程：
    1. 获取梦境记录
    2. 调用 Prompt Expansion Service 扩写描述（LLM 智能扩写）
    3. 将扩写后的 prompt 提交到万相图片生成 API
    4. 保存扩写结果和生成记录
    """
    # 获取梦境
    result = await db.execute(
        select(Dream).where(Dream.id == data.dream_id, Dream.user_id == UUID(user_id))
    )
    dream = result.scalar_one_or_none()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")

    try:
        # ===== Step 1: Prompt Expansion（核心扩写步骤）=====
        expanded_prompt = await dashscope_service.expand_prompt(
            content=dream.content,  # 始终基于原始描述扩写，保证新鲜度
            gen_type="image",
            style=data.style,
            mood=dream.mood,
        )

        # 保存扩写结果到梦境记录
        dream.enhanced_content = expanded_prompt
        await db.flush()

        # ===== Step 2: 提交图片生成任务 =====
        task_id = await dashscope_service.generate_image(
            prompt=expanded_prompt,
            negative_prompt=data.negative_prompt or _get_default_negative_prompt(),
            size=data.size,
            n=data.count,
        )

        # ===== Step 3: 保存生成记录 =====
        generation = Generation(
            dream_id=dream.id,
            user_id=UUID(user_id),
            type="image",
            style=data.style,
            prompt=expanded_prompt,
            negative_prompt=data.negative_prompt,
            status="processing",
            task_id=task_id,
            metadata_json={
                "size": data.size,
                "count": data.count,
                "original_content": dream.content,
            },
        )
        db.add(generation)
        await db.commit()
        await db.refresh(generation)

        return GenerationResponse.model_validate(generation)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/video", response_model=GenerationResponse)
async def generate_video(
    data: GenerateVideoRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    生成梦境视频
    
    智能选择生成模式：
    - 若该 dream 已有生成成功的图片 → 图生视频 (I2V)，以图片为参考
    - 若没有现成图片 → 文生视频 (T2V)，纯文本生成
    """
    # 获取梦境
    result = await db.execute(
        select(Dream).where(Dream.id == data.dream_id, Dream.user_id == UUID(user_id))
    )
    dream = result.scalar_one_or_none()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")

    try:
        # ===== Step 1: 检查是否有已完成的图片生成 =====
        image_result = await db.execute(
            select(Generation).where(
                Generation.dream_id == dream.id,
                Generation.type == "image",
                Generation.status == "completed",
            ).order_by(Generation.created_at.desc()).limit(1)
        )
        existing_image = image_result.scalar_one_or_none()
        use_i2v = existing_image and existing_image.result_url

        # ===== Step 2: Prompt Expansion（视频专用扩写）=====
        expanded_prompt = await dashscope_service.expand_prompt(
            content=dream.content,
            gen_type="video",
            style=data.style,
            mood=dream.mood,
        )

        # 保存扩写结果
        dream.enhanced_content = expanded_prompt
        await db.flush()

        # ===== Step 3: 提交视频生成任务（I2V 或 T2V）=====
        if use_i2v:
            # 有参考图 → 图生视频
            task_id = await dashscope_service.generate_video_from_image(
                prompt=expanded_prompt,
                image_url=existing_image.result_url,
                negative_prompt=_get_default_negative_prompt(),
                resolution=data.resolution,
                duration=data.duration,
                ratio=data.ratio,
            )
            gen_mode = "i2v"
        else:
            # 无参考图 → 文生视频
            task_id = await dashscope_service.generate_video(
                prompt=expanded_prompt,
                negative_prompt=_get_default_negative_prompt(),
                resolution=data.resolution,
                duration=data.duration,
                ratio=data.ratio,
            )
            gen_mode = "t2v"

        # ===== Step 4: 保存生成记录 =====
        generation = Generation(
            dream_id=dream.id,
            user_id=UUID(user_id),
            type="video",
            style=data.style,
            prompt=expanded_prompt,
            status="processing",
            task_id=task_id,
            metadata_json={
                "duration": data.duration,
                "mode": gen_mode,
                "reference_image": existing_image.result_url if use_i2v else None,
                "original_content": dream.content,
            },
        )
        db.add(generation)
        await db.commit()
        await db.refresh(generation)

        return GenerationResponse.model_validate(generation)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.get("/task/{generation_id}", response_model=TaskStatusResponse)
async def check_generation_status(
    generation_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询生成任务状态"""
    result = await db.execute(
        select(Generation).where(
            Generation.id == generation_id,
            Generation.user_id == UUID(user_id),
        )
    )
    generation = result.scalar_one_or_none()
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    # 如果已完成，直接返回
    if generation.status in ["completed", "failed"]:
        return TaskStatusResponse(
            id=generation.id,
            status=generation.status,
            result_url=generation.result_url,
            type=generation.type,
        )

    # 查询 DashScope 任务状态
    if not generation.task_id:
        raise HTTPException(status_code=400, detail="No task ID associated")

    try:
        task_result = await dashscope_service.check_task_status(generation.task_id)
        dash_status = task_result["status"]

        # 更新本地状态
        if dash_status == "SUCCEEDED":
            generation.status = "completed"
            generation.result_url = task_result.get("result_url", "")
        elif dash_status == "FAILED":
            generation.status = "failed"
        # PENDING / RUNNING 保持 processing

        await db.commit()
        await db.refresh(generation)

        return TaskStatusResponse(
            id=generation.id,
            status=generation.status,
            result_url=generation.result_url,
            type=generation.type,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


def _get_default_negative_prompt() -> str:
    """默认负面提示词 - 排除常见质量问题"""
    return (
        "blurry, low quality, distorted face, extra limbs, "
        "watermark, text overlay, logo, banner, "
        "oversaturated, underexposed, grainy noise, "
        "ugly, deformed, disfigured, poorly drawn"
    )
