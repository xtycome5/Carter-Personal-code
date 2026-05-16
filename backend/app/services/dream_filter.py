"""
Dream Filter Service - 梦境视频后处理

在视频生成完成后，通过 ffmpeg 应用梦境退化滤镜，
将清晰的 AI 生成视频转化为"记忆中的梦"的质感：
- 柔焦模糊（sigma=3.5）
- 柔光泛光（bloom screen blend）
- 胶片颗粒（temporal noise）
- 色彩加浓（saturation 1.25）
- 低帧率顿挫（8fps 原生输出）
- 暗角聚焦（vignette）

所有退化效果均由后处理完成，不需要在 prompt 中描述。
"""
import asyncio
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# Filter Chain Configuration
# ============================================================

DREAM_FILTER_CONFIG = {
    # 视觉效果
    "blur_sigma": 3.5,          # 主体柔焦强度
    "bloom_blur": 15,           # 泛光层模糊
    "bloom_brightness": 0.05,   # 泛光亮度提升
    "bloom_opacity": 0.15,      # 泛光混合透明度
    "noise_strength": 12,       # 胶片颗粒强度 (temporal)
    "saturation": 1.25,         # 色彩饱和度
    "contrast": 0.95,           # 对比度（略降）
    "vignette_angle": "PI/4",   # 暗角强度

    # 时间效果
    "output_fps": 8,            # 输出帧率（顿挫感）

    # 编码
    "crf": 22,                  # 视频质量 (lower = better)
    "preset": "medium",         # 编码速度/质量平衡
}


def build_filter_chain(config: dict = None) -> str:
    """构建 ffmpeg filter_complex 字符串"""
    c = config or DREAM_FILTER_CONFIG

    return (
        f"[0:v]split=2[base][glow];"
        f"[base]gblur=sigma={c['blur_sigma']}[blurred];"
        f"[glow]gblur=sigma={c['bloom_blur']},"
        f"eq=brightness={c['bloom_brightness']}[glowed];"
        f"[blurred][glowed]blend=all_mode=screen:"
        f"all_opacity={c['bloom_opacity']}[bloomed];"
        f"[bloomed]noise=alls={c['noise_strength']}:allf=t,"
        f"eq=saturation={c['saturation']}:contrast={c['contrast']},"
        f"fps={c['output_fps']},"
        f"vignette={c['vignette_angle']}"
    )


async def apply_dream_filter_to_url(
    video_url: str,
    output_path: str,
    config: dict = None,
) -> str:
    """
    从 URL 下载视频并应用梦境滤镜

    ffmpeg 可以直接读取 URL，无需先下载

    Args:
        video_url: 视频 URL（DashScope 返回的临时 URL）
        output_path: 输出文件路径
        config: 滤镜参数配置

    Returns:
        输出文件路径
    """
    c = config or DREAM_FILTER_CONFIG
    filter_chain = build_filter_chain(c)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_url,
        "-filter_complex", filter_chain,
        "-c:v", "libx264",
        "-preset", c.get("preset", "medium"),
        "-crf", str(c.get("crf", 22)),
        "-r", str(c["output_fps"]),
        "-an",
        output_path,
    ]

    logger.info(f"[DreamFilter] Processing URL -> {output_path}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode()[-500:] if stderr else "Unknown error"
        logger.error(f"[DreamFilter] ffmpeg failed: {error_msg}")
        if os.path.exists(output_path):
            os.remove(output_path)
        raise RuntimeError(f"Dream filter failed: {error_msg}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"[DreamFilter] Done. Output: {output_path} ({size_mb:.1f}MB)")

    return output_path
