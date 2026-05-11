from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============ Auth Schemas ============

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    nickname: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class OAuthCallback(BaseModel):
    code: str
    state: Optional[str] = None


# ============ User Schemas ============

class UserResponse(BaseModel):
    id: UUID
    email: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


# ============ Dream Schemas ============

class DreamCreate(BaseModel):
    title: Optional[str] = None
    content: str
    mood: Optional[str] = None
    tags: Optional[List[str]] = []
    is_public: Optional[bool] = False


class DreamUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class DreamResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    content: str
    enhanced_content: Optional[str] = None
    mood: Optional[str] = None
    tags: List[str] = []
    is_public: bool = False
    created_at: datetime
    generations: List["GenerationResponse"] = []

    class Config:
        from_attributes = True


class DreamListResponse(BaseModel):
    dreams: List[DreamResponse]
    total: int
    page: int
    page_size: int


# ============ Generation Schemas ============

class GenerateImageRequest(BaseModel):
    dream_id: UUID
    style: Optional[str] = "surreal"  # 风格选项
    negative_prompt: Optional[str] = None
    size: Optional[str] = "1024*1024"  # 分辨率
    count: Optional[int] = 1  # 生成数量 1-4


class GenerateVideoRequest(BaseModel):
    dream_id: UUID
    style: Optional[str] = "dreamlike"
    resolution: Optional[str] = "720P"
    duration: Optional[int] = 5  # 秒数 2-15
    ratio: Optional[str] = "16:9"


class EnhanceRequest(BaseModel):
    dream_id: UUID
    style: Optional[str] = None  # 可指定增强方向


class GenerationResponse(BaseModel):
    id: UUID
    dream_id: UUID
    type: str
    style: Optional[str] = None
    prompt: str
    status: str
    task_id: Optional[str] = None
    result_url: Optional[str] = None
    metadata_json: Optional[dict] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    id: UUID
    status: str
    result_url: Optional[str] = None
    type: str
