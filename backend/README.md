# Backend - Dream Recorder API

## Tech Stack
- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic (PostgreSQL)
- Pydantic v2
- python-jose (JWT)
- httpx (async HTTP client for DashScope API)
- passlib + bcrypt (password hashing)

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 配置环境变量
alembic upgrade head  # 初始化数据库
uvicorn app.main:app --reload --port 8000
```

## Environment Variables
See `.env.example` for required configuration.
