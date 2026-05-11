"""
Auth Routes - 用户注册、登录、OAuth
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse, OAuthCallback
)
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """邮箱注册"""
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 创建用户
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        nickname=data.nickname or data.email.split("@")[0],
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 生成 token
    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """邮箱登录"""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: str = Depends(
        __import__("app.core.security", fromlist=["get_current_user"]).get_current_user
    ),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户信息"""
    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.get("/oauth/google/url")
async def google_oauth_url():
    """获取 Google OAuth 跳转 URL"""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
    )
    return {"url": url}


@router.post("/oauth/google", response_model=TokenResponse)
async def google_oauth_callback(data: OAuthCallback, db: AsyncSession = Depends(get_db)):
    """Google OAuth 回调处理"""
    import httpx

    # 用 code 换取 token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": data.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange OAuth code")
        tokens = token_resp.json()

        # 获取用户信息
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        userinfo = userinfo_resp.json()

    email = userinfo["email"]
    oauth_id = userinfo["id"]

    # 查找或创建用户
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            nickname=userinfo.get("name", email.split("@")[0]),
            avatar_url=userinfo.get("picture"),
            oauth_provider="google",
            oauth_id=oauth_id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )


@router.get("/oauth/github/url")
async def github_oauth_url():
    """获取 GitHub OAuth 跳转 URL"""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured")
    url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
    )
    return {"url": url}


@router.post("/oauth/github", response_model=TokenResponse)
async def github_oauth_callback(data: OAuthCallback, db: AsyncSession = Depends(get_db)):
    """GitHub OAuth 回调处理"""
    import httpx

    async with httpx.AsyncClient() as client:
        # 用 code 换取 token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": data.code,
            },
            headers={"Accept": "application/json"},
        )
        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to exchange OAuth code")

        # 获取用户信息
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo = user_resp.json()

        # 获取邮箱
        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        emails = email_resp.json()
        primary_email = next(
            (e["email"] for e in emails if e.get("primary")), None
        )

    email = primary_email or userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Unable to get email from GitHub")

    # 查找或创建用户
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            nickname=userinfo.get("login", email.split("@")[0]),
            avatar_url=userinfo.get("avatar_url"),
            oauth_provider="github",
            oauth_id=str(userinfo["id"]),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )
