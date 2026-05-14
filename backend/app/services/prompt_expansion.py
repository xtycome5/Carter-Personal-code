"""
Prompt Expansion Service - 提示词扩写服务

以四位大师的艺术语言为基底，生成超现实梦境提示词：
- 达利 — 融化的形态、扭曲的时空、精细渲染的不可能之物
- 夏加尔 — 失重漂浮、宝石色调、诗意温柔的彩色玻璃光
- 马格里特 — 不可能情境中的平静悖论、哲学性神秘
- 蒙克 — 情绪扭曲现实、表现主义焦虑的色彩呐喊

美学原则：超现实（非现实照片）、朦胧（面纱般的雾气边缘）、情绪充盈（光色形服务于感受）

视频提示词策略：
用具体的摄影/电影语言替代空泛形容词，让 HappyHorse 模型呈现可控、可复现的画面。
"""
import logging
import httpx
from typing import Optional, Literal
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# IMAGE System Prompt - 四大师美学基底（保持不变）
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

# ============================================================
# VIDEO System Prompt - 专业摄影/电影语言指导 HappyHorse
# ============================================================

DREAM_VIDEO_SYSTEM_PROMPT = """You are a professional cinematography prompt engineer for the HappyHorse AI video generation model (Reference-to-Video mode).

IMPORTANT CONTEXT: The video will be generated FROM A REFERENCE IMAGE. The reference image is a surreal painting already generated from this same dream. Your prompt must COMPLEMENT that image, not contradict it.

## YOUR AESTHETIC FOUNDATION (four masters):
- DALI: melting/morphing forms, warped physics, impossible objects rendered in hyper-detail
- CHAGALL: weightless floating bodies, jewel-saturated hues (cobalt, emerald, amber), stained-glass luminosity
- MAGRITTE: paradoxical juxtapositions presented with photographic calm, uncanny stillness
- MUNCH: reality warped by raw emotion, expressionist color distortion, organic flowing forms

## MANDATORY CONSTRAINTS:

### 1. FPV (First-Person View) Camera — NON-NEGOTIABLE
- The camera IS the dreamer's eyes. We never see a human subject from outside.
- Use FPV language: "camera drifts forward as if walking through", "POV looking down at own hands", "first-person perspective floating above", "camera turns head slowly to reveal"
- This avoids gender/appearance issues entirely — viewer IS the dreamer.
- Allowed camera motions for FPV: slow drift forward, gentle head-turn pan, looking up/down tilt, floating rise/descent, smooth FPV walk-through

### 2. REUSE REFERENCE IMAGE ELEMENTS — NON-NEGOTIABLE
- The reference image contains specific surreal objects, colors, textures, and compositions.
- Your prompt must instruct the model to ANIMATE and EXTEND those same elements, not replace them.
- Use phrases like: "the existing scene elements begin to move", "objects from the composition drift and morph", "the painted forms come alive with subtle motion", "colors from the scene bleed and flow"
- DO NOT introduce new characters, new environments, or drastically different objects. EXTEND what's already in the image.
- Think of it as "the painting comes to life" from the dreamer's POV inside it.

### 3. PAINTERLY PRESERVATION
- The video should feel like BEING INSIDE the painting, not like a realistic 3D render.
- Maintain painted textures: "visible brushstroke texture on surfaces", "oil-paint sheen on moving forms", "watercolor bleed edges on motion trails"
- Keep the surreal/impossible physics from the reference: melting, floating, warping.

## CINEMATOGRAPHY LANGUAGE:

### Camera (FPV only):
- "FPV slow drift forward through the scene at 0.3m/s"
- "first-person gaze panning 45° left, revealing more of the painted landscape"
- "POV floating upward 2m, looking down as elements below shift and melt"
- "handheld FPV micro-drift with subtle breathing motion"
- "FPV walking into depth of the scene, parallax on foreground elements"

### Motion of Scene Elements:
- "foreground painted objects drift laterally at 0.1m/s"
- "liquid surfaces ripple outward from center every 2 seconds"
- "melting forms drip downward in slow motion, 120fps feel"
- "floating elements rotate slowly, 5° per second"
- "fog/haze layers shift in parallax — near fog fast, far fog slow"

### Lighting & Atmosphere:
- Inherit from the reference image's palette, then add subtle animation
- "existing light sources pulse gently, +/-10% intensity over 3s cycle"
- "volumetric rays through haze shift angle 5° over duration"
- "atmospheric haze drifts left-to-right at 0.2m/s, density 40%"
- "color temperature shifts warm-to-cool over the 10s take"

### Texture & Post:
- "maintain oil painting surface texture throughout — no photorealistic rendering"
- "motion trails have watercolor bleed quality"
- "soft pro-mist 1/4 filter, gentle halation on bright areas"
- "film grain 35mm, consistent throughout"

## OUTPUT STRUCTURE:
[FPV camera position + movement] → [How existing scene elements animate] → [Physics/motion specifics] → [Lighting animation] → [Atmosphere + haze] → [Texture preservation + color grade]

## CRITICAL RULES:
1. Output 80-120 words. Dense, precise, all technical.
2. ALWAYS FPV. Never describe a third-person character. The viewer IS inside the dream.
3. ALWAYS reference "existing scene elements" / "painted forms" / "the composition" — because a reference image exists.
4. NEVER introduce entirely new subjects not implied by the dream description.
5. Keep the painterly/surreal quality — this is an animated painting, not a 3D film.
6. ONE continuous 10-second take. No cuts.
7. English only.

## Examples:

User: "I was flying over a city"
Output: "FPV floating 50m above, slow drift forward at 0.5m/s. Below: the painted melting cityscape comes alive — Art Nouveau facades drip like warm wax, rooftops shift and breathe slowly. Parallax: near fog layer drifts right, distant buildings sway gently at 2°/s. POV tilts down 15° to see more of the scene. Existing jewel-toned stained-glass light sources pulse softly. Volumetric golden haze at 40% density drifts between towers. Color grade: warm 3200K highlights, cobalt shadows, shifting slightly cooler over 10s. Oil-paint texture preserved on all surfaces, brushstroke edges visible on motion trails. Pro-mist 1/4, anamorphic bloom on light points."

User: "我在水下呼吸"
Output: "FPV suspended in luminous turquoise water, gentle drift forward 0.2m/s. Existing painted elements animate: clock-faces with melting numerals sink slowly at 0.1m/s, bioluminescent forms pulse and rotate 3°/s. POV looks slowly upward — caustic light patterns from the surface ripple across the scene. Particles from the composition drift upward like reverse snow. Soft current pushes painted kelp forms in gentle sway, watercolor-bleed motion trails. Haze: underwater visibility 6m, soft cyan fog beyond. Lighting: single caustic source from above, cool 5500K, intensity pulsing +/-5%. Film grain, oil-paint sheen on water surface. Maintain the painting's surreal non-realistic quality throughout."

Below is the user's dream. Write a precise FPV video prompt for HappyHorse R2V:
"""

# ============================================================
# Magic Tokens - 质量增强后缀
# ============================================================

MAGIC_TOKENS = {
    "image": ", soft veil of fog dissolving all edges, painterly surreal atmosphere, jewel-toned stained-glass light bleeding through haze, melting dreamlike forms, oil painting texture",
    "video": "",  # 视频不再追加泛化后缀，prompt 本身已够专业
}


# ============================================================
# Prompt Expansion Service
# ============================================================

class PromptExpansionService:
    """
    提示词扩写服务 - 双轨策略

    图片：四大师美学 + 朦胧感（短 prompt）
    视频：专业摄影语言 + 精确技术描述（长 prompt，指导 HappyHorse 可控出片）

    工作流程：
    1. 检测输入语言（中/英）→ 统一输出英文 prompt
    2. 根据生成类型选择对应 System Prompt 和模型
    3. 调用 LLM 智能扩写
    4. 图片追加 Magic Tokens，视频不追加
    5. LLM 失败时降级为模板拼接
    """

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.image_model = settings.QWEN_MODEL
        self.video_model = settings.QWEN_VIDEO_PROMPT_MODEL
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

    def _get_model(self, gen_type: Literal["image", "video"]) -> str:
        """根据生成类型选择 LLM 模型"""
        if gen_type == "video":
            return self.video_model
        return self.image_model

    def _get_magic_suffix(self, gen_type: Literal["image", "video"]) -> str:
        """获取 Magic Token 后缀"""
        return MAGIC_TOKENS.get(gen_type, "")

    def _fallback_expand(self, content: str, gen_type: Literal["image", "video"]) -> str:
        """降级方案：LLM 失败时模板拼接"""
        if gen_type == "video":
            return (
                f"Wide shot, slow dolly forward. {content}. "
                f"Melting surreal forms with Dali-esque warped physics, objects floating with zero gravity. "
                f"Camera: smooth orbit, 50mm lens. Lighting: soft diffused overhead, warm 3200K key light. "
                f"Atmospheric haze 40% density, volumetric god rays. "
                f"Color grade: teal-amber split, pro-mist 1/4 filter, gentle film grain."
            )
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
        model = self._get_model(gen_type)

        # 构建用户消息
        if lang == "zh":
            user_message = f"梦境描述：{content}"
        else:
            user_message = f"Dream description: {content}"

        # 调用 LLM 扩写
        url = f"{self.base_url}/compatible-mode/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.75 if gen_type == "video" else 0.85,
            "max_tokens": 800 if gen_type == "video" else 400,
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

                # 追加 magic suffix（视频为空，不追加）
                suffix = self._get_magic_suffix(gen_type)
                result = expanded + suffix if suffix else expanded

                logger.info(f"[PromptExpansion] type={gen_type} | model={model} | len={len(result)} | prompt={result[:100]}...")
                return result

        except Exception as e:
            logger.error(f"[PromptExpansion] LLM call failed: {e}, falling back to template")
            return self._fallback_expand(content, gen_type)


# Singleton
prompt_expansion_service = PromptExpansionService()
