import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # nullable for OAuth users
    nickname = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    oauth_provider = Column(String(50), nullable=True)  # google, github
    oauth_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    dreams = relationship("Dream", back_populates="user", cascade="all, delete-orphan")
    generations = relationship("Generation", back_populates="user", cascade="all, delete-orphan")


class Dream(Base):
    __tablename__ = "dreams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)  # 用户原始描述
    enhanced_content = Column(Text, nullable=True)  # AI 增强后的描述
    mood = Column(String(50), nullable=True)  # 情绪标记
    tags = Column(JSON, default=list)  # 标签数组
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="dreams")
    generations = relationship("Generation", back_populates="dream", cascade="all, delete-orphan")


class Generation(Base):
    __tablename__ = "generations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dream_id = Column(UUID(as_uuid=True), ForeignKey("dreams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)  # image / video
    style = Column(String(100), nullable=True)  # 生成风格
    prompt = Column(Text, nullable=False)  # 实际使用的提示词
    negative_prompt = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending/processing/completed/failed
    task_id = Column(String(255), nullable=True)  # DashScope 任务ID
    result_url = Column(String(1000), nullable=True)  # 生成结果URL
    metadata_json = Column(JSON, default=dict)  # 元数据
    # Gallery审核字段
    featured = Column(Boolean, default=False, index=True)  # 是否上架到Gallery
    featured_at = Column(DateTime(timezone=True), nullable=True)  # 上架时间（用于排序）
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    dream = relationship("Dream", back_populates="generations")
    user = relationship("User", back_populates="generations")


class Artist(Base):
    """画家池 — 用于 prompt expansion 的美学参考"""
    __tablename__ = "artists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(50), unique=True, nullable=False, index=True)  # 唯一标识: DALI, MAGRITTE...
    name = Column(String(200), nullable=False)  # 显示名: Salvador Dalí
    style = Column(Text, nullable=False)  # 风格描述 (用于 system prompt)
    masterwork_url = Column(String(1000), nullable=True)  # 参考图 OSS URL
    painting = Column(String(300), nullable=True)  # 代表作名称
    category = Column(String(100), nullable=True)  # 分类: surrealism_core, expressionism...
    active = Column(Boolean, default=True, index=True)  # 是否启用
    sort_order = Column(Integer, default=0)  # 排序（同 category 内）
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ApiCallLog(Base):
    """DashScope API 调用日志 — 用于模型监控面板"""
    __tablename__ = "api_call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model = Column(String(100), nullable=False, index=True)  # qwen-plus, wan2.7-image-pro, happyhorse-1.0-r2v
    endpoint = Column(String(100), nullable=False)  # creative_director, prompt_expansion, image_generation, video_generation
    method = Column(String(10), default="POST")  # POST, GET
    status = Column(String(20), nullable=False)  # success, failed, timeout
    duration_ms = Column(Integer, nullable=False, default=0)  # 调用耗时(毫秒)
    tokens_input = Column(Integer, default=0)  # 输入 tokens（LLM 类）
    tokens_output = Column(Integer, default=0)  # 输出 tokens（LLM 类）
    error = Column(Text, nullable=True)  # 错误信息
    request_payload = Column(JSON, nullable=True)  # 请求摘要（不含完整 prompt，只存 model/size 等）
    response_summary = Column(JSON, nullable=True)  # 响应摘要（task_id/image_url 前缀等）
    user_id = Column(UUID(as_uuid=True), nullable=True)  # 触发调用的用户（可选）
    generation_id = Column(UUID(as_uuid=True), nullable=True)  # 关联的 Generation（可选）
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
