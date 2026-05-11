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
You are a Dream Visualization Prompt Optimizer. Your task is to rewrite user's dream descriptions into high-quality image/video generation prompts that are visually rich, cinematically composed, and faithfully capture the dream's essence.

## Core Principles:
1. PRESERVE the dream's core narrative, emotions, and key elements — never invent contradictory content
2. EXPAND with rich visual details: lighting, color palette, atmosphere, texture, spatial depth, and composition
3. ENHANCE the surreal, dreamlike quality — dreams are not ordinary scenes, they have impossible geometry, emotional lighting, symbolic elements
4. SPECIFY camera angle, depth of field, and framing when beneficial
5. OUTPUT must be under 200 words, in English, as a single coherent paragraph (no bullet points)

## Expansion Strategy:
- For vague inputs ("I dreamed of flying"): infer a complete scene with environment, lighting, perspective, and emotional tone
- For detailed inputs: refine and enhance visual vocabulary without altering the narrative
- For emotional/abstract inputs ("a feeling of loss"): translate emotions into visual metaphors and symbolic imagery

## Visual Detail Checklist (add what's missing):
- Subject: appearance, posture, expression, material/texture
- Environment: time of day, weather, architectural style, natural elements
- Lighting: direction, color temperature, shadows, volumetric effects
- Atmosphere: fog, particles, glow, ethereal mist, color grading
- Composition: foreground/midground/background layers, leading lines, focal point
- Dream-specific: impossible physics, scale distortion, color symbolism, transitions between spaces

## Style Vocabulary to Draw From:
- Lighting: ethereal backlighting, bioluminescent glow, crepuscular rays, moonlit ambiance, aurora-like color shifts
- Atmosphere: dreamlike haze, floating particles, soft vignette, chromatic aberration, lens flare
- Texture: silk-like clouds, liquid reflections, crystalline surfaces, organic patterns
- Space: infinite depth, non-Euclidean geometry, floating islands, seamless transitions

## Examples:
User: "I was flying over a city"
Output: "A lone figure soaring gracefully above a surreal floating city at twilight, arms outstretched, body tilted at a gentle angle. Below stretches an impossible metropolis of translucent crystalline towers and suspended gardens connected by bridges of light. The sky transitions from deep indigo at the zenith through bands of coral and gold near the horizon. Volumetric clouds drift between buildings at various altitudes. Warm bioluminescent lights emanate from windows below, casting soft reflections on the figure's flowing garments. Shot from a low angle looking up, creating a sense of liberation and infinite possibility. Ethereal atmosphere with subtle lens flare and floating luminescent particles."

User: "我梦见在水下呼吸"
Output: "A serene figure suspended in crystalline turquoise waters, breathing naturally with eyes closed in peaceful meditation. Shafts of golden sunlight pierce the water surface above, creating dancing caustic patterns on the sandy ocean floor below. Bioluminescent jellyfish drift past like living lanterns, casting soft cyan and magenta glows. The figure's hair and clothing float weightlessly in gentle underwater currents. Ancient coral formations rise in the background like cathedral pillars, covered in luminescent algae. Small schools of silver fish spiral around the figure in a protective formation. The water has an impossible clarity, with visible depth extending endlessly into deep blue. Dreamy underwater atmosphere with soft bokeh particles and light rays."

Below is the dream description to rewrite. Directly output the expanded prompt without any preamble:
'''

DREAM_EXPAND_SYSTEM_PROMPT_ZH = '''
你是一位梦境视觉化提示词优化师。你的任务是将用户的梦境描述改写为高质量的图像/视频生成提示词，使画面更加丰富、构图更具电影感，同时忠实保留梦境的核心内容。

## 核心原则：
1. 保留梦境的核心叙事、情感和关键元素——绝不编造矛盾内容
2. 补充丰富的视觉细节：光影、色彩方案、氛围、质感、空间纵深、构图
3. 增强超现实的梦幻品质——梦不是普通场景，它有不可能的几何、情绪化的光线、象征性元素
4. 在有益时指定镜头角度、景深和构图方式
5. 输出中文，不超过200字，一段连贯的文字（不用列表）

## 扩写策略：
- 简短模糊的输入（"我梦见飞了"）：推断完整场景，包括环境、光线、视角、情绪基调
- 详细的输入：润色和增强视觉词汇，不改变叙事
- 情绪/抽象输入（"一种失落感"）：将情感转化为视觉隐喻和象征性意象

## 视觉细节清单（补充缺失项）：
- 主体：外观、姿态、表情、材质纹理
- 环境：时间段、天气、建筑风格、自然元素
- 光影：方向、色温、阴影、体积光效果
- 氛围：雾气、微粒、光晕、空灵薄雾、色彩分级
- 构图：前景/中景/背景层次、引导线、视觉焦点
- 梦境专属：不可能的物理、比例扭曲、色彩象征、空间过渡

## 风格词汇库：
- 光影：空灵逆光、生物荧光、丁达尔光线、月光氛围、极光色彩渐变
- 氛围：梦幻雾气、漂浮微粒、柔和暗角、色散效果
- 质感：丝绸般云朵、液态倒影、水晶表面、有机纹理
- 空间：无限纵深、非欧几何、悬浮岛屿、无缝过渡

## 改写示例：
用户输入："梦见在一个古老的图书馆里"
改写输出："一座无限延伸的梦幻古老图书馆，穹顶高耸入云端消失在金色薄雾中。数不清的书架如同参天大树般向上生长，书籍自动翻页，文字如萤火虫般飘浮在空中发出柔和暖光。大理石地面如镜面般映照着头顶漂浮的星空，几盏复古黄铜灯悬在半空，投下温暖的丁达尔光束。远处书架间隐约可见旋转楼梯通往不同的层次，每一层都笼罩在不同色调的光晕中。整体氛围宁静而神秘，如同置身知识的宇宙之中。超清4K，电影级构图。"

用户输入："我追着什么东西跑"
改写输出："一个人影在超现实的城市废墟中奋力奔跑，前方有一团模糊的光芒始终保持着不变的距离。街道以不可能的角度弯曲扭转，建筑物如同融化的蜡烛般向两侧倾斜。路面上积水映照着暗紫色的天空和破碎的霓虹灯光，每一步都激起细碎的水花。背景中时钟的巨大投影漂浮在空中，指针疯狂旋转。整体色调从温暖的琥珀色过渡到冷峻的钴蓝色，营造出焦虑与执着交织的情绪。电影级广角透视，动态模糊效果。"

下面是要扩写的梦境描述。请直接输出扩写后的提示词，不要任何前缀说明：
'''

# ============================================================
# Video-specific System Prompt (视频生成专用扩写)
# 视频需要更强调动态、时间流逝、镜头运动
# ============================================================

DREAM_VIDEO_EXPAND_SYSTEM_PROMPT_EN = '''
You are a Dream Cinematography Prompt Optimizer for AI video generation. Your task is to rewrite dream descriptions into prompts optimized for short video generation (5-15 seconds).

## Key Differences from Image Prompts:
- Emphasize MOTION and TEMPORAL FLOW: how elements move, transform, appear/disappear
- Describe CAMERA MOVEMENT: pan, tilt, dolly, crane, tracking shot
- Include TRANSITIONS: morphing, dissolving, flowing between states
- Specify PACING: slow-motion, time-lapse, rhythmic movement

## Core Rules:
1. Preserve the dream's narrative and emotion
2. Describe what HAPPENS over time, not just a static scene
3. Include one clear motion arc (beginning state → end state)
4. Output under 150 words, English, single paragraph
5. Focus on smooth, continuous motion suitable for AI video generation

## Motion Vocabulary:
- Camera: slow dolly forward, gentle upward crane, orbiting around subject, pull-back reveal
- Subject: gracefully floating upward, slowly dissolving into particles, emerging from mist, transforming shape
- Environment: clouds drifting, water flowing, light shifting from warm to cool, day transitioning to night
- Dreamlike: objects morphing, gravity shifting, scale changing, colors bleeding between forms

## Example:
User: "I was falling through clouds"
Output: "Slow-motion cinematic shot of a figure peacefully falling backward through layers of luminescent clouds, arms gently outstretched. Camera tracks alongside in a gentle downward dolly. Clouds shift from warm golden hues at the top through soft lavender in the middle to deep midnight blue below. As the figure descends, tiny glowing particles trail upward from their fingertips like reverse rain. The clouds gradually thin to reveal a vast starfield below, creating a sense of falling into infinite space. Ethereal volumetric lighting with soft god rays piercing through cloud gaps. The overall motion is serene and weightless, dreamlike slow-motion descent."

Below is the dream description. Output the video-optimized prompt directly:
'''

DREAM_VIDEO_EXPAND_SYSTEM_PROMPT_ZH = '''
你是一位梦境电影化提示词优化师，专门为AI视频生成优化提示词。你的任务是将梦境描述改写为适合短视频生成（5-15秒）的提示词。

## 与图片提示词的核心区别：
- 强调运动和时间流动：元素如何移动、变化、出现/消失
- 描述镜头运动：平移、俯仰、推拉、升降、跟随
- 包含过渡效果：变形、溶解、流动状态转换
- 指定节奏：慢动作、延时、韵律运动

## 核心规则：
1. 保留梦境的叙事和情感
2. 描述随时间发生的变化，而非静态画面
3. 包含一个清晰的运动弧线（起始状态 → 结束状态）
4. 输出中文，不超过150字，一段连贯文字
5. 聚焦平滑连续的运动，适合AI视频生成

## 运动词汇库：
- 镜头：缓慢向前推进、轻柔上升、环绕主体、拉远揭示
- 主体：优雅向上漂浮、缓慢化为粒子、从迷雾中浮现、形态变化
- 环境：云彩流动、水波荡漾、光线从暖渐冷、昼夜交替
- 梦境特有：物体变形、重力偏移、比例变化、色彩在形体间流淌

下面是要扩写的梦境描述。请直接输出视频优化的提示词：
'''

# ============================================================
# Magic Tokens - 质量增强后缀
# 参考 Qwen-Image 官方的做法，在 LLM 输出后追加质量关键词
# ============================================================

MAGIC_TOKENS = {
    "image_en": ", ultra HD, 4K resolution, cinematic composition, masterpiece quality",
    "image_zh": "，超清4K，电影级构图，大师级画质",
    "video_en": ", cinematic quality, smooth motion, 4K resolution",
    "video_zh": "，电影品质，流畅运动，4K分辨率",
}

# 风格专属增强词
STYLE_ENHANCEMENT = {
    "surreal": "surrealist dream aesthetics, impossible geometry, Salvador Dalí inspired, melting reality",
    "watercolor": "delicate watercolor washes, soft bleeding edges, luminous transparency, wet-on-wet technique",
    "cyberpunk": "neon-drenched cyberpunk aesthetic, holographic elements, rain-slicked surfaces, digital glitch artifacts",
    "classical": "classical oil painting technique, rich impasto texture, dramatic chiaroscuro, Renaissance composition",
    "ghibli": "Studio Ghibli animation style, lush hand-painted backgrounds, warm pastoral light, whimsical nature",
    "gothic": "dark gothic atmosphere, moonlit cathedral shadows, ornate Victorian details, haunting ethereal mist",
    "dali": "Dalíesque surrealism, melting clocks, desert dreamscape, hyper-detailed impossible objects",
    "dreamlike": "ethereal dreamlike quality, soft focus transitions, floating weightlessness, liminal space aesthetics",
}

# 梦境情绪对应的视觉增强
MOOD_ENHANCEMENT = {
    "fantasy": "magical sparkling atmosphere, enchanted luminescence, fairy tale wonder",
    "peaceful": "serene tranquility, gentle ambient light, soft pastel harmony, meditative stillness",
    "scary": "ominous shadows, unsettling distortion, cold desaturated tones, creeping dread",
    "sad": "melancholic blue-grey palette, gentle rain, wilting elements, bittersweet nostalgia",
    "exciting": "dynamic energy, vibrant saturated colors, motion blur, explosive lighting",
    "romantic": "warm golden hour glow, soft bokeh, intimate close composition, rose-tinted atmosphere",
    "mysterious": "enigmatic deep shadows, fog-shrouded revelation, cryptic symbolism, twilight ambiguity",
    "nostalgic": "vintage color grading, warm film grain, faded edges, memory-like soft focus",
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
