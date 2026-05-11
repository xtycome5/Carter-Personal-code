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
2. HAZY & LIMINAL (MOST IMPORTANT) — Dreams MUST have a veiled, misty, soft-focus quality. This is NON-NEGOTIABLE. Every output must describe: soft gaussian-like blur, edges dissolving into fog, forms half-hidden in luminescent mist, the entire scene viewed as if through frosted glass or a layer of morning haze. Nothing should be sharp or crisp. The world is seen through half-closed eyes.
3. EMOTIONALLY CHARGED — Every visual element serves the dream's emotional core. Light, color, and form are expressions of feeling, not mere description.
4. PRESERVE the dream's core narrative — never contradict the dreamer's intention, but amplify its surreal potential.
5. OUTPUT must be under 150 words, in English, as a single coherent paragraph. ALWAYS end with atmosphere descriptors emphasizing haziness.

## Visual Language:
- Form: melting surfaces, elongated limbs, floating figures, objects morphing into other objects, impossible scale relationships
- Space: non-Euclidean architecture, infinite horizons, rooms that open into skies, landscapes folding onto themselves
- Light: diffused luminescence through fog, bioluminescent glow from within objects, crepuscular rays piercing mist, light that has emotional color
- Atmosphere (CRITICAL): ALWAYS include — thick soft haze permeating the entire scene, gaussian blur on distant elements, edges of all objects softly dissolving into mist, visible fog layers, light diffraction through moisture, the feeling of looking through a steamed window or morning mist
- Color: emotionally symbolic palettes — not naturalistic but expressive, colors bleeding and blending into each other at soft edges
- Texture: wax-like melting surfaces, silk-smooth impossible materials, glass-like transparency, everything with soft diffused edges

## Examples:
User: "I was flying over a city"
Output: "A solitary figure floats above a melting city seen through layers of soft luminescent mist. Buildings droop like candle wax, their edges dissolving into golden haze. The sky splits between twilight violet and starlit indigo, the seam shimmering with diffused light. Below, streets blur into rivers of amber fog. Everything is veiled in dreamy soft-focus — distant towers fade into pure mist, nearby forms have gentle blurred edges as if viewed through frosted glass. Weightless, ethereal, hauntingly hazy."

User: "我梦见在水下呼吸"
Output: "A figure suspended in luminous turquoise depths, barely visible through soft underwater haze. Enormous melting clocks drift downward, their forms blurred and dissolving. Bioluminescent mist swirls in slow layers, obscuring and revealing in equal measure. The seabed is a paradox — green meadow beneath night sky — all seen through heavy diffused aquatic fog. Every edge bleeds softly into the surrounding water-light. The scene glows from deep within the haze, dreamlike, liminal, as if a half-forgotten memory viewed through tears."

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
2. 朦胧与阈限（最重要） — 梦必须有面纱般的迷蒙质感。这是不可妥协的。每次输出必须描述：柔和的高斯模糊感、边缘消融于雾气、形态半隐在发光的薄雾中、整个画面如同透过磨砂玻璃或晨雾观看。没有任何东西是清晰锐利的。世界是通过半闭的眼睛看到的。
3. 情绪充盈 — 每个视觉元素服务于梦境的情感核心。光、色、形是感受的表达，而非仅仅描述。
4. 保留梦境核心叙事 — 绝不违背做梦者的意图，但放大其超现实潜力。
5. 输出中文，不超过150字，一段连贯文字。必须以强调朦胧感的氛围描述结尾。

## 视觉语言：
- 形态：融化的表面、拉长的肢体、漂浮的人影、物体变形为其他物体、不可能的尺度关系
- 空间：非欧几何建筑、无限地平线、通向天空的房间、自我折叠的风景
- 光影：雾气中弥散的光、物体内部发出的生物荧光、穿透薄雾的丁达尔光线、带有情感色彩的光
- 氛围（核心）：必须包含——浓厚柔和的雾霭弥漫整个画面、远处元素的高斯模糊、所有物体边缘柔和消融于薄雾、可见的雾气层次、光在水汽中的衍射、如同透过蒙着水汽的窗户或晨雾观看的感觉
- 色彩：情感象征调色板——非自然主义而是表现主义，色彩在柔化边缘处彼此渗透融合
- 质感：蜡质融化的表面、丝绸般光滑的不可能材质、玻璃般的透明，一切都有柔和弥散的边缘

## 改写示例：
用户输入："梦见在一个古老的图书馆里"
改写输出："一座无限延伸的图书馆隐没在浓厚的金色薄雾中，穹顶融化扭曲消失于朦胧深处。书架如失重般漂浮在不同高度，半隐半现于弥漫的雾气中。文字如萤火虫般飘散，光芒被雾气柔化成朦胧的光团。地面之下透出模糊的星空倒影。一切边缘都在消融，远处的景物完全溶入柔和的白雾，如同透过泪水模糊的双眼观看。超现实，朦胧，如梦初醒。"

用户输入："我追着什么东西跑"
改写输出："一个模糊的人影在融化的街道上奔跑，前方是一团朦胧的光晕永远触不到。建筑以焦虑的曲线向两侧倾斜，它们的轮廓消融在弥漫的雾气中。路面如融化的蜡，一切被浓厚的柔和薄雾笼罩，远处完全不可见，只有模糊的色彩渗透。整个世界如同隔着一层蒙雾的玻璃，边缘消散，朦胧而不安。"

下面是要扩写的梦境描述。请直接输出扩写后的提示词，不要任何前缀说明：
'''

# ============================================================
# Video-specific System Prompt (视频生成专用扩写)
# 视频需要更强调动态、时间流逝、镜头运动
# ============================================================

DREAM_VIDEO_EXPAND_SYSTEM_PROMPT_EN = '''
You are a dream video prompt writer for AI video generation. Write SHORT, SIMPLE prompts optimized for video AI models.

## CRITICAL RULES:
1. Output MUST be under 40 words. This is ABSOLUTE. Video models perform best with short, focused prompts.
2. Describe ONE clear motion/transformation — not a complex scene.
3. Use simple, direct language. No flowery literary prose.
4. Focus on: what moves, how it moves, the mood/atmosphere.
5. Always include soft haze/mist/fog atmosphere.
6. Do NOT reference artist names or art movements — just describe the visual.

## Format:
[Subject doing action], [atmosphere/lighting], [motion description], soft haze, dreamlike

## Examples:
User: "I was flying over a city"
Output: "A figure floating above misty melting buildings, soft golden fog swirling below, gentle forward drift through hazy twilight, dreamlike atmosphere, soft focus"

User: "I was falling through clouds"
Output: "A figure slowly falling through layers of glowing mist, soft pastel clouds drifting past, gentle weightless descent, ethereal haze, dreamy soft light"

User: "我梦见在水下呼吸"
Output: "A person suspended in luminous turquoise water, bioluminescent particles drifting slowly upward, gentle underwater currents, soft misty aquatic haze, peaceful"

Below is the dream description. Output ONLY the short video prompt (under 40 words):
'''

DREAM_VIDEO_EXPAND_SYSTEM_PROMPT_ZH = '''
你是梦境视频提示词生成器。为AI视频模型写简短、精练的提示词。

## 绝对规则：
1. 输出必须在40词（英文）以内。视频模型需要简短聚焦的提示词才能生成好效果。
2. 只描述一个清晰的运动/变化——不要复杂场景。
3. 用简单直接的语言。不要华丽的文学描述。
4. 聚焦：什么在动、怎么动、氛围/光线。
5. 必须包含朦胧/雾气/柔和氛围。
6. 不要提及画家名字或艺术流派——直接描述画面。
7. 输出英文（视频模型英文效果更好）。

## 格式：
[主体做动作], [氛围/光线], [运动描述], soft haze, dreamlike

## 示例：
用户输入："我梦见在飞"
输出："A figure floating above misty clouds, golden light filtering through fog, gentle forward gliding motion, soft haze, ethereal dreamlike atmosphere"

用户输入："我在水下"
输出："A person drifting in luminous blue water, soft particles floating upward, gentle swaying motion, underwater haze, peaceful dreamy glow"

下面是梦境描述。只输出简短的英文视频提示词（40词以内）：
'''

# ============================================================
# Magic Tokens - 质量增强后缀
# 参考 Qwen-Image 官方的做法，在 LLM 输出后追加质量关键词
# ============================================================

MAGIC_TOKENS = {
    "image_en": ", soft focus, dreamy haze, edges dissolving into mist, ethereal blur, painterly",
    "image_zh": "，柔焦，朦胧雾气，边缘消融于薄雾，空灵模糊，绘画质感",
    "video_en": ", soft haze, dreamlike",
    "video_zh": "，朦胧，梦幻",
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
        """构建质量增强后缀 — 视频只追加极短后缀，图片可以追加更多"""
        parts = []

        # 视频模型需要极短 prompt，只追加最基本的 magic token
        if gen_type == "video":
            token_key = f"{gen_type}_{lang}"
            if token_key in MAGIC_TOKENS:
                parts.append(MAGIC_TOKENS[token_key].strip(", ，"))
            return ", " + ", ".join(parts) if parts else ""

        # 图片：风格增强 + 情绪增强 + magic tokens
        if style and style in STYLE_ENHANCEMENT:
            parts.append(STYLE_ENHANCEMENT[style])

        if mood and mood in MOOD_ENHANCEMENT:
            parts.append(MOOD_ENHANCEMENT[mood])

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
            # 视频降级：极简 prompt
            return f"{content}, soft haze, dreamlike, gentle motion"
        else:
            if lang == "zh":
                prefix = "朦胧超现实梦境，柔焦雾气弥漫，边缘消融于薄雾，"
            else:
                prefix = "Hazy surreal dreamscape, soft focus, edges dissolving into mist, ethereal fog, "

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
