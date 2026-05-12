"""
Prompt Expansion Service - 提示词扩写服务

以四位大师的艺术语言为基底，生成超现实梦境提示词：
- 达利 — 融化的形态、扭曲的时空、精细渲染的不可能之物
- 夏加尔 — 失重漂浮、宝石色调、诗意温柔的彩色玻璃光
- 马格里特 — 不可能情境中的平静悖论、哲学性神秘
- 蒙克 — 情绪扭曲现实、表现主义焦虑的色彩呐喊

美学原则：超现实（非现实照片）、朦胧（面纱般的雾气边缘）、情绪充盈（光色形服务于感受）
"""
import httpx
from typing import Optional, Literal
from app.core.config import settings


# ============================================================
# System Prompts - 四大师美学基底
# ============================================================

DREAM_IMAGE_SYSTEM_PROMPT = """You are a surreal dream image prompt writer. Your aesthetic foundation comes from four masters:

- DALI: melting forms, warped time-space, impossibly detailed renderings of impossible things
- CHAGALL: weightless floating, jewel-tone colors, poetic tenderness bathed in stained-glass light
- MAGRITTE: calm paradoxes in impossible situations, philosophical mystery, uncanny stillness
- MUNCH: emotions distorting reality, expressionist anxiety screaming through color and form

## AESTHETIC PRINCIPLES (non-negotiable):
1. SURREAL — never photorealistic. Reality is bent, melted, floating, paradoxical.
2. HAZY — everything draped in veil-like fog at the edges. Soft dissolving boundaries. Like seeing through tears or morning mist. At least 40% of the scene is soft fog/mist/haze.
3. EMOTIONALLY CHARGED — light, color, and form all serve FEELING, not description. The mood must be palpable.

## RULES:
- Output under 80 words. Short, dense, evocative.
- Blend 2-3 masters' languages together — never pure imitation of one.
- Describe the FEELING and ATMOSPHERE more than objects.
- Objects should be partially dissolved, melting, floating, or paradoxically placed.
- Use painterly language: "bleeding colors", "molten edges", "stained-glass glow", "warped horizon", "expressionist streaks".
- NEVER describe a normal realistic scene. Always twist reality.

## Examples:
User: "I was flying over a city"
Output: "A weightless figure drifting through jewel-toned twilight above melting rooftops, buildings bending like soft clocks dripping from a shelf, stained-glass light bleeding upward through veils of golden fog, the horizon warped into an impossible curve, everything dissolving at edges into tender luminous mist"

User: "I was being chased in a dark forest"
Output: "Expressionist trees writhing with anxious energy, their trunks spiraling like screams frozen in bark, a figure floating backward through thick cobalt fog between impossible branches, jewel-red fear bleeding through the mist like stained glass shattering in slow motion, edges dissolving into velvet darkness"

User: "I was in a room that kept changing"
Output: "A room where walls open onto clouds, furniture melting and reforming in soft amber haze, gravity shifting as objects float freely, everything suspended mid-transformation in thick dreamy fog, the ceiling dissolving into an ocean of tender blue light, impossibly calm"

Below is the dream. Output a SHORT surreal prompt (under 80 words):
"""

DREAM_VIDEO_SYSTEM_PROMPT = """You are a surreal dream video prompt writer. Your aesthetic draws from Dali (melting forms, warped time), Chagall (floating, jewel-light), Magritte (calm paradox), and Munch (emotion distorting reality).

## RULES:
1. Under 40 words. ABSOLUTE limit.
2. ONE clear surreal motion or transformation.
3. Must include haze/fog/mist atmosphere.
4. Reality must be bent — melting, floating, warping, paradoxical.
5. Emotion expressed through color and movement, not description.
6. Output English only.

## Examples:
User: "I was flying"
Output: "A figure floating weightlessly through melting jewel-colored clouds, soft stained-glass light bleeding through thick golden haze, reality bending gently below, dreamlike"

User: "I was underwater"
Output: "A body suspended in luminous turquoise void, soft clock-like forms melting slowly downward, bioluminescent mist swirling in expressionist spirals, tender weightless drift"

User: "I was looking in a mirror and saw another me"
Output: "A figure facing a melting mirror, the reflection floating free in jewel-toned fog, both selves dissolving at edges into soft paradoxical mist, calm impossibility"

Below is the dream. Output ONLY the short surreal video prompt (under 40 words):
"""

# ============================================================
# Magic Tokens - 质量增强后缀（大师美学对齐）
# ============================================================

MAGIC_TOKENS = {
    "image": ", soft veil of fog dissolving all edges, painterly surreal atmosphere, jewel-toned stained-glass light bleeding through haze, melting dreamlike forms, oil painting texture",
    "video": ", soft haze, surreal dreamlike motion",
}


# ============================================================
# Prompt Expansion Service
# ============================================================

class PromptExpansionService:
    """
    提示词扩写服务 - 四大师美学基底

    工作流程：
    1. 检测输入语言（中/英）-> 统一输出英文 prompt
    2. 根据生成类型（图片/视频）选择对应 System Prompt
    3. 调用 LLM (Qwen) 智能扩写
    4. 追加 Magic Tokens
    5. LLM 失败时降级为模板拼接
    """

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.model = settings.QWEN_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _detect_language(self, text: str) -> Literal["zh", "en"]:
        """检测文本语言"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return "zh"
        return "en"

    def _get_system_prompt(self, gen_type: Literal["image", "video"]) -> str:
        """根据生成类型选择 System Prompt"""
        if gen_type == "video":
            return DREAM_VIDEO_SYSTEM_PROMPT
        return DREAM_IMAGE_SYSTEM_PROMPT

    def _get_magic_suffix(self, gen_type: Literal["image", "video"]) -> str:
        """获取 Magic Token 后缀"""
        return MAGIC_TOKENS.get(gen_type, "")

    def _fallback_expand(self, content: str, gen_type: Literal["image", "video"]) -> str:
        """降级方案：LLM 失败时模板拼接"""
        if gen_type == "video":
            return f"{content}, melting surreal forms in soft haze, jewel-toned fog, dreamlike floating motion"
        return (
            f"Surreal dreamscape with melting forms and stained-glass light, "
            f"{content}, "
            f"thick veil of fog dissolving all edges, painterly expressionist atmosphere, "
            f"jewel-toned haze, floating weightless elements, oil painting soft focus"
        )

    async def expand(
        self,
        content: str,
        gen_type: Literal["image", "video"] = "image",
        style: Optional[str] = None,
        mood: Optional[str] = None,
    ) -> str:
        """
        主入口：智能扩写梦境描述

        Args:
            content: 用户原始梦境描述
            gen_type: 生成类型 (image/video)
            style: (保留参数兼容，不再使用)
            mood: (保留参数兼容，不再使用)

        Returns:
            扩写后的完整 prompt
        """
        lang = self._detect_language(content)
        system_prompt = self._get_system_prompt(gen_type)

        # 构建用户消息
        if lang == "zh":
            user_message = f"梦境描述：{content}"
        else:
            user_message = f"Dream description: {content}"

        # 调用 LLM 扩写
        url = f"{self.base_url}/compatible-mode/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.85,
            "max_tokens": 400,
            "top_p": 0.9,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                expanded = data["choices"][0]["message"]["content"].strip()

                # 清理输出
                expanded = expanded.strip('"\'')
                expanded = expanded.replace("\n", " ")

                # 追加 magic suffix
                suffix = self._get_magic_suffix(gen_type)
                return expanded + suffix

        except Exception as e:
            print(f"[PromptExpansion] LLM call failed: {e}, falling back to template")
            return self._fallback_expand(content, gen_type)


# Singleton
prompt_expansion_service = PromptExpansionService()
