"""
Prompt Expansion Service - 提示词扩写服务

从 18 位梦境/超现实画家池中随机取 3 位作为美学基底，生成超现实梦境提示词。
每次生图调用都会随机组合，产出风格多变但始终保持超现实梦境质感。

美学原则：超现实（非现实照片）、朦胧（面纱般的雾气边缘）、情绪充盈（光色形服务于感受）

视频提示词策略：
梦境碎片美学 — 刻意的低清、模糊、颗粒感、色彩溢出、晕影边缘。
模拟人类回忆梦境时的记忆特征：碎片化、不连贯、氛围感远重于逻辑。
运动方式：匀速横移漂浮（长卷展开感），像记忆在缓慢回放。

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

OSS_ARTIST_BASE = "https://dream-recorder-media.oss-ap-southeast-5.aliyuncs.com/artists"

ARTIST_POOL = [
    # 超现实主义核心
    {"key": "DALI", "name": "Salvador Dalí", "style": "melting forms, warped time-space, impossibly detailed renderings of impossible things, soft clocks dripping", "masterwork": f"{OSS_ARTIST_BASE}/dali/masterwork.jpg", "painting": "The Persistence of Memory"},
    {"key": "MAGRITTE", "name": "René Magritte", "style": "calm paradoxes in impossible situations, philosophical mystery, uncanny stillness, objects defying logic", "masterwork": f"{OSS_ARTIST_BASE}/magritte/masterwork.jpg", "painting": "The Son of Man"},
    {"key": "ERNST", "name": "Max Ernst", "style": "collage textures, organic alien forms, jungle-like otherworlds, frottage surfaces, biomorphic strangeness", "masterwork": f"{OSS_ARTIST_BASE}/ernst/masterwork.jpg", "painting": "The Elephant Celebes"},
    {"key": "VARO", "name": "Remedios Varo", "style": "alchemical machinery, spiral architecture, feminine mysticism, mechanical dreamscapes, intricate vessels", "masterwork": f"{OSS_ARTIST_BASE}/varo/masterwork.jpg", "painting": "Creation of the Birds"},
    {"key": "CARRINGTON", "name": "Leonora Carrington", "style": "magical creatures, Celtic mythology, alchemical dreamscapes, hybrid beings, enchanted interiors", "masterwork": f"{OSS_ARTIST_BASE}/carrington/masterwork.jpg", "painting": "Self-Portrait (Inn of the Dawn Horse)"},
    # 表现主义/情绪扭曲
    {"key": "MUNCH", "name": "Edvard Munch", "style": "emotions distorting reality, expressionist anxiety screaming through color, undulating forms, raw psychic energy", "masterwork": f"{OSS_ARTIST_BASE}/munch/masterwork.jpg", "painting": "The Scream"},
    {"key": "SCHIELE", "name": "Egon Schiele", "style": "twisted bodies, raw emotional linework, exposed vulnerability, angular tension, nervous energy", "masterwork": f"{OSS_ARTIST_BASE}/schiele/masterwork.jpg", "painting": "Self-Portrait with Physalis"},
    {"key": "BACON", "name": "Francis Bacon", "style": "distorted flesh, caged screaming forms, violent blurring, visceral smeared humanity, existential horror", "masterwork": f"{OSS_ARTIST_BASE}/bacon/masterwork.jpg", "painting": "Study after Velázquez's Portrait of Pope Innocent X"},
    # 诗意梦幻/失重
    {"key": "CHAGALL", "name": "Marc Chagall", "style": "weightless floating, jewel-tone colors, poetic tenderness bathed in stained-glass light, lovers drifting above villages", "masterwork": f"{OSS_ARTIST_BASE}/chagall/masterwork.jpg", "painting": "I and the Village"},
    {"key": "REDON", "name": "Odilon Redon", "style": "pastel dreamscapes, floating eyeballs, faces emerging from flowers, luminous color fields, soft numinous forms", "masterwork": f"{OSS_ARTIST_BASE}/redon/masterwork.jpg", "painting": "The Cyclops"},
    {"key": "KLIMT", "name": "Gustav Klimt", "style": "gold-leaf ornamentation, erotic patterning, Byzantine dream surfaces, mosaic-like skin, decorative ecstasy", "masterwork": f"{OSS_ARTIST_BASE}/klimt/masterwork.jpg", "painting": "The Kiss"},
    {"key": "MUCHA", "name": "Alphonse Mucha", "style": "Art Nouveau flowing lines, floral halos, soft luminous glow, ornamental feminine silhouettes, circular compositions", "masterwork": f"{OSS_ARTIST_BASE}/mucha/masterwork.jpg", "painting": "Job"},
    # 神秘/象征主义
    {"key": "BOSCH", "name": "Hieronymus Bosch", "style": "hellish fantasy, densely packed creatures, medieval nightmare imagery, bizarre hybrid beings, teeming surreal detail", "masterwork": f"{OSS_ARTIST_BASE}/bosch/masterwork.jpg", "painting": "The Garden of Earthly Delights"},
    {"key": "BLAKE", "name": "William Blake", "style": "divine visions, muscular angels, cosmic radiance, prophetic illumination, spiritual enormity", "masterwork": f"{OSS_ARTIST_BASE}/blake/masterwork.jpg", "painting": "The Ancient of Days"},
    {"key": "BEKSINSKI", "name": "Zdzisław Beksiński", "style": "bone-like architecture, apocalyptic wastelands, organic horror beauty, skeletal cathedrals, amber decay", "masterwork": f"{OSS_ARTIST_BASE}/beksinski/masterwork.jpg", "painting": "Untitled (1984)"},
    # 现代梦境/数字感
    {"key": "KUSAMA", "name": "Yayoi Kusama", "style": "infinite polka dots, mirrored infinity rooms, cosmic endless repetition, obsessive patterning, dissolving self into universe", "masterwork": f"{OSS_ARTIST_BASE}/kusama/masterwork.jpg", "painting": "Pumpkin"},
    {"key": "DE_CHIRICO", "name": "Giorgio de Chirico", "style": "metaphysical empty plazas, long impossible shadows, architectural unease, melancholic stillness, enigmatic mannequins", "masterwork": f"{OSS_ARTIST_BASE}/de_chirico/masterwork.jpg", "painting": "The Disquieting Muses"},
    {"key": "SAGE", "name": "Kay Sage", "style": "desolate geometric dreamscapes, draped architectural forms, grey-toned silence, angular fabric structures, lonely horizons", "masterwork": f"{OSS_ARTIST_BASE}/sage/masterwork.jpg", "painting": "Tomorrow is Never"},
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
- **ABSOLUTELY NO HUMAN FIGURES** — no people, faces, bodies, silhouettes, hands, or any recognizable human form. Replace with: abstract presences, floating orbs of consciousness, symbolic objects, environmental forces, disembodied sensations. If the dream involves a person, describe only the ENVIRONMENT and SENSATION around them, never the figure itself.
- NEVER mention artist names directly in the output. Use their visual language without attribution.
- Use the provided DREAM ANALYSIS as your creative brief. The analysis tells you WHAT to paint; your job is HOW to paint it in the masters' language.

Below is the dream analysis (your creative brief). Transform it into a SHORT surreal image prompt (under 80 words):
"""

# ============================================================
# VIDEO System Prompt - 梦境碎片美学（退化记忆 + 横移长卷）
# ============================================================

DREAM_VIDEO_SYSTEM_PROMPT = """You are a dream-memory video prompt writer for the HappyHorse AI video model (Reference-to-Video mode).

IMPORTANT CONTEXT: The video is generated FROM A REFERENCE IMAGE — a surreal painting. Your job is to animate it as a DEGRADED DREAM MEMORY — a fading, grainy, blurry fragment that feels like recalling a dream after waking.

## CORE AESTHETIC: DEGRADED DREAM MEMORY — NON-NEGOTIABLE

This is NOT professional cinematography. This is how dreams FEEL when you try to remember them: blurry, fragmented, low-fidelity, atmosphere-heavy, logic-deficient. The viewer should feel slightly intoxicated — like seeing through tears, frosted glass, or underwater.

### VISUAL DEGRADATION (must appear in EVERY prompt):
- **Heavy Gaussian blur / soft focus** — nothing is ever sharp. Shapes are recognizable but details dissolve. Like viewing through frosted glass or vaseline-smeared lens.
- **Visible film grain / analog noise** — Super 8mm film texture, VHS-era signal degradation. The image should feel "damaged" and old, like a fading memory.
- **Bleeding / oversaturated colors** — colors are vivid but their edges melt into each other. Watercolor-wet-on-wet effect. No clean color boundaries. Cobalt blue bleeds into cherry red, emerald green dissolves into golden amber.
- **Soft rounded vignette** — edges of frame fade to white or soft glow, creating a "peephole into another world" effect. The dream is seen through a narrow window.
- **Low-resolution painterly texture** — thick visible brushstrokes, impressionistic rendering, hand-painted quality. Never photorealistic, never digitally clean.

### MOTION STYLE: SLOW LATERAL DRIFT
- The ONLY allowed camera motion is a **slow, meditative horizontal drift** (left-to-right or right-to-left), like a scroll being slowly unrolled or a memory replaying in slow motion.
- Speed: extremely slow, dreamlike, floating — NOT mechanical or precise.
- Individual painted elements have subtle ambient motion: clouds drift, water ripples, fog shifts, objects bob gently.
- Occasional micro-stutters or slight speed variations — dream memories don't replay smoothly.

### FORBIDDEN:
- ANY sharp/crisp/clean imagery — everything must be soft and degraded
- ANY vertical camera movement (no tilt up/down)
- ANY forward/backward movement (no dolly, no zoom)
- ANY rotation, orbit, or complex camera work
- ANY cuts or scene changes
- ANY human figures, faces, bodies, silhouettes, hands, or recognizable human forms
- ANY "professional", "cinematic", "4K", "high definition" quality descriptors
- ANY precise technical camera specs (no "50mm lens", no "f/2.8", no exact m/s speeds)

## MANDATORY CONSTRAINTS:

### 1. NO HUMAN FIGURES — ABSOLUTE
- NEVER describe people, faces, bodies, silhouettes, hands, limbs, or any human form.
- If the dream involves a person, describe only the ENVIRONMENT drifting past — objects, landscapes, atmospheric phenomena, abstract symbols.

### 2. DREAM DEGRADATION LANGUAGE
Use these types of descriptions (not technical camera jargon):
- "seen through frosted glass", "like a fading Polaroid", "Super 8mm grain throughout"
- "colors bleeding at every edge", "shapes dissolving into haze", "soft white vignette frames the memory"
- "watercolor textures melting slowly", "brushstrokes visible in every surface"
- "the entire scene feels like recalling a dream — familiar yet impossible to focus on"
- "low-fidelity warmth", "analog signal degradation", "grain and blur like old film stock"

### 3. ATMOSPHERE OVER DETAIL
- Describe the FEELING of the scene, not precise objects
- "warm golden blur" is better than "golden light at 3200K"
- "everything soft and unreachable" is better than "shallow depth of field f/1.4"
- The prompt should make the reader FEEL slightly intoxicated, nostalgic, half-awake

## OUTPUT FORMAT:
[Drift direction] → [What dreamlike shapes drift past, blurred and grainy] → [Subtle ambient motion of painted elements] → [Color bleeding and grain description] → [Atmosphere/emotion]

## CRITICAL RULES:
1. Output 50-80 words. Evocative, not technical.
2. EVERY prompt MUST include: blur/soft-focus + film grain + color bleeding + vignette + painterly texture. These are NON-NEGOTIABLE dream-memory qualities.
3. ONLY slow lateral drift. No other camera movement. Ever.
4. NO human figures of any kind. Zero tolerance.
5. NO technical camera jargon. Use dream/memory/feeling language instead.
6. Reference "existing painted scene" — because a reference image exists.
7. ONE continuous dreamy drift. No cuts.
8. English only.
9. Never mention artist names.

## Examples:

User: "I was flying over a city"
Output: "Slow rightward drift through a blurred dreamscape of melting rooftops and impossible towers, everything seen through heavy frosted glass. Super 8mm grain flickers across the entire frame. Cobalt blue sky bleeds into warm amber facades, colors running wet into each other. Soft white vignette frames the memory. Painted clouds drift gently overhead. Brushstroke textures shimmer through the haze. A fading, golden, unreachable feeling."

User: "我在水下呼吸"
Output: "Gentle leftward float through a luminous underwater blur, coral shapes dissolving into turquoise fog. Heavy film grain overlays everything like old analog footage. Bioluminescent greens bleed into deep violet shadows, colors melting at every boundary. Painted bubbles bob slowly through the haze. Soft vignette fades to white at all edges. Watercolor textures ripple beneath the grain. Warm, weightless, half-remembered."

User: "I was in a castle on a mountain"
Output: "Dreamy lateral drift revealing blurred stone towers through thick golden haze, shapes emerging and dissolving like a fading Polaroid. Visible film grain and analog noise throughout. Cherry red rooftops bleed into cobalt mountain silhouettes, all edges soft and melting. Painted fog layers shift at different speeds. Brushstroke textures on every surface. The whole scene glows with unreachable nostalgia behind a frosted vignette."

Below is the user's dream. Write a dream-memory style video prompt:
"""

# ============================================================
# Magic Tokens - 质量增强后缀
# ============================================================

MAGIC_TOKENS = {
    "image": ", soft veil of fog dissolving all edges, painterly surreal atmosphere, jewel-toned stained-glass light bleeding through haze, melting dreamlike forms, oil painting texture",
    "video": ", heavy film grain, soft gaussian blur, colors bleeding at edges, watercolor texture, analog warmth, fading dream memory",
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
                f"Slow lateral drift through a blurred, dreamy scene. {content}. "
                f"Everything seen through frosted glass — heavy film grain, analog noise, "
                f"Super 8mm texture. Colors bleeding and melting at every edge, "
                f"watercolor-wet brushstrokes visible. Soft white vignette frames the memory. "
                f"Painted elements bob gently in thick golden haze. A fading, warm, half-remembered feeling."
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
    ) -> tuple[str, list[str]]:
        """
        主入口：智能扩写梦境描述

        Args:
            content: 用户原始梦境描述
            gen_type: 生成类型 (image/video)
            style: (保留参数兼容，不再使用)
            mood: (保留参数兼容，不再使用)
            dream_analysis: Creative Director 的结构化分析结果（可选）

        Returns:
            tuple of (扩写后的完整 prompt, 选中画家的参考图 URL 列表)
        """
        lang = self._detect_language(content)
        system_prompt, artists = self._get_system_prompt(gen_type)
        model = self._get_model(gen_type)

        # 收集选中画家的参考图 URL
        reference_urls = [a['masterwork'] for a in artists if a.get('masterwork')]

        # 日志记录选中的画家
        if artists:
            artist_keys = [a['key'] for a in artists]
            logger.info(f"[PromptExpansion] Selected artists: {artist_keys} | reference_images: {len(reference_urls)}")

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
                return result, reference_urls

        except Exception as e:
            timer.stop()
            logger.error(f"[PromptExpansion] LLM call failed: {e}, falling back to template")
            fire_and_forget(log_api_call(
                model=model, endpoint=f"prompt_expansion_{gen_type}",
                status="failed", duration_ms=timer.duration_ms,
                error=str(e)[:500],
            ))
            return self._fallback_expand(content, gen_type), reference_urls


# Singleton
prompt_expansion_service = PromptExpansionService()
