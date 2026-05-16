"""
DashScope AI Service - 阿里云百炼 AI 接口封装
支持：提示词扩写、图片生成(万相)、视频生成(万相)

调用链路 (Two-Step Pipeline):
  用户描述 → CreativeDirector(意图+场景分析) → PromptExpansion(画家池/FPV改写) → 生图/生视频 API
"""
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)
from app.core.config import settings
from app.services.prompt_expansion import prompt_expansion_service
from app.services.creative_director import creative_director_service
from app.services.api_logger import ApiCallTimer, log_api_call, fire_and_forget


class DashScopeService:
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def expand_prompt(
        self,
        content: str,
        gen_type: str = "image",
        style: Optional[str] = None,
        mood: Optional[str] = None,
    ) -> tuple[str, list[str]]:
        """
        提示词扩写 - Two-Step Pipeline
        
        Step 1 (Creative Director): 理解梦境意图、补全场景、输出结构化分析
        Step 2 (Prompt Expansion): 基于结构化分析 + 画家池/FPV约束 生成最终 prompt
        
        Args:
            content: 用户原始梦境描述（中文或英文）
            gen_type: "image" 或 "video"
            style: (保留参数兼容，不再使用)
            mood: (保留参数兼容，不再使用)
        
        Returns:
            tuple of (扩写后的完整 prompt, 选中画家的参考图 URL 列表)
        """
        # === Step 1: Creative Director 分析 ===
        logger.info(f"[Pipeline] Step 1: Creative Director analyzing dream (gen_type={gen_type})")
        dream_analysis = await creative_director_service.analyze(
            content=content,
            gen_type=gen_type,
        )

        # === Step 2: Prompt Expansion 改写 ===
        logger.info(f"[Pipeline] Step 2: Prompt Expansion with dream analysis")
        return await prompt_expansion_service.expand(
            content=content,
            gen_type=gen_type,
            style=style,
            mood=mood,
            dream_analysis=dream_analysis,
        )

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: str = "1024*1024",
        n: int = 1,
    ) -> str:
        """
        异步调用 wan2.7-image-pro 生成图片，返回 task_id
        wan2.7-image-pro 使用异步模式，需要前端轮询 check_task_status 获取结果
        支持尺寸: 1024*1024, 720*1280, 1280*720, 768*1024, 1024*768
        """
        url = f"{self.base_url}/api/v1/services/aigc/image-generation/generation"

        content = [{"text": prompt}]

        payload = {
            "model": settings.IMAGE_MODEL,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": content,
                    }
                ]
            },
            "parameters": {
                "size": size,
                "n": n,
            },
        }

        if negative_prompt:
            payload["parameters"]["negative_prompt"] = negative_prompt

        headers = {
            **self.headers,
            "X-DashScope-Async": "enable",
        }

        logger.info(f"[T2I] POST {url} | model={payload['model']} | size={size} | prompt={prompt[:80]}...")

        timer = ApiCallTimer()
        timer.start()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                task_id = data["output"]["task_id"]
                timer.stop()
                logger.info(f"[T2I] task_id={task_id}")
                fire_and_forget(log_api_call(
                    model=settings.IMAGE_MODEL, endpoint="image_generation",
                    status="success", duration_ms=timer.duration_ms,
                    request_payload={"size": size, "n": n},
                    response_summary={"task_id": task_id},
                ))
                return task_id
        except Exception as e:
            timer.stop()
            fire_and_forget(log_api_call(
                model=settings.IMAGE_MODEL, endpoint="image_generation",
                status="failed", duration_ms=timer.duration_ms,
                error=str(e)[:500],
            ))
            raise

    async def generate_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        resolution: str = "720P",
        duration: int = 10,
        ratio: str = "16:9",
    ) -> str:
        """文生视频 (T2V) - 异步提交，返回 task_id"""
        url = f"{self.base_url}/api/v1/services/aigc/video-generation/video-synthesis"

        payload = {
            "model": settings.VIDEO_MODEL,
            "input": {"prompt": prompt},
            "parameters": {"resolution": resolution, "ratio": ratio, "duration": duration},
        }
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt

        headers = {**self.headers, "X-DashScope-Async": "enable"}
        logger.info(f"[T2V] POST {url} | model={payload['model']} | prompt={prompt[:80]}...")

        timer = ApiCallTimer()
        timer.start()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                task_id = data["output"]["task_id"]
                timer.stop()
                logger.info(f"[T2V] task_id={task_id}")
                fire_and_forget(log_api_call(
                    model=settings.VIDEO_MODEL, endpoint="video_generation_t2v",
                    status="success", duration_ms=timer.duration_ms,
                    request_payload={"resolution": resolution, "duration": duration, "ratio": ratio},
                    response_summary={"task_id": task_id},
                ))
                return task_id
        except Exception as e:
            timer.stop()
            fire_and_forget(log_api_call(
                model=settings.VIDEO_MODEL, endpoint="video_generation_t2v",
                status="failed", duration_ms=timer.duration_ms, error=str(e)[:500],
            ))
            raise

    async def generate_video_from_image(
        self,
        prompt: str,
        image_url: str,
        negative_prompt: Optional[str] = None,
        resolution: str = "720P",
        duration: int = 10,
        ratio: str = "16:9",
    ) -> str:
        """图生视频 (I2V) - 以首帧图为基础，返回 task_id"""
        url = f"{self.base_url}/api/v1/services/aigc/video-generation/video-synthesis"

        payload = {
            "model": settings.VIDEO_I2V_MODEL,
            "input": {"prompt": prompt, "media": [{"type": "first_frame", "url": image_url}]},
            "parameters": {"resolution": resolution, "ratio": ratio, "duration": duration},
        }
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt

        headers = {**self.headers, "X-DashScope-Async": "enable"}
        logger.info(f"[I2V] POST {url} | model={payload['model']} | image={image_url[:60]}... | prompt={prompt[:60]}...")

        timer = ApiCallTimer()
        timer.start()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                task_id = data["output"]["task_id"]
                timer.stop()
                logger.info(f"[I2V] task_id={task_id}")
                fire_and_forget(log_api_call(
                    model=settings.VIDEO_I2V_MODEL, endpoint="video_generation_i2v",
                    status="success", duration_ms=timer.duration_ms,
                    request_payload={"resolution": resolution, "duration": duration},
                    response_summary={"task_id": task_id},
                ))
                return task_id
        except Exception as e:
            timer.stop()
            fire_and_forget(log_api_call(
                model=settings.VIDEO_I2V_MODEL, endpoint="video_generation_i2v",
                status="failed", duration_ms=timer.duration_ms, error=str(e)[:500],
            ))
            raise

    async def generate_video_from_reference(
        self,
        prompt: str,
        reference_image_urls: list[str],
        negative_prompt: Optional[str] = None,
        resolution: str = "720P",
        duration: int = 10,
        ratio: str = "16:9",
    ) -> str:
        """参考生视频 (R2V) - 以参考图为风格参考，返回 task_id"""
        url = f"{self.base_url}/api/v1/services/aigc/video-generation/video-synthesis"

        media = [{"type": "reference_image", "url": u} for u in reference_image_urls]
        payload = {
            "model": settings.VIDEO_R2V_MODEL,
            "input": {"prompt": prompt, "media": media},
            "parameters": {"resolution": resolution, "ratio": ratio, "duration": duration},
        }
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt

        headers = {**self.headers, "X-DashScope-Async": "enable"}
        logger.info(f"[R2V] POST {url} | model={payload['model']} | refs={[u[:50] for u in reference_image_urls]} | prompt={prompt[:60]}...")

        timer = ApiCallTimer()
        timer.start()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                task_id = data["output"]["task_id"]
                timer.stop()
                logger.info(f"[R2V] task_id={task_id}")
                fire_and_forget(log_api_call(
                    model=settings.VIDEO_R2V_MODEL, endpoint="video_generation_r2v",
                    status="success", duration_ms=timer.duration_ms,
                    request_payload={"resolution": resolution, "duration": duration},
                    response_summary={"task_id": task_id},
                ))
                return task_id
        except Exception as e:
            timer.stop()
            fire_and_forget(log_api_call(
                model=settings.VIDEO_R2V_MODEL, endpoint="video_generation_r2v",
                status="failed", duration_ms=timer.duration_ms, error=str(e)[:500],
            ))
            raise

    async def generate_image_from_reference(
        self,
        prompt: str,
        reference_image_url: str,
        negative_prompt: Optional[str] = None,
        size: str = "1024*1024",
        n: int = 1,
    ) -> str:
        """参考生图 (V2I) - 以参考图为基础，返回 task_id"""
        url = f"{self.base_url}/api/v1/services/aigc/image-generation/generation"

        content = [{"image": reference_image_url}, {"text": prompt}]
        payload = {
            "model": settings.IMAGE_PRO_MODEL,
            "input": {"messages": [{"role": "user", "content": content}]},
            "parameters": {"size": size, "n": n},
        }
        if negative_prompt:
            payload["parameters"]["negative_prompt"] = negative_prompt

        headers = {**self.headers, "X-DashScope-Async": "enable"}
        logger.info(f"[V2I] POST {url} | model={payload['model']} | ref_img={reference_image_url[:60]}... | prompt={prompt[:60]}...")

        timer = ApiCallTimer()
        timer.start()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                task_id = data["output"]["task_id"]
                timer.stop()
                logger.info(f"[V2I] task_id={task_id}")
                fire_and_forget(log_api_call(
                    model=settings.IMAGE_PRO_MODEL, endpoint="image_generation_v2i",
                    status="success", duration_ms=timer.duration_ms,
                    request_payload={"size": size},
                    response_summary={"task_id": task_id},
                ))
                return task_id
        except Exception as e:
            timer.stop()
            fire_and_forget(log_api_call(
                model=settings.IMAGE_PRO_MODEL, endpoint="image_generation_v2i",
                status="failed", duration_ms=timer.duration_ms, error=str(e)[:500],
            ))
            raise

    async def check_task_status(self, task_id: str) -> dict:
        """查询异步任务状态"""
        url = f"{self.base_url}/api/v1/tasks/{task_id}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            output = data.get("output", {})
            status = output.get("task_status", "UNKNOWN")

            result = {
                "status": status,
                "task_id": task_id,
            }

            if status == "SUCCEEDED":
                # wan2.7-image 返回 choices 格式
                if "choices" in output:
                    choices = output["choices"]
                    if choices:
                        msg_content = choices[0].get("message", {}).get("content", [])
                        for item in msg_content:
                            if item.get("type") == "image" or "image" in item:
                                result["result_url"] = item.get("image", "")
                                break
                # 旧版图片模型返回 results 数组
                elif "results" in output:
                    result["result_url"] = output["results"][0].get("url", "")
                # 视频生成返回 video_url
                elif "video_url" in output:
                    result["result_url"] = output["video_url"]

            elif status == "FAILED":
                result["error"] = output.get("message", "Generation failed")

            return result


# Singleton
dashscope_service = DashScopeService()
