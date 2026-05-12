"""
DashScope AI Service - 阿里云百炼 AI 接口封装
支持：提示词扩写、图片生成(万相)、视频生成(万相)

调用链路:
  用户描述 → PromptExpansionService(LLM扩写) → 生图/生视频 API
"""
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)
from app.core.config import settings
from app.services.prompt_expansion import prompt_expansion_service


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
    ) -> str:
        """
        提示词扩写 - 在调用生图/生视频之前必须先调用此方法
        
        将用户的梦境描述通过 LLM 智能扩写为高质量的图像/视频生成 prompt。
        采用 Qwen-Image 官方方案：LLM 调用 + 结构化 System Prompt + Magic Tokens
        
        Args:
            content: 用户原始梦境描述（中文或英文）
            gen_type: "image" 或 "video"
            style: 风格选项 (surreal/watercolor/cyberpunk/classical/ghibli/gothic/dali/dreamlike)
            mood: 情绪标记 (fantasy/peaceful/scary/sad/exciting/romantic/mysterious/nostalgic)
        
        Returns:
            扩写后的完整 prompt，可直接传入生图/生视频 API
        """
        return await prompt_expansion_service.expand(
            content=content,
            gen_type=gen_type,
            style=style,
            mood=mood,
        )

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: str = "1024*1024",
        n: int = 1,
    ) -> str:
        """
        异步提交图片生成任务，返回 task_id
        注意：传入的 prompt 应该是已经过 expand_prompt() 扩写后的
        """
        url = f"{self.base_url}/api/v1/services/aigc/image-generation/generation"
        
        # wan2.7-image 使用 messages 格式
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

        logger.info(f"[T2I] POST {url} | model={payload['model']} | prompt={prompt[:80]}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            task_id = data["output"]["task_id"]
            logger.info(f"[T2I] task_id={task_id}")
            return task_id

    async def generate_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        resolution: str = "720P",
        duration: int = 5,
        ratio: str = "16:9",
    ) -> str:
        """
        文生视频 (T2V) - 异步提交视频生成任务，返回 task_id
        无参考图，纯文本生成视频 (happyhorse-1.0-t2v)
        """
        url = f"{self.base_url}/api/v1/services/aigc/video-generation/video-synthesis"

        payload = {
            "model": settings.VIDEO_MODEL,
            "input": {
                "prompt": prompt,
            },
            "parameters": {
                "resolution": resolution,
                "ratio": ratio,
                "duration": duration,
            },
        }

        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt

        headers = {
            **self.headers,
            "X-DashScope-Async": "enable",
        }

        logger.info(f"[T2V] POST {url} | model={payload['model']} | prompt={prompt[:80]}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            task_id = data["output"]["task_id"]
            logger.info(f"[T2V] task_id={task_id}")
            return task_id

    async def generate_video_from_image(
        self,
        prompt: str,
        image_url: str,
        negative_prompt: Optional[str] = None,
        resolution: str = "720P",
        duration: int = 5,
        ratio: str = "16:9",
    ) -> str:
        """
        图生视频 (I2V) - 以首帧图为基础生成视频，返回 task_id
        当 dream 已有生成好的图片时使用此方法 (happyhorse-1.0-i2v)
        """
        url = f"{self.base_url}/api/v1/services/aigc/video-generation/video-synthesis"

        payload = {
            "model": settings.VIDEO_I2V_MODEL,
            "input": {
                "prompt": prompt,
                "media": [{"type": "first_frame", "url": image_url}],
            },
            "parameters": {
                "resolution": resolution,
                "ratio": ratio,
                "duration": duration,
            },
        }

        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt

        headers = {
            **self.headers,
            "X-DashScope-Async": "enable",
        }

        logger.info(f"[I2V] POST {url} | model={payload['model']} | image={image_url[:60]}... | prompt={prompt[:60]}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            task_id = data["output"]["task_id"]
            logger.info(f"[I2V] task_id={task_id}")
            return task_id

    async def generate_video_from_reference(
        self,
        prompt: str,
        reference_image_urls: list[str],
        negative_prompt: Optional[str] = None,
        resolution: str = "720P",
        duration: int = 5,
        ratio: str = "16:9",
    ) -> str:
        """
        参考生视频 (R2V) - 以参考图为风格/主体参考生成视频，返回 task_id
        当用户先生图后生视频时使用此方法 (happyhorse-1.0-r2v)
        
        与 I2V 区别：I2V 以图片为首帧，R2V 以图片为风格/主体参考
        """
        url = f"{self.base_url}/api/v1/services/aigc/video-generation/video-synthesis"

        media = [{"type": "reference_image", "url": u} for u in reference_image_urls]

        payload = {
            "model": settings.VIDEO_R2V_MODEL,
            "input": {
                "prompt": prompt,
                "media": media,
            },
            "parameters": {
                "resolution": resolution,
                "ratio": ratio,
                "duration": duration,
            },
        }

        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt

        headers = {
            **self.headers,
            "X-DashScope-Async": "enable",
        }

        logger.info(f"[R2V] POST {url} | model={payload['model']} | refs={[u[:50] for u in reference_image_urls]} | prompt={prompt[:60]}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            task_id = data["output"]["task_id"]
            logger.info(f"[R2V] task_id={task_id}")
            return task_id

    async def generate_image_from_reference(
        self,
        prompt: str,
        reference_image_url: str,
        negative_prompt: Optional[str] = None,
        size: str = "1024*1024",
        n: int = 1,
    ) -> str:
        """
        参考生图 (V2I) - 以参考图（视频帧）为基础生成图片，返回 task_id
        当用户先生视频后生图时使用此方法 (wan2.7-image-pro)
        
        使用 messages 格式：content 中先放 image URL，再放 text prompt
        """
        url = f"{self.base_url}/api/v1/services/aigc/image-generation/generation"

        content = [
            {"image": reference_image_url},
            {"text": prompt},
        ]

        payload = {
            "model": settings.IMAGE_PRO_MODEL,
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

        logger.info(f"[V2I] POST {url} | model={payload['model']} | ref_img={reference_image_url[:60]}... | prompt={prompt[:60]}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            task_id = data["output"]["task_id"]
            logger.info(f"[V2I] task_id={task_id}")
            return task_id

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
