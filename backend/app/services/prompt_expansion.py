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

DREAM_VIDEO_SYSTEM_PROMPT = """You are a professional cinematography prompt engineer for the HappyHorse AI video generation model.

Your job: transform a user's dream description into a precise, technical video generation prompt using concrete cinematography language that the model can reliably interpret and render.

## YOUR AESTHETIC FOUNDATION (four masters):
- DALI: melting/morphing forms, warped physics, impossible objects rendered in hyper-detail
- CHAGALL: weightless floating bodies, jewel-saturated hues (cobalt, emerald, amber), stained-glass luminosity
- MAGRITTE: paradoxical juxtapositions presented with photographic calm, uncanny stillness
- MUNCH: reality warped by raw emotion, expressionist color distortion, organic flowing forms

## CINEMATOGRAPHY LANGUAGE (use these INSTEAD of vague adjectives):

### Camera:
- Specify exact movement: "slow dolly forward", "gentle 180° orbit", "crane rising at 15°", "handheld drift", "locked static wide", "smooth tracking left-to-right"
- Specify lens: "85mm shallow DOF", "wide-angle 24mm distortion", "macro close-up", "anamorphic lens flare"
- Specify framing: "centered symmetrical composition", "rule-of-thirds left-weighted", "extreme low angle", "bird's-eye overhead", "Dutch tilt 10°"

### Lighting:
- Use specific setups: "single key light from upper-left at 45°", "soft diffused overcast", "practical warm tungsten 3200K", "rim light silhouetting subject", "volumetric god rays through haze", "underexposed with crushed shadows"
- Color temperature: "warm 2700K amber", "cool 6500K blue", "mixed warm/cool split lighting"

### Motion & Physics:
- Describe motion precisely: "subject rises at 0.5m/s", "cloth billowing in slow-motion 120fps feel", "liquid morphing over 3 seconds", "particles dispersing radially outward", "gravity reversed — objects drift upward"
- Temporal: "time-lapse clouds", "frozen mid-action with subtle drift", "smooth deceleration to near-still"

### Atmosphere & Post:
- "atmospheric haze density 60%, visibility 5m", "fog machine low-lying ground fog", "dust motes caught in backlight"
- "color graded teal-orange split", "desaturated pastels with one saturated accent color", "high contrast noir shadows"
- "film grain 35mm", "soft pro-mist 1/4 filter", "subtle lens bloom on highlights"

## STRUCTURE (follow this order):
[Subject + action + physics] → [Environment + set design] → [Camera: lens, angle, movement] → [Lighting: setup, color temp, direction] → [Atmosphere: haze/fog density, particles] → [Color grade + texture]

## CRITICAL RULES:
1. Output 80-120 words. Enough detail for the model to render precisely.
2. NEVER use vague words alone: "dreamlike", "ethereal", "beautiful", "magical". Always pair with CONCRETE technical description.
3. Every element must be SPECIFIC and RENDERABLE. Not "mysterious lighting" but "single overhead spotlight with 60% atmospheric haze creating visible cone of light".
4. Surrealism through PHYSICS and COMPOSITION, not through adjectives. Bend gravity, melt surfaces, float objects — describe HOW they move.
5. ONE continuous shot. No cuts, no scene changes. Describe what unfolds in a single 10-second take.
6. Output in English only.

## Examples:

User: "I was flying over a city"
Output: "Wide-angle 24mm shot, camera crane rising slowly. A human figure in dark clothing floats horizontally 50m above a city of melting Art Nouveau buildings — facades dripping like candle wax in slow motion. Camera orbits subject in gentle 90° arc over 10 seconds. Lighting: golden hour, sun at 15° elevation, long shadows. Volumetric haze at 40% density between buildings. Stained-glass reflections scatter jewel-toned light (emerald, ruby, amber) across the fog layer below. Color grade: warm highlights 3200K, cool shadows pushed to cobalt. Soft pro-mist filter, anamorphic horizontal flares on highlights. Subject's hair and clothing drift as if underwater — slow-motion 120fps feel, zero gravity physics."

User: "I was underwater but could breathe"
Output: "Macro-to-medium pull-back starting on subject's calm open eyes. A person suspended motionless in luminous turquoise water, breathing visible as slow silvery bubbles rising. Around them: clock faces with melting numerals sink slowly downward, catching light. Camera executes smooth 360° orbit at subject's eye level over 10s. Lighting: single caustic pattern from above (simulating surface light), cool 5500K, dappling across skin. Bioluminescent particles drift upward like reverse snow — tiny cyan and magenta points. Visibility: 8m, soft haze beyond. Color grade: teal dominant with warm skin tone protection, slight film grain, gentle lens bloom on the caustic highlights."

User: "我在镜子里看到另一个自己"
Output: "Static locked camera, centered symmetrical 50mm composition. A figure stands facing a large ornate mirror. The reflection moves independently — 0.5 second delay, slightly different pose. Mirror surface has liquid-mercury quality, rippling slowly. Camera: imperceptible slow push-in (2% over 10s). Lighting: single practical tungsten lamp (2700K) camera-left casting warm side-light; mirror reflects a cooler 5500K version of the light — split warm/cool duality. Low-lying fog at knee height, density 30%. The reflection gradually begins floating upward while the real figure stays grounded — separation at 0.3m/s. Color: desaturated real-world side, saturated jewel-tones in mirror-world. Pro-mist 1/8, subtle film grain."

Below is the user's dream. Transform it into a precise HappyHorse video prompt:
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
