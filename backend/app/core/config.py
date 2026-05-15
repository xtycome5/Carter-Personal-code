from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "DreamRecorder"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/dreamrecorder"

    # DashScope AI
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope-intl.aliyuncs.com"
    QWEN_MODEL: str = "qwen-plus"
    QWEN_VIDEO_PROMPT_MODEL: str = "qwen-plus"  # 视频提示词专用，可单独升级
    IMAGE_MODEL: str = "wan2.7-image-pro"
    IMAGE_PRO_MODEL: str = "wan2.7-image-pro"  # 参考生图也用同一模型
    VIDEO_MODEL: str = "happyhorse-1.0-t2v"
    VIDEO_I2V_MODEL: str = "happyhorse-1.0-i2v"
    VIDEO_R2V_MODEL: str = "happyhorse-1.0-r2v"

    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/auth/callback/google"
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: str = "http://localhost:3000/api/auth/callback/github"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Alibaba Cloud OSS
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_ENDPOINT: str = "https://oss-ap-southeast-5.aliyuncs.com"  # Jakarta, same region as ECS
    OSS_BUCKET_NAME: str = "dream-recorder-media"
    OSS_CUSTOM_DOMAIN: str = ""  # Optional: CDN domain like "media.dreamrecorder.xyz"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
