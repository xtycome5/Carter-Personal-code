import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON
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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    dream = relationship("Dream", back_populates="generations")
    user = relationship("User", back_populates="generations")
