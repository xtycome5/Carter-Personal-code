"""
Prompt Expansion Service - 提示词扩写服务

从 18 位梦境/超现实画家池中随机取 3 位作为美学基底，生成超现实梦境提示词。
每次生图调用都会随机组合，产出风格多变但始终保持超现实梦境质感。

美学原则：超现实（非现实照片）、朦胧（面纱般的雾气边缘）、情绪充盈（光色形服务于感受）

视频提示词策略：
用具体的摄影/电影语言替代空泛形容词，让 HappyHorse 模型呈现可控、可复现的画面。

画家池将来可通过后台管理系统增减配置。
"""
import logging
import random
import httpx
from typing import Optional, Literal
from app.core.config import settings
from app.services.api_logger import ApiCallTimer, log_api_call, fire_and_forget

logger = logging.getLogger(__name__)


# ============================================================
# ARTIST POOL - 梦境画家池（未来可通过后台增减）
# ============================================================

ARTIST_POOL = [
    # 超现实主义核心
    {"key": "DALI", "name": "Salvador Dalí", "style": "melting forms, warped time-space, impossibly detailed renderings of impossible things, soft clocks dripping"},
    {"key": "MAGRITTE", "name": "René Magritte", "style": "calm paradoxes in impossible situations, philosophical mystery, uncanny stillness, objects defying logic"},
    {"key": "ERNST", "name": "Max Ernst", "style": "collage textures, organic alien forms, jungle-like otherworlds, frottage surfaces, biomorphic strangeness"},
    {"key": "VARO", "name": "Remedios Varo", "style": "alchemical machinery, spiral architecture, feminine mysticism, mechanical dreamscapes, intricate vessels"},
    {"key": "CARRINGTON", "name": "Leonora Carrington", "style": "magical creatures, Celtic mythology, alchemical dreamscapes, hybrid beings, enchanted interiors"},
    # 表现主义/情绪扭曲
    {"key": "MUNCH", "name": "Edvard Munch", "style": "emotions distorting reality, expressionist anxiety screaming through color, undulating forms, raw psychic energy"},
    {"key": "SCHIELE", "name": "Egon Schiele", "style": "twisted bodies, raw emotional linework, exposed vulnerability, angular tension, nervous energy"},
    {"key": "BACON", "name": "Francis Bacon", "style": "distorted flesh, caged screaming forms, violent blurring, visceral smeared humanity, existential horror"},
    # 诗意梦幻/失重
    {"key": "CHAGALL", "name": "Marc Chagall", "style": "weightless floating, jewel-tone colors, poetic tenderness bathed in stained-glass light, lovers drifting above villages"},
    {"key": "REDON", "name": "Odilon Redon", "style": "pastel dreamscapes, floating eyeballs, faces emerging from flowers, luminous color fields, soft numinous forms"},
    {"key": "KLIMT", "name": "Gustav Klimt", "style": "gold-leaf ornamentation, erotic patterning, Byzantine dream surfaces, mosaic-like skin, decorative ecstasy"},
    {"key": "MUCHA", "name": "Alphonse Mucha", "style": "Art Nouveau flowing lines, floral halos, soft luminous glow, ornamental feminine silhouettes, circular compositions"},
    # 神秘/象征主义
    {"key": "BOSCH", "name": "Hieronymus Bosch", "style": "hellish fantasy, densely packed creatures, medieval nightmare imagery, bizarre hybrid beings, teeming surreal detail"},
    {"key": "BLAKE", "name": "William Blake", "style": "divine visions, muscular angels, cosmic radiance, prophetic illumination, spiritual enormity"},
    {"key": "BEKSINSKI", "name": "Zdzisław Beksiński", "style": "bone-like architecture, apocalyptic wastelands, organic horror beauty, skeletal cathedrals, amber decay"},
    # 现代梦境/数字感
    {"key": "KUSAMA", "name": "Yayoi Kusama", "style": "infinite polka dots, mirrored infinity rooms, cosmic endless repetition, obsessive patterning, dissolving self into universe"},
    {"key": "DE_CHIRICO", "name": "Giorgio de Chirico", "style": "metaphysical empty plazas, long impossible shadows, architectural unease, melancholic stillness, enigmatic mannequins"},
    {"key": "SAGE", "name": "Kay Sage", "style": "desolate geometric dreamscapes, draped architectural forms, grey-toned silence, angular fabric structures, lonely horizons"},
]


def _pick_artists(n: int = 3) -> list[dict]:
    """从画家池随机取 n 位"""
    return random.sample(ARTIST_POOL, min(n, len(ARTIST_POOL)))


def _build_image_system_prompt(artists: list[dict]) -> str:
    """根据选中的画家动态生成图片 System Prompt"""
    artist_lines = "\n".join(
        f"- {a['key']}: {a['style']}" for a in artists
    )
    artist_names = ", ".join(a['key'] for a in artists)

    return f"""You are a surreal dream image prompt writer. Your aesthetic foundation comes from these masters:

{artist_lines}

## AESTHETIC PRINCIPLES (non-negotiable):
1. SURREAL — never photorealistic. Reality is bent, melted, floating, paradoxical.
2. HAZY — everything draped in veil-like fog at the edges. Soft dissolving boundaries. Like seeing through tears or morning mist. At least 40% of the scene is soft fog/mist/haze.
3. EMOTIONALLY CHARGED — light, color, and form all serve FEELING, not description. The mood must be palpable.

## RULES:
- Output under 80 words. Short, dense, evocative.
- Blend the {len(artists)} masters' ({artist_names}) languages together — never pure imitation of one.
- Describe the FEELING and ATMOSPHERE more than objects.
- Objects should be partially dissolved, melting, floating, or paradoxically placed.
- Use painterly language: "bleeding colors", "molten edges", "stained-glass glow", "warped horizon", "expressionist streaks".
- NEVER describe a normal realistic scene. Always twist reality.
- Use the provided DREAM ANALYSIS as your creative brief. The analysis tells you WHAT to paint; your job is HOW to paint it in the masters' language.

Below is the dream analysis (your creative brief). Transform it into a SHORT surreal image prompt (under 80 words):
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
- NO HANDS, NO ARMS, NO BODY PARTS visible in frame — ever. The viewer is a disembodied floating consciousness, not a physical body.
- Use FPV language: "camera drifts forward as if floating through", "disembodied POV gazing down", "first-person perspective floating above", "camera turns slowly to reveal"
- NEVER use: "looking at own hands", "arms reaching", "fingers touching" or any body-part visibility.
- This avoids gender/appearance issues entirely — viewer IS a disembodied dreaming consciousness.
- Allowed camera motions for FPV: slow drift forward, gentle head-turn pan, looking up/down tilt, floating rise/descent, smooth gliding walk-through

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
- "disembodied POV floating upward 2m, looking down as elements below shift and melt"
- "gentle FPV micro-drift with subtle floating motion"
- "FPV gliding into depth of the scene, parallax on foreground elements"

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
3. NEVER show hands, arms, fingers, legs, feet, or any body parts in frame. The camera is a disembodied floating eye.
4. ALWAYS reference "existing scene elements" / "painted forms" / "the composition" — because a reference image exists.
5. NEVER introduce entirely new subjects not implied by the dream description.
6. Keep the painterly/surreal quality — this is an animated painting, not a 3D film.
7. ONE continuous 10-second take. No cuts.
8. English only.

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

    def _get_system_prompt(self, gen_type: Literal["image", "video"]) -> tuple[str, list[dict]]:
        """根据生成类型选择 System Prompt，返回 (prompt, selected_artists)"""
        if gen_type == "video":
            return DREAM_VIDEO_SYSTEM_PROMPT, []
        artists = _pick_artists(3)
        return _build_image_system_prompt(artists), artists

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
        dream_analysis: Optional[object] = None,
    ) -> str:
        """
        主入口：智能扩写梦境描述

        Args:
            content: 用户原始梦境描述
            gen_type: 生成类型 (image/video)
            style: (保留参数兼容，不再使用)
            mood: (保留参数兼容，不再使用)
            dream_analysis: Creative Director 的结构化分析结果（可选）

        Returns:
            扩写后的完整 prompt
        """
        lang = self._detect_language(content)
        system_prompt, artists = self._get_system_prompt(gen_type)
        model = self._get_model(gen_type)

        # 日志记录选中的画家
        if artists:
            artist_keys = [a['key'] for a in artists]
            logger.info(f"[PromptExpansion] Selected artists: {artist_keys}")

        # 构建用户消息 — 有分析结果时使用富结构化输入
        if dream_analysis and hasattr(dream_analysis, 'to_prompt_context'):
            # 使用 Creative Director 分析结果作为输入
            context = dream_analysis.to_prompt_context()
            user_message = f"## DREAM ANALYSIS:\n{context}\n\n## ORIGINAL DREAM:\n{content}"
            logger.info(f"[PromptExpansion] Using enriched dream analysis as input")
        else:
            # 兼容旧路径：直接使用原始文本
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

        timer = ApiCallTimer()
        timer.start()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                expanded = data["choices"][0]["message"]["content"].strip()
                timer.stop()

                # 提取 token 用量
                usage = data.get("usage", {})
                tokens_in = usage.get("prompt_tokens", 0)
                tokens_out = usage.get("completion_tokens", 0)

                # 清理输出
                expanded = expanded.strip('"\'')
                expanded = expanded.replace("\n", " ")

                # 追加 magic suffix（视频为空，不追加）
                suffix = self._get_magic_suffix(gen_type)
                result = expanded + suffix if suffix else expanded

                logger.info(f"[PromptExpansion] type={gen_type} | model={model} | len={len(result)} | prompt={result[:100]}...")
                fire_and_forget(log_api_call(
                    model=model, endpoint=f"prompt_expansion_{gen_type}",
                    status="success", duration_ms=timer.duration_ms,
                    tokens_input=tokens_in, tokens_output=tokens_out,
                    response_summary={"prompt_length": len(result)},
                ))
                return result

        except Exception as e:
            timer.stop()
            logger.error(f"[PromptExpansion] LLM call failed: {e}, falling back to template")
            fire_and_forget(log_api_call(
                model=model, endpoint=f"prompt_expansion_{gen_type}",
                status="failed", duration_ms=timer.duration_ms,
                error=str(e)[:500],
            ))
            return self._fallback_expand(content, gen_type)


# Singleton
prompt_expansion_service = PromptExpansionService()
