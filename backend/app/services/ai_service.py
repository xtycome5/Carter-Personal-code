"""
DashScope AI Service - 阿里云百炼 AI 接口封装
支持：提示词扩写、图片生成(万相)、视频生成(万相)

调用链路:
  用户描述 → PromptExpansionService(LLM扩写) → 生图/生视频 API
"""
import httpx
from typing import Optional
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
        
        # 构建 messages 格式
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

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["output"]["task_id"]

    async def generate_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        resolution: str = "720P",
        duration: int = 5,
        ratio: str = "16:9",
    ) -> str:
        """
        异步提交视频生成任务，返回 task_id
        注意：传入的 prompt 应该是已经过 expand_prompt() 扩写后的
        
        视频模型自带 prompt_extend 参数，但我们在外层已做了更精细的梦境扩写，
        所以此处关闭模型自带的 prompt_extend，避免二次扩写导致语义偏移。
        """
        url = f"{self.base_url}/api/v1/services/aigc/video-generation/video-synthesis"

        payload = {
            "model": settings.VIDEO_MODEL,
            "input": {
                "prompt": prompt,
            },
            "parameters": {
                "resolution": resolution,
                "duration": duration,
                "ratio": ratio,
                "prompt_extend": False,  # 关闭模型自带扩写，使用我们的扩写结果
            },
        }

        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt

        headers = {
            **self.headers,
            "X-DashScope-Async": "enable",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["output"]["task_id"]

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
                # 图片生成返回 results 数组
                if "results" in output:
                    result["result_url"] = output["results"][0].get("url", "")
                # 视频生成返回 video_url
                elif "video_url" in output:
                    result["result_url"] = output["video_url"]

            elif status == "FAILED":
                result["error"] = output.get("message", "Generation failed")

            return result


# Singleton
dashscope_service = DashScopeService()
