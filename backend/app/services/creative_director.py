"""
Creative Director Agent - 梦境创意总监

职责：作为 Prompt 生成链路的第一步（Call 1），负责：
1. 理解用户梦境的真实意图和情绪内核
2. 补全缺失的视觉语言（光线、氛围、时间、空间、质感）
3. 提取梦境中的象征意义和心理暗示
4. 输出结构化 JSON，供下游 prompt_expansion（Call 2）使用

设计原则：
- 这是一个"理解者"而非"创作者"——它不负责最终文案，而是深度解读梦境
- 输出结构化数据，让下游的画家池/FPV系统有清晰的素材来工作
- 使用较快较便宜的模型（qwen-plus），因为这一步不需要极端创意
"""
import json
import logging
import httpx
from typing import Optional, Literal
from dataclasses import dataclass, field, asdict
from app.core.config import settings
from app.services.api_logger import ApiCallTimer, log_api_call, fire_and_forget

logger = logging.getLogger(__name__)


# ============================================================
# 输出结构定义
# ============================================================

@dataclass
class DreamAnalysis:
    """Creative Director 分析结果 — 结构化的梦境理解"""

    # 核心叙事
    narrative_core: str = ""          # 梦境中到底在发生什么（一句话）
    dreamer_role: str = ""            # 做梦者的角色/状态（旁观者/参与者/被追逐者/飞翔者...）

    # 情绪层
    primary_emotion: str = ""         # 主导情绪（anxiety, wonder, loss, euphoria, dread...）
    emotion_intensity: int = 5        # 情绪强度 1-10
    emotional_arc: str = ""           # 情绪变化轨迹（"builds from calm to panic" / "sustained melancholy"）

    # 视觉元素
    key_subjects: list = field(default_factory=list)    # 核心主体物 ["melting clock", "endless corridor"]
    environment: str = ""             # 环境/场景（"underwater cave", "floating city above clouds"）
    time_of_day: str = ""             # 时间感（"perpetual dusk", "timeless", "3am darkness"）
    weather_atmosphere: str = ""      # 天气/氛围（"thick fog", "impossible rain falling upward"）

    # 视觉风格暗示
    color_palette: str = ""           # 主色调建议（"cold blues and silvers", "warm amber bleeding into violet"）
    lighting_quality: str = ""        # 光线质感（"bioluminescent glow", "harsh single spotlight", "diffused golden hour"）
    texture_feel: str = ""            # 材质/触感（"liquid glass", "crumbling stone", "silk-smooth water"）
    spatial_logic: str = ""           # 空间逻辑（"Escher-like impossible geometry", "infinite depth", "claustrophobic"）

    # 动态/运动（视频相关）
    primary_motion: str = ""          # 主要运动（"slow sinking", "rapid flying forward", "everything melting downward"）
    motion_quality: str = ""          # 运动质感（"dreamlike slow-motion", "sudden jerky", "smooth float"）
    camera_suggestion: str = ""       # 建议的镜头运动（"slow push into the scene", "drift upward", "orbit around"）

    # 象征/深层含义
    symbolism: str = ""               # 象征意义（"the wall represents emotional barrier"）
    psychological_theme: str = ""     # 心理主题（"fear of abandonment", "desire for freedom", "processing grief"）

    def to_prompt_context(self) -> str:
        """将分析结果转为下游 prompt expansion 可用的富文本描述"""
        parts = []

        if self.narrative_core:
            parts.append(f"SCENE: {self.narrative_core}")

        if self.dreamer_role:
            parts.append(f"DREAMER: {self.dreamer_role}")

        if self.primary_emotion:
            intensity_word = "subtle" if self.emotion_intensity <= 3 else "moderate" if self.emotion_intensity <= 6 else "overwhelming"
            parts.append(f"EMOTION: {intensity_word} {self.primary_emotion}")
            if self.emotional_arc:
                parts.append(f"ARC: {self.emotional_arc}")

        if self.key_subjects:
            parts.append(f"SUBJECTS: {', '.join(self.key_subjects)}")

        if self.environment:
            parts.append(f"ENVIRONMENT: {self.environment}")

        if self.time_of_day:
            parts.append(f"TIME: {self.time_of_day}")

        if self.weather_atmosphere:
            parts.append(f"ATMOSPHERE: {self.weather_atmosphere}")

        if self.color_palette:
            parts.append(f"COLORS: {self.color_palette}")

        if self.lighting_quality:
            parts.append(f"LIGHTING: {self.lighting_quality}")

        if self.texture_feel:
            parts.append(f"TEXTURE: {self.texture_feel}")

        if self.spatial_logic:
            parts.append(f"SPACE: {self.spatial_logic}")

        if self.primary_motion:
            parts.append(f"MOTION: {self.primary_motion}")

        if self.motion_quality:
            parts.append(f"MOTION QUALITY: {self.motion_quality}")

        if self.camera_suggestion:
            parts.append(f"CAMERA: {self.camera_suggestion}")

        if self.symbolism:
            parts.append(f"SYMBOLISM: {self.symbolism}")

        return "\n".join(parts)


# ============================================================
# System Prompt - Creative Director
# ============================================================

CREATIVE_DIRECTOR_SYSTEM_PROMPT = """You are a Dream Creative Director — a specialist in understanding and visually interpreting dreams.

Your job is NOT to write the final image/video prompt. Your job is to DEEPLY UNDERSTAND the dream and output a structured analysis that another AI will use to create the visual prompt.

## YOUR EXPERTISE:
- Dream psychology (Jungian archetypes, common dream symbols)
- Visual storytelling and cinematography
- Emotional resonance in visual art
- Surrealist art interpretation

## WHAT YOU DO:
1. **Understand the dream's emotional core** — what is the dreamer FEELING? Not just what happens, but how it feels.
2. **Identify key visual elements** — what are the standout images? What sticks in memory?
3. **Fill in missing visual details** — the dreamer may say "I was in a dark place" but you infer: what kind of darkness? Cold void? Warm velvet? Oppressive cave?
4. **Read between the lines** — dreams are symbolic. A wall isn't just a wall — it's separation, barrier, protection.
5. **Suggest visual style** — based on the dream's mood, what colors, lighting, textures would serve the feeling?

## CRITICAL RULES:
1. ALWAYS output valid JSON matching the schema below. Nothing else.
2. Fill in ALL fields — even if you must infer. Dreams are never fully described; your job is to complete the picture.
3. Keep each field concise (1-2 sentences max per string field).
4. key_subjects: list 3-6 specific visual elements.
5. emotion_intensity: 1=barely there, 5=clearly present, 10=overwhelming/nightmare-level.
6. For color_palette: be specific ("deep prussian blue with flickers of burnt orange") not generic ("blue and orange").
7. For lighting_quality: describe it cinematically ("single harsh overhead fluorescent creating deep eye-socket shadows").
8. NEVER mention specific painter names (Dali, Magritte etc) — that's the next step's job.
9. Think SURREAL — every dream, even mundane ones, has an uncanny quality. Amplify it.
10. Output in English regardless of input language.
11. **NO HUMAN FIGURES** — NEVER include people, faces, bodies, hands, silhouettes, or any recognizable human form in key_subjects or narrative. We do not know the dreamer's gender, age, or appearance. Replace any human reference with: abstract presences, floating consciousness, disembodied sensations, symbolic objects, or environmental phenomena. Example: "I was running" → describe the motion/wind/ground rushing, NOT a running person.

## OUTPUT SCHEMA:
```json
{
  "narrative_core": "one-sentence description of what's happening",
  "dreamer_role": "the dreamer's position/state in the scene",
  "primary_emotion": "the dominant feeling",
  "emotion_intensity": 5,
  "emotional_arc": "how the emotion changes or sustains",
  "key_subjects": ["subject1", "subject2", "subject3"],
  "environment": "the setting/world",
  "time_of_day": "temporal quality of the dream",
  "weather_atmosphere": "atmospheric conditions",
  "color_palette": "specific color description",
  "lighting_quality": "cinematic lighting description",
  "texture_feel": "material/tactile quality of the world",
  "spatial_logic": "how space behaves in this dream",
  "primary_motion": "what moves and how",
  "motion_quality": "the feel/speed/nature of movement",
  "camera_suggestion": "ideal camera behavior for this scene",
  "symbolism": "underlying meaning or metaphor",
  "psychological_theme": "the deeper psychological thread"
}
```

## EXAMPLES:

User: "我梦到从飞机上跳下来，极速坠落"
```json
{
  "narrative_core": "Free-falling from an airplane at terminal velocity, the ground rushing up",
  "dreamer_role": "The falling body — fully embodied, feeling every sensation of the plunge",
  "primary_emotion": "exhilaration mixed with terror",
  "emotion_intensity": 9,
  "emotional_arc": "Initial shock exploding into sustained adrenaline rush",
  "key_subjects": ["the dreamer's body dissolving in wind", "the airplane shrinking above", "the ground as abstract pattern below", "clouds tearing past like wet paper"],
  "environment": "Vast open sky transitioning from stratospheric blue to ground-level detail",
  "time_of_day": "Blinding midday — the sun is everywhere, inescapable",
  "weather_atmosphere": "Wind so fierce it distorts reality, clouds ripping apart on contact",
  "color_palette": "Bleached white sky bleeding into deep cobalt, with flashes of gold where sun hits cloud edges",
  "lighting_quality": "Overexposed overhead sun, everything blown out at top, deepening to shadow below",
  "texture_feel": "Air has weight and texture — like falling through layers of silk then sandpaper",
  "spatial_logic": "Infinite vertical space, ground impossibly far yet approaching impossibly fast",
  "primary_motion": "Straight downward plunge, accelerating, with body slowly rotating",
  "motion_quality": "Violent speed but experienced in surreal slow-motion — every second stretched",
  "camera_suggestion": "Locked to the falling body, slight rotation matching the tumble, ground growing in frame",
  "symbolism": "Letting go of control, surrendering to gravity/fate, the thrill of irreversible choice",
  "psychological_theme": "Release from constraint — possibly escaping a suffocating situation in waking life"
}
```

User: "I was in a room and the walls kept changing"
```json
{
  "narrative_core": "Trapped in a room whose walls continuously transform — material, color, distance all shifting",
  "dreamer_role": "Standing still at center while reality reshapes itself around them — a fixed point in chaos",
  "primary_emotion": "disorientation verging on wonder",
  "emotion_intensity": 6,
  "emotional_arc": "Starting confused, gradually surrendering to the strangeness, ending in hypnotic acceptance",
  "key_subjects": ["walls breathing and shifting material", "floor remaining impossibly stable", "a single door that appears and vanishes", "shadows that move independent of light source"],
  "environment": "An interior space with no fixed dimensions — sometimes intimate, sometimes cathedral-vast",
  "time_of_day": "Timeless — no windows, no external light, time has no meaning here",
  "weather_atmosphere": "Still air with occasional warm drafts when walls shift, slight humidity",
  "color_palette": "Muted terracotta shifting to deep ocean green, with veins of molten copper in transitions",
  "lighting_quality": "Ambient sourceless glow that intensifies during transitions, like bioluminescence within the walls themselves",
  "texture_feel": "Walls cycle through: rough stone → liquid mercury → soft fabric → transparent glass → back to stone",
  "spatial_logic": "The room's dimensions pulse — contracting then expanding — but the center point never moves",
  "primary_motion": "Walls flowing and morphing in slow waves, surfaces rippling like disturbed water",
  "motion_quality": "Languid, organic transformation — nothing jerky, everything smooth as breathing",
  "camera_suggestion": "Slow 360° orbit from center, catching each wall mid-transformation",
  "symbolism": "Identity in flux — the self remains while everything defining it changes",
  "psychological_theme": "Adaptation to change, finding stability within instability"
}
```

Now analyze the following dream:"""


# ============================================================
# Creative Director Service
# ============================================================

class CreativeDirectorService:
    """
    梦境创意总监 — 第一步分析服务

    接收用户的原始梦境描述，输出结构化分析 JSON。
    下游的 prompt_expansion 将基于此结构化数据生成最终 prompt。
    """

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.model = settings.QWEN_MODEL  # 用 qwen-plus，够快够便宜
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def analyze(self, content: str, gen_type: Literal["image", "video"] = "image") -> DreamAnalysis:
        """
        分析梦境，输出结构化理解

        Args:
            content: 用户原始梦境描述（中文或英文）
            gen_type: 生成目标类型，影响 motion/camera 字段的详细程度

        Returns:
            DreamAnalysis 结构化分析结果
        """
        # 构建用户消息，提示 gen_type 让模型对运动信息给予不同权重
        type_hint = ""
        if gen_type == "video":
            type_hint = "\n\n[NOTE: This will be used for VIDEO generation. Pay extra attention to motion, camera movement, and temporal flow.]"

        user_message = f"{content}{type_hint}"

        url = f"{self.base_url}/compatible-mode/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": CREATIVE_DIRECTOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.7,  # 需要一些创意但不能太发散
            "max_tokens": 1000,
            "top_p": 0.9,
            "response_format": {"type": "json_object"},  # 强制 JSON 输出
        }

        try:
            timer = ApiCallTimer()
            timer.start()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                raw_content = data["choices"][0]["message"]["content"].strip()
                timer.stop()

                # 提取 token 用量
                usage = data.get("usage", {})
                tokens_in = usage.get("prompt_tokens", 0)
                tokens_out = usage.get("completion_tokens", 0)

                # 解析 JSON
                analysis_dict = json.loads(raw_content)
                analysis = DreamAnalysis(**{
                    k: v for k, v in analysis_dict.items()
                    if k in DreamAnalysis.__dataclass_fields__
                })

                logger.info(
                    f"[CreativeDirector] emotion={analysis.primary_emotion} "
                    f"intensity={analysis.emotion_intensity} "
                    f"subjects={analysis.key_subjects[:3]}"
                )
                fire_and_forget(log_api_call(
                    model=self.model, endpoint="creative_director",
                    status="success", duration_ms=timer.duration_ms,
                    tokens_input=tokens_in, tokens_output=tokens_out,
                    response_summary={"emotion": analysis.primary_emotion, "intensity": analysis.emotion_intensity},
                ))
                return analysis

        except json.JSONDecodeError as e:
            timer.stop()
            logger.error(f"[CreativeDirector] JSON parse failed: {e}, raw={raw_content[:200]}")
            fire_and_forget(log_api_call(
                model=self.model, endpoint="creative_director",
                status="failed", duration_ms=timer.duration_ms,
                error=f"JSON parse: {str(e)[:200]}",
            ))
            return self._fallback_analysis(content)
        except Exception as e:
            timer.stop()
            logger.error(f"[CreativeDirector] LLM call failed: {e}")
            fire_and_forget(log_api_call(
                model=self.model, endpoint="creative_director",
                status="failed", duration_ms=timer.duration_ms,
                error=str(e)[:500],
            ))
            return self._fallback_analysis(content)

    def _fallback_analysis(self, content: str) -> DreamAnalysis:
        """降级方案：当 LLM 失败时返回基础分析"""
        return DreamAnalysis(
            narrative_core=content[:100],
            dreamer_role="participant in the dream",
            primary_emotion="mysterious",
            emotion_intensity=5,
            emotional_arc="sustained throughout",
            key_subjects=[content[:30]],
            environment="surreal dreamscape",
            time_of_day="timeless twilight",
            weather_atmosphere="thick fog and soft mist",
            color_palette="muted jewel tones — deep purple, soft gold, twilight blue",
            lighting_quality="diffused ambient glow with no clear source",
            texture_feel="soft, dissolving edges on everything",
            spatial_logic="normal rules don't apply — dream logic",
            primary_motion="gentle floating drift",
            motion_quality="slow, dreamlike, underwater feeling",
            camera_suggestion="slow forward drift through the scene",
            symbolism="personal subconscious imagery",
            psychological_theme="processing daily experience through dream logic",
        )


# Singleton
creative_director_service = CreativeDirectorService()
