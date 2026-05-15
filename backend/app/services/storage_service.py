"""
OSS Storage Service - 阿里云对象存储
负责：下载 DashScope 临时 URL → 上传到 OSS → 返回永久 URL

Bucket 结构:
  dream-recorder-media/
    images/{user_id}/{generation_id}.{ext}
    videos/{user_id}/{generation_id}.{ext}
"""
import io
import logging
from typing import Optional
from urllib.parse import urlparse
import httpx
import oss2

from app.core.config import settings

logger = logging.getLogger(__name__)


class OSSStorageService:
    def __init__(self):
        self._bucket: Optional[oss2.Bucket] = None

    @property
    def bucket(self) -> oss2.Bucket:
        if self._bucket is None:
            auth = oss2.Auth(
                settings.OSS_ACCESS_KEY_ID,
                settings.OSS_ACCESS_KEY_SECRET,
            )
            self._bucket = oss2.Bucket(
                auth,
                settings.OSS_ENDPOINT,
                settings.OSS_BUCKET_NAME,
            )
        return self._bucket

    @property
    def enabled(self) -> bool:
        """Check if OSS is configured"""
        return bool(
            settings.OSS_ACCESS_KEY_ID
            and settings.OSS_ACCESS_KEY_SECRET
            and settings.OSS_BUCKET_NAME
        )

    def _get_extension(self, url: str, media_type: str) -> str:
        """Infer file extension from URL or media type"""
        path = urlparse(url).path.lower()
        if path.endswith(".png"):
            return "png"
        elif path.endswith(".jpg") or path.endswith(".jpeg"):
            return "jpg"
        elif path.endswith(".webp"):
            return "webp"
        elif path.endswith(".mp4"):
            return "mp4"
        elif path.endswith(".mov"):
            return "mov"
        # Default by type
        return "png" if media_type == "image" else "mp4"

    def _build_key(self, user_id: str, generation_id: str, media_type: str, ext: str) -> str:
        """Build OSS object key: images/{user_id}/{gen_id}.ext"""
        folder = "images" if media_type == "image" else "videos"
        return f"{folder}/{user_id}/{generation_id}.{ext}"

    def _get_public_url(self, key: str) -> str:
        """Get public URL for an uploaded object"""
        if settings.OSS_CUSTOM_DOMAIN:
            return f"https://{settings.OSS_CUSTOM_DOMAIN}/{key}"
        return f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT.replace('https://', '').replace('http://', '')}/{key}"

    async def persist(
        self,
        temp_url: str,
        user_id: str,
        generation_id: str,
        media_type: str,  # "image" or "video"
    ) -> Optional[str]:
        """
        Download from temp URL and upload to OSS.
        Returns permanent OSS URL, or None if failed/not configured.
        """
        if not self.enabled:
            logger.warning("[OSS] Not configured, skipping persist")
            return None

        if not temp_url:
            return None

        # Skip if already an OSS URL
        if settings.OSS_BUCKET_NAME in temp_url:
            logger.info(f"[OSS] URL already on OSS, skipping: {temp_url[:60]}")
            return temp_url

        try:
            # Download from DashScope temp URL
            logger.info(f"[OSS] Downloading from temp URL: {temp_url[:80]}...")
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(temp_url)
                response.raise_for_status()
                content = response.content
                content_type = response.headers.get("content-type", "")

            # Determine extension
            ext = self._get_extension(temp_url, media_type)
            if "jpeg" in content_type or "jpg" in content_type:
                ext = "jpg"
            elif "png" in content_type:
                ext = "png"
            elif "webp" in content_type:
                ext = "webp"
            elif "mp4" in content_type:
                ext = "mp4"

            # Build key and upload
            key = self._build_key(user_id, generation_id, media_type, ext)
            logger.info(f"[OSS] Uploading {len(content)} bytes to: {key}")

            # Upload with correct content-type
            headers = {}
            if media_type == "image":
                headers["Content-Type"] = f"image/{ext}"
            else:
                headers["Content-Type"] = "video/mp4"

            self.bucket.put_object(key, io.BytesIO(content), headers=headers)

            # Return permanent URL
            permanent_url = self._get_public_url(key)
            logger.info(f"[OSS] Persisted: {permanent_url[:80]}")
            return permanent_url

        except httpx.HTTPStatusError as e:
            logger.error(f"[OSS] Download failed (HTTP {e.response.status_code}): {temp_url[:60]}")
            return None
        except Exception as e:
            logger.error(f"[OSS] Persist failed: {e}")
            return None


# Singleton
oss_storage_service = OSSStorageService()
