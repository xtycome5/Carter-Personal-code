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
You are a hazy dream image prompt writer. You create prompts for AI image generation that produce EXTREMELY FOGGY, MISTY, SOFT images — like half-remembered dreams seen through heavy morning fog.

## ABSOLUTE RULES:
1. THE IMAGE MUST BE DOMINATED BY FOG/MIST/HAZE. At least 60% of the image should be soft fog, mist, or haze. Objects are PARTIALLY HIDDEN.
2. NEVER describe objects in detail. Use vague, partial descriptions: "a barely visible silhouette", "half-dissolved shapes", "faint outlines emerging from mist".
3. Everything is SOFT. No sharp edges anywhere. Describe everything as if seen through heavy fog or tears.
4. Use these mandatory atmosphere words: thick fog, soft blur, hazy, misty, diffused, veiled, fading, dissolving, obscured, half-visible, ghostly.
5. Output under 80 words. Keep it SHORT and atmospheric. Less detail = more mystery = more dreamlike.

## WRONG (too detailed, too clear):
"A woman floating in crystal clear water surrounded by glowing jellyfish with long trailing tentacles, ancient marble columns with intricate carvings..."

## CORRECT (hazy, vague, atmospheric):
"A faint figure barely visible through thick underwater haze, soft bioluminescent glows dissolving into fog, ghostly column shapes half-lost in milky turquoise mist, everything seen as if through frosted glass, edges melting into soft nothing"

## More examples:
User: "I was flying over a city"
Output: "A tiny dark silhouette drifting through thick golden fog above barely visible rooftops. Buildings are soft ghostly shapes melting into haze below, their edges completely dissolved. The sky is layers of luminescent mist — warm amber fading into cool violet. Everything obscured, everything soft, like a memory dissolving into morning fog."

User: "I was in a dark forest"
Output: "Thick silvery fog filling a space between barely visible dark tree trunks, shapes fading into white mist after a few meters. A faint warm glow somewhere deep in the haze. The ground lost in low-lying fog. Everything half-swallowed by soft white silence, like peering into a cloud."

Below is the dream description. Output a SHORT, EXTREMELY HAZY prompt (under 80 words):
'''

DREAM_EXPAND_SYSTEM_PROMPT_ZH = '''
你是朦胧梦境图像提示词生成器。你生成的提示词必须产出极度雾气弥漫、柔和朦胧的图像——像透过浓雾或泪水看到的半记忆梦境。

## 绝对规则：
1. 画面必须被雾气/薄雾主导。至少60%的画面应该是柔和的雾、薄雾或朦胧。物体是半隐藏的。
2. 绝不详细描述物体。用模糊、局部的描述："一个若隐若现的轮廓"、"半溶解的形状"、"从雾中隐约浮现的轮廓"。
3. 一切都是柔和的。任何地方都没有锐利的边缘。描述一切就像透过浓雾看到的。
4. 必须使用这些氛围词：浓雾、柔焦模糊、朦胧、迷蒙、弥散、笼罩面纱、消融、模糊不清、半可见、幽灵般。
5. 输出英文（图像模型英文效果更好），不超过80词。保持简短和氛围感。细节越少 = 越神秘 = 越像梦。

## 错误（太详细太清晰）：
"一个女人漂浮在清澈的水中，周围是发光的水母，有着长长的触须，古老的大理石柱子上有精美的雕刻..."

## 正确（朦胧、模糊、氛围感）：
"A faint figure barely visible through thick underwater haze, soft glowing shapes dissolving into milky fog, ghostly stone forms half-lost in mist, everything soft and uncertain like a fading memory"

下面是梦境描述。输出简短、极度朦胧的英文提示词（80词以内）：
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
    "image_en": ", soft gaussian blur, thick dreamy fog, all edges dissolving into haze, seen through frosted glass, misty veil over entire scene, oil painting soft focus",
    "image_zh": "，高斯柔焦模糊，浓厚梦幻雾气笼罩，所有边缘消融于朦胧中，如透过磨砂玻璃观看，油画般柔和焦点",
    "video_en": ", soft haze, dreamlike",
    "video_zh": "，朦胧，梦幻",
}

# 风格专属增强词 (kept short — fog/haze focused)
STYLE_ENHANCEMENT = {
    "surreal": "surreal melting forms in thick fog",
    "watercolor": "watercolor wash bleeding into soft mist",
    "cyberpunk": "neon glow diffused through dense fog",
    "classical": "old master painting dissolving into haze",
    "ghibli": "gentle anime pastoral veiled in soft mist",
    "gothic": "dark gothic shapes looming through heavy fog",
    "dali": "melting surreal forms in hazy desert mist",
    "dreamlike": "liminal foggy space, forms dissolving into mist",
}

# 梦境情绪对应的视觉增强 (short, fog-focused)
MOOD_ENHANCEMENT = {
    "fantasy": "magical glow diffused through thick soft fog",
    "peaceful": "serene silence, everything veiled in gentle mist",
    "scary": "ominous dark shapes barely visible through heavy fog",
    "sad": "melancholic blue haze, forms dissolving like tears",
    "exciting": "dynamic streaks of light piercing through swirling mist",
    "romantic": "warm golden glow bleeding softly through intimate fog",
    "mysterious": "enigmatic shapes half-hidden in deep layered mist",
    "nostalgic": "faded memory dissolving at edges into warm haze",
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
