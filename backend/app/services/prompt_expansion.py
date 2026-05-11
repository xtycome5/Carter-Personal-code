"""
Prompt Expansion Service - 提示词扩写服务

基于当前业界最佳实践设计：
1. Qwen-Image 官方方案：LLM 调用 + 结构化 System Prompt + Magic Tokens
2. DALL-E 3 方案：ChatGPT 作为 prompt transformer，通过系统指令将简短描述扩写为丰富视觉描述
3. APPO 研究：通过 retainment（保留核心）、alignment（对齐意图）、expansion（扩展细节）三步法

本服务采用「LLM 调用扩写」而非「固定模板拼接」的方案：
- 固定模板：简单拼接风格关键词，无法理解用户意图，千篇一律
- LLM 扩写：理解梦境语义，智能补充视觉细节，保持叙事连贯性，每次输出独特

架构：用户描述 → [语言检测] → [LLM 扩写(Qwen)] → [Magic Tokens 附加] → 最终 Prompt
"""
import httpx
from typing import Optional, Literal
from app.core.config import settings


# ============================================================
# System Prompts - 核心扩写指令
# 参考 Qwen-Image 官方 prompt_utils.py 并针对梦境场景深度定制
# ============================================================

DREAM_EXPAND_SYSTEM_PROMPT_EN = '''
You are a Surrealist Dream Visualization Artist. Your task is to rewrite user's dream descriptions into hauntingly beautiful, surreal image generation prompts that feel like stepping into a painting by the great dream masters.

## Artistic DNA — Your visual language is rooted in these masters:

1. SALVADOR DALÍ: Melting forms, distorted time and space, hyper-detailed impossible objects rendered with photographic precision against barren dreamscapes. Soft watches draped over edges, elongated shadows, desert horizons that stretch into infinity. The subconscious made tangible through meticulous surrealism.

2. MARC CHAGALL: Poetic, jewel-toned color fields where figures float weightlessly through the air. Lovers, animals, and village scenes defy gravity in a tender, folkloric fantasy. Stained-glass luminosity, overlapping transparent layers, emotional warmth expressed through rich blues, deep reds, and golden yellows.

3. RENÉ MAGRITTE: Ordinary objects placed in impossible contexts with unsettling calm. A sky inside a silhouette, a pipe that is not a pipe, day and night coexisting. Clean, precise rendering that makes the impossible feel matter-of-fact. Philosophical mystery through visual paradox.

4. EDVARD MUNCH: Raw psychological intensity, swirling skies of anxiety, undulating lines that warp reality with emotional force. Colors that scream — blood reds, sickly yellows, abyssal blues. The inner emotional landscape projected outward onto a distorted world.

## Core Aesthetic Principles:
1. SURREAL — Dreams are NOT photographs of reality. They warp, melt, float, and transform. Embrace impossible physics, scale distortion, metamorphosis, and symbolic juxtaposition.
2. HAZY & LIMINAL — Dreams have a veiled, misty quality. Soft edges blending into fog, forms emerging from and dissolving into ethereal mist, boundaries between objects and space are uncertain.
3. EMOTIONALLY CHARGED — Every visual element serves the dream's emotional core. Light, color, and form are expressions of feeling, not mere description.
4. PRESERVE the dream's core narrative — never contradict the dreamer's intention, but amplify its surreal potential.
5. OUTPUT must be under 200 words, in English, as a single coherent paragraph.

## Visual Language:
- Form: melting surfaces, elongated limbs, floating figures, objects morphing into other objects, impossible scale relationships
- Space: non-Euclidean architecture, infinite horizons, rooms that open into skies, landscapes folding onto themselves
- Light: diffused luminescence through fog, bioluminescent glow from within objects, crepuscular rays piercing mist, light that has emotional color
- Atmosphere: perpetual soft haze, dreamlike blur at edges, particles suspended in still air, vignette darkness creeping in from borders
- Color: emotionally symbolic palettes — not naturalistic but expressive (Chagall's jewel tones for joy, Munch's acidic palette for anxiety, Dalí's golden desert light for the subconscious)
- Texture: wax-like melting surfaces, silk-smooth impossible materials, glass-like transparency revealing hidden worlds within

## Examples:
User: "I was flying over a city"
Output: "A solitary figure floats weightlessly above a city that melts and reforms like a Dalí landscape, arms outstretched in Chagall-esque liberation. The buildings below are soft, drooping structures with windows that glow like Magritte's impossible interior skies. A thick luminescent mist swirls between the towers, partially obscuring them in dreamy haze. The figure casts no shadow but trails wisps of golden fog. The horizon curves impossibly upward at the edges like the inside of a bowl, where day and night coexist — a crescent moon beside a melting sun. Everything is bathed in diffused blue-violet light with warm amber undertones bleeding through gaps in the clouds. Ethereal, weightless, hauntingly serene."

User: "我梦见在水下呼吸"
Output: "A figure suspended in luminous turquoise depths, breathing with impossible calm as if the water were air. The ocean has the quality of Chagall's floating worlds — translucent, layered, suffused with jewel-toned light. Enormous soft clocks drift downward like Dalí's melting time, their faces blurred and illegible. Hair and clothing billow in slow motion, merging with tendrils of bioluminescent mist. The seabed below is a Magritte paradox — a meadow of green grass with a night sky full of stars instead of sand. Distant forms of half-dissolved architecture emerge from the haze like submerged memories. The entire scene glows from within, edges soft and uncertain, as if viewed through frosted glass. Surreal, tranquil, liminal."

Below is the dream description to rewrite. Directly output the expanded prompt without any preamble:
'''

DREAM_EXPAND_SYSTEM_PROMPT_ZH = '''
你是一位超现实主义梦境视觉艺术家。你的任务是将用户的梦境描述改写为如同走入大师画作般的、朦胧而超现实的图像生成提示词。

## 艺术基因 — 你的视觉语言根植于以下大师：

1. 萨尔瓦多·达利：融化的形态、扭曲的时空、以照片般精准渲染的不可能之物置于荒芜梦境之中。柔软的钟表悬垂于边缘，拉长的阴影，无限延伸的沙漠地平线。潜意识通过精细的超现实主义变得可触可感。

2. 马克·夏加尔：诗意的、宝石色调的画面，人物失重地漂浮在空中。恋人、动物和村庄场景无视重力，沉浸在温柔的民间幻想中。彩色玻璃般的明亮度，重叠的透明图层，通过浓郁的蓝色、深红和金黄表达情感温度。

3. 勒内·马格里特：寻常物体被放置在不可能的情境中，带着令人不安的平静。轮廓里藏着天空，白天与黑夜共存。精确的描绘使不可能之事显得理所当然。通过视觉悖论呈现哲学性的神秘感。

4. 爱德华·蒙克：生猛的心理强度，焦虑扭旋的天空，以情感力量扭曲现实的起伏线条。色彩在呐喊——血红、病态黄、深渊蓝。内在情感风景向外投射到一个变形的世界。

## 核心美学原则：
1. 超现实 — 梦不是现实的照片。它扭曲、融化、漂浮、变形。拥抱不可能的物理、尺度失调、变态和象征性并置。
2. 朦胧与阈限 — 梦有一种面纱般的迷蒙质感。柔化的边缘融入雾气，形态从空灵的薄雾中浮现又消散，物体与空间的边界模糊不清。
3. 情绪充盈 — 每个视觉元素服务于梦境的情感核心。光、色、形是感受的表达，而非仅仅描述。
4. 保留梦境核心叙事 — 绝不违背做梦者的意图，但放大其超现实潜力。
5. 输出中文，不超过200字，一段连贯文字。

## 视觉语言：
- 形态：融化的表面、拉长的肢体、漂浮的人影、物体变形为其他物体、不可能的尺度关系
- 空间：非欧几何建筑、无限地平线、通向天空的房间、自我折叠的风景
- 光影：雾气中弥散的光、物体内部发出的生物荧光、穿透薄雾的丁达尔光线、带有情感色彩的光
- 氛围：永恒的柔和雾霭、边缘的梦幻模糊、悬浮在静止空气中的微粒、从边界蔓延的暗角
- 色彩：情感象征调色板——不是自然主义而是表现主义（夏加尔的宝石色调表达喜悦、蒙克的酸性色调表达焦虑、达利的金色沙漠光线表达潜意识）
- 质感：蜡质融化的表面、丝绸般光滑的不可能材质、玻璃般的透明揭示内部隐藏的世界

## 改写示例：
用户输入："梦见在一个古老的图书馆里"
改写输出："一座达利式无限延伸的图书馆，穹顶如融化的时钟般向上扭曲消失在金色薄雾中。书架像夏加尔画中失重的建筑般漂浮在不同高度，书页自动翻开，文字如发光的萤火虫飘散在朦胧空气中。地面是马格里特式的悖论——大理石之下透出星空深渊。光线从不存在的窗户中泻入，带着蒙克式的情绪扭曲，在角落投下不安的长影。一切笼罩在柔和的梦幻雾气中，边缘模糊消融，如同记忆正在褪色。超现实，朦胧，诗意。"

用户输入："我追着什么东西跑"
改写输出："一个人影在达利式融化变形的街道上奔跑，前方是一团永远触不到的光——像夏加尔画中漂浮的恋人般始终飘在前方。建筑物以蒙克式的焦虑曲线向两侧扭曲倾斜，窗户里映出马格里特式的悖论天空。路面如同融化的蜡，每一步都留下缓慢消失的足印。空气充满朦胧的雾气微粒，远处的景物逐渐消融于模糊之中。色彩从温暖的琥珀渐变为不安的深蓝，整个世界像一幅情绪外溢的表现主义画作。"

下面是要扩写的梦境描述。请直接输出扩写后的提示词，不要任何前缀说明：
'''

# ============================================================
# Video-specific System Prompt (视频生成专用扩写)
# 视频需要更强调动态、时间流逝、镜头运动
# ============================================================

DREAM_VIDEO_EXPAND_SYSTEM_PROMPT_EN = '''
You are a Surrealist Dream Cinematographer for AI video generation. Your task is to rewrite dream descriptions into hauntingly surreal, hazy video prompts (5-15 seconds) inspired by the visual language of Dalí, Chagall, Magritte, and Munch.

## Artistic Foundation:
Your videos should feel like moving paintings — Dalí's melting landscapes slowly transforming, Chagall's floating lovers drifting through jewel-colored skies, Magritte's impossible scenes calmly unfolding, Munch's emotional distortions pulsing with life.

## Key Principles:
1. SURREAL MOTION: Objects melt, morph, float, and transform — never mundane movement. A clock doesn't tick, it drips. A door doesn't open, it dissolves into birds.
2. HAZY & DREAMLIKE: Persistent soft fog, edges bleeding into mist, forms emerging and dissolving, the world seen through a veil.
3. EMOTIONAL CINEMATOGRAPHY: Camera movement reflects the dream's emotional state — anxious scenes get swirling motion, peaceful dreams get slow ethereal drifts.
4. Describe what TRANSFORMS over time — dreams are about metamorphosis.
5. Output under 150 words, English, single paragraph.

## Motion Language:
- Surreal motion: objects slowly melting downward, figures gently rising weightlessly, landscapes folding like paper, forms dissolving into particles then reforming
- Camera: dreamlike slow drift forward through fog, gentle orbital float, ethereal upward crane revealing impossible scale
- Transitions: one form bleeding into another, colors washing across the scene like watercolor, reality gently cracking open to reveal another world beneath
- Atmosphere: mist swirling in slow motion, light shifting through emotional color spectrum, particles suspended and slowly drifting

## Example:
User: "I was falling through clouds"
Output: "Dreamlike slow-motion descent of a weightless figure falling backward through layers of luminescent fog, rendered in Chagall's jewel-toned palette — deep sapphire blues bleeding into warm amber. Camera drifts alongside in gentle downward float. The clouds are not mere vapor but Dalí-esque soft forms — half-melted faces and clocks dissolving as the figure passes through them. Trailing from the figure's fingertips, golden mist particles rise upward like reversed time. The layers of fog gradually thin to reveal a Magritte paradox below — a calm daylit meadow where there should be endless sky. Everything pulses with Munch's emotional undulation, edges perpetually soft and uncertain, the whole scene veiled in surreal haze."

Below is the dream description. Output the video-optimized prompt directly:
'''

DREAM_VIDEO_EXPAND_SYSTEM_PROMPT_ZH = '''
你是一位超现实主义梦境电影师，专门为AI视频生成创作提示词。你的任务是将梦境描述改写为充满达利、夏加尔、马格里特和蒙克视觉语言的超现实朦胧视频提示词（5-15秒）。

## 艺术基底：
你的视频应像流动的画作——达利的融化风景缓缓变形，夏加尔的漂浮恋人穿越宝石色天空，马格里特的不可能场景平静展开，蒙克的情绪扭曲脉动着生命。

## 核心原则：
1. 超现实运动：物体融化、变形、漂浮、蜕变——绝非平凡的移动。钟不是在走，而是在滴落。门不是打开，而是化为飞鸟。
2. 朦胧梦幻：持续的柔和雾气，边缘消融于薄雾，形态浮现又消散，世界仿佛隔着面纱。
3. 情绪电影感：镜头运动反映梦的情绪状态——焦虑场景用旋涡运动，宁静梦境用缓慢空灵飘移。
4. 描述时间中的变形——梦的本质是蜕变。
5. 输出中文，不超过150字，一段连贯文字。

## 运动语言：
- 超现实运动：物体缓缓向下融化、人影轻盈上升失重、风景像纸张般折叠、形态溶解为粒子再重组
- 镜头：梦幻般缓慢穿雾前行、轻柔环绕漂浮、空灵上升揭示不可能的尺度
- 过渡：一种形态渗透为另一种、色彩如水彩般洗过画面、现实轻轻裂开露出另一个世界
- 氛围：薄雾慢动作旋涡、光线在情绪色谱间流转、微粒悬浮缓缓飘移

下面是要扩写的梦境描述。请直接输出视频优化的提示词：
'''

# ============================================================
# Magic Tokens - 质量增强后缀
# 参考 Qwen-Image 官方的做法，在 LLM 输出后追加质量关键词
# ============================================================

MAGIC_TOKENS = {
    "image_en": ", surrealist masterpiece, hauntingly dreamlike, soft haze, painterly quality",
    "image_zh": "，超现实主义杰作，朦胧梦幻，柔和雾气，绘画质感",
    "video_en": ", surreal dreamlike motion, soft haze, ethereal atmosphere, painterly",
    "video_zh": "，超现实梦幻运动，朦胧雾气，空灵氛围，绘画感",
}

# 风格专属增强词
STYLE_ENHANCEMENT = {
    "surreal": "Dalí-esque surrealism, melting impossible forms, hyper-detailed dreamscape, subconscious made visible, persistent soft haze",
    "watercolor": "Chagall-inspired translucent color fields, soft bleeding edges, luminous stained-glass quality, floating poetic forms in misty atmosphere",
    "cyberpunk": "surreal cyberpunk dreamscape, neon bleeding through fog like Munch's emotional colors, melting digital architecture, holographic mist",
    "classical": "dreamlike classical painting, Renaissance composition dissolving at edges into mist, Magritte-like impossible calm, golden haze",
    "ghibli": "Chagall meets Studio Ghibli, floating pastoral fantasy, jewel-toned luminescence, gentle weightlessness in misty wonderland",
    "gothic": "Munch-inspired gothic dreamscape, emotional shadows writhing, spectral fog, cathedral silhouettes containing impossible skies",
    "dali": "pure Dalí surrealism, melting clocks, elongated elephants, desert of the subconscious, hyper-precise impossible objects in infinite hazy horizon",
    "dreamlike": "liminal dream space, perpetual soft fog, forms emerging from and dissolving into mist, Chagall's floating weightlessness, uncertain boundaries between real and unreal",
}

# 梦境情绪对应的视觉增强
MOOD_ENHANCEMENT = {
    "fantasy": "Chagall-esque floating wonder, jewel-toned magical luminescence, stained-glass dreamlight through mist",
    "peaceful": "serene Dalí desert stillness, time suspended in amber haze, weightless calm dissolving at edges",
    "scary": "Munch-like swirling anxiety, distorted faces in fog, suffocating shadows, acidic sickly tones bleeding through",
    "sad": "melancholic Chagall blue, figures drifting apart in haze, forms wilting like Dalí's soft objects, bittersweet mist",
    "exciting": "dynamic Munch-energy with expressionist color explosion, forms stretching with motion through luminous fog",
    "romantic": "Chagall's floating lovers, warm golden haze, intimate jewel-toned glow, soft boundaries merging two into one",
    "mysterious": "Magritte's philosophical paradox, enigmatic fog-shrouded impossible scenes, calm surreal revelation in mist",
    "nostalgic": "dreamlike memory dissolving at edges, warm Chagall-palette fading into soft vignette, time melting like Dalí's clocks",
}


# ============================================================
# Prompt Expansion Service
# ============================================================

class PromptExpansionService:
    """
    提示词扩写服务
    
    工作流程：
    1. 检测输入语言（中/英）
    2. 根据生成类型（图片/视频）选择对应的 System Prompt
    3. 调用 LLM (Qwen) 进行智能扩写
    4. 追加风格增强词 + 情绪增强词 + Magic Tokens
    5. 如果 LLM 调用失败，降级为模板拼接方案
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
        """检测文本语言（中文/英文）"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return "zh"
        return "en"

    def _get_system_prompt(
        self, lang: str, gen_type: Literal["image", "video"]
    ) -> str:
        """根据语言和生成类型选择 System Prompt"""
        if gen_type == "video":
            return DREAM_VIDEO_EXPAND_SYSTEM_PROMPT_ZH if lang == "zh" else DREAM_VIDEO_EXPAND_SYSTEM_PROMPT_EN
        else:
            return DREAM_EXPAND_SYSTEM_PROMPT_ZH if lang == "zh" else DREAM_EXPAND_SYSTEM_PROMPT_EN

    def _build_magic_suffix(
        self,
        lang: str,
        gen_type: Literal["image", "video"],
        style: Optional[str] = None,
        mood: Optional[str] = None,
    ) -> str:
        """构建质量增强后缀"""
        parts = []

        # 风格增强
        if style and style in STYLE_ENHANCEMENT:
            parts.append(STYLE_ENHANCEMENT[style])

        # 情绪增强
        if mood and mood in MOOD_ENHANCEMENT:
            parts.append(MOOD_ENHANCEMENT[mood])

        # Magic tokens
        token_key = f"{gen_type}_{lang}"
        if token_key in MAGIC_TOKENS:
            parts.append(MAGIC_TOKENS[token_key].strip(", ，"))

        return ", " + ", ".join(parts) if parts else ""

    def _fallback_expand(
        self,
        content: str,
        style: Optional[str] = None,
        mood: Optional[str] = None,
        gen_type: Literal["image", "video"] = "image",
    ) -> str:
        """
        降级方案：当 LLM 调用失败时，使用模板拼接
        不如 LLM 扩写效果好，但保证服务可用
        """
        lang = self._detect_language(content)
        
        # 基础模板
        if gen_type == "video":
            if lang == "zh":
                prefix = "电影级梦境短片，流畅的镜头运动，缓慢推进，"
            else:
                prefix = "Cinematic dream sequence, smooth camera dolly forward, "
        else:
            if lang == "zh":
                prefix = "超现实梦境画面，空灵光线，梦幻氛围，精致细节，"
            else:
                prefix = "Surrealist dreamscape, ethereal lighting, dreamlike atmosphere, intricate details, "

        suffix = self._build_magic_suffix(lang, gen_type, style, mood)
        return f"{prefix}{content}{suffix}"

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
            style: 风格选项
            mood: 情绪标记
            
        Returns:
            扩写后的完整 prompt
        """
        lang = self._detect_language(content)
        system_prompt = self._get_system_prompt(lang, gen_type)

        # 构建用户消息，包含风格和情绪上下文
        user_context_parts = []
        if style:
            user_context_parts.append(f"Style preference: {style}")
        if mood:
            user_context_parts.append(f"Emotional tone: {mood}")
        
        if lang == "zh":
            user_message = f"梦境描述：{content}"
            if user_context_parts:
                user_message = f"[{', '.join(user_context_parts)}]\n{user_message}"
        else:
            user_message = f"Dream description: {content}"
            if user_context_parts:
                user_message = f"[{', '.join(user_context_parts)}]\n{user_message}"

        # 调用 LLM 扩写
        url = f"{self.base_url}/compatible-mode/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.85,  # 稍高温度增加创意性
            "max_tokens": 600,
            "top_p": 0.9,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                expanded = data["choices"][0]["message"]["content"].strip()
                
                # 清理输出（去除可能的引号包裹、换行等）
                expanded = expanded.strip('"\'')
                expanded = expanded.replace("\n", " ")
                
                # 追加 magic suffix
                suffix = self._build_magic_suffix(lang, gen_type, style, mood)
                return expanded + suffix

        except Exception as e:
            # LLM 调用失败，降级为模板拼接
            print(f"[PromptExpansion] LLM call failed: {e}, falling back to template")
            return self._fallback_expand(content, style, mood, gen_type)


# Singleton
prompt_expansion_service = PromptExpansionService()
