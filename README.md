# Dream Recorder

AI-powered dream visualization. Describe your dream, get surreal paintings and cinematic videos.

## Tech Stack

- **Frontend**: Next.js 16 + TypeScript + Tailwind CSS + Framer Motion
- **Backend**: Python FastAPI + SQLAlchemy + PostgreSQL
- **AI Pipeline**: Alibaba Cloud DashScope (Qwen-Plus + Wan2.7-Image + HappyHorse R2V)
- **Storage**: Alibaba Cloud OSS (permanent media storage)
- **Auth**: JWT + OAuth2 (Google / GitHub)
- **Server**: Alibaba Cloud ECS (Jakarta), Nginx reverse proxy

## Architecture

```
User → Next.js (port 3000) → Nginx (port 80) → FastAPI (port 8000)
                                                       │
                              ┌─────────────────────────┼──────────────────┐
                              │                         │                  │
                         PostgreSQL              DashScope API         OSS Bucket
                         (dreamrecorder)         (AI generation)      (dream-recorder-media)
```

### AI Prompt Pipeline (Two-Step)

```
User dream text
    │
    ▼
[Call 1] Creative Director Agent (qwen-plus, temp 0.7)
    → Analyzes intent, emotion, fills visual gaps
    → Outputs structured DreamAnalysis JSON (18 fields)
    │
    ▼
[Call 2] Prompt Expansion (qwen-plus, temp 0.85)
    → Image: random 3-pick from 18-artist pool → surreal painting prompt
    → Video: FPV camera constraints → cinematic motion prompt
    │
    ▼
[Generation] Wan2.7-Image (text-to-image) → HappyHorse R2V (reference-to-video, 10s)
    │
    ▼
[Storage] DashScope temp URL → download → upload to OSS → permanent public URL
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in: DATABASE_URL, DASHSCOPE_API_KEY, OSS credentials

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

## Project Structure

```
Dream Recorder/
├── README.md
├── DESIGN.md
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── auth.py              # Login/register, OAuth callbacks
│   │   │   ├── dreams.py            # Dream CRUD + list (paginated)
│   │   │   └── generate.py          # Image/video generation + task polling
│   │   ├── core/
│   │   │   ├── config.py            # Settings (DB, DashScope, OSS, OAuth)
│   │   │   └── security.py          # JWT token handling
│   │   ├── db/session.py            # Async SQLAlchemy session
│   │   ├── models/models.py         # User, Dream, Generation ORM models
│   │   ├── schemas/schemas.py       # Pydantic request/response schemas
│   │   └── services/
│   │       ├── ai_service.py        # DashScope API calls (image/video/LLM)
│   │       ├── creative_director.py # Call 1: intent analysis → DreamAnalysis JSON
│   │       ├── prompt_expansion.py  # Call 2: artist pool + FPV → final prompt
│   │       └── storage_service.py   # OSS persist (temp URL → permanent)
│   ├── scripts/
│   │   └── migrate_to_oss.py       # Batch migrate old URLs to OSS
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/
        │   ├── page.tsx             # Redirect (→ /create or → /auth)
        │   ├── auth/page.tsx        # Split-screen login (Email + Google + GitHub)
        │   ├── create/page.tsx      # Main page: dream input + Daily Top 20
        │   ├── dreams/page.tsx      # My Dreams grid
        │   ├── dreams/[id]/page.tsx # Dream detail (image + video side by side)
        │   ├── explore/page.tsx     # Explore (placeholder)
        │   ├── favorites/page.tsx   # Favorites (placeholder)
        │   ├── globals.css          # Design system CSS variables
        │   └── layout.tsx           # Root layout + Sidebar
        ├── components/layout/
        │   ├── Sidebar.tsx          # Left icon sidebar (72px)
        │   └── AuthProvider.tsx     # Auth state + route protection
        ├── lib/api.ts               # API client (fetch wrapper)
        └── stores/authStore.ts      # Zustand auth store (persist)
```

## Key Features

### 18-Artist Pool (Random 3-Pick)
Each image generation randomly samples 3 artists from a curated pool of 18 dream/surreal painters (Dalí, Magritte, Chagall, Munch, Klimt, Kusama, etc.). This produces varied aesthetics while maintaining consistent surreal quality.

### FPV Video (First-Person View)
Video generation uses a "disembodied floating consciousness" perspective — no human subject, no hands/body. The camera IS the dreamer's eyes. This avoids gender appearance issues and keeps videos consistent with the surreal painting.

### Image-First Flow
Users must generate an image before video. Video uses R2V (Reference-to-Video) with the image as reference, preserving the painterly aesthetic instead of creating photorealistic output.

### OSS Permanent Storage
DashScope returns temporary URLs that expire within hours. The system automatically downloads results and persists them to Alibaba Cloud OSS with permanent public URLs.

## Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dreamrecorder

# DashScope AI
DASHSCOPE_API_KEY=sk-xxx
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com

# OSS Storage
OSS_ACCESS_KEY_ID=LTAI5t...
OSS_ACCESS_KEY_SECRET=xxx
OSS_ENDPOINT=https://oss-ap-southeast-5.aliyuncs.com
OSS_BUCKET_NAME=dream-recorder-media

# OAuth (optional)
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx

# App
SECRET_KEY=your-secret
FRONTEND_URL=http://localhost:3000
```

## Deployment (Production)

Server: Alibaba Cloud ECS (147.139.134.10), Jakarta region

```bash
# Pull latest
cd /opt/dream-recorder && git pull

# Backend
cd backend && source venv/bin/activate
pip install -r requirements.txt
pkill -f uvicorn
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &

# Frontend
cd ../frontend && npm run build
pkill -f next-server
nohup npm exec next start -- -p 3000 > /tmp/frontend.log 2>&1 &
```

Nginx proxies port 80 → frontend (3000), `/api/` → backend (8000).

## Roadmap

- [x] Core AI pipeline (Creative Director + Prompt Expansion + Image + Video)
- [x] 18-artist pool with random sampling
- [x] FPV video generation (R2V only)
- [x] OSS permanent storage
- [x] C-end redesign (wan.video-inspired dark SaaS aesthetic)
- [ ] Fix /dreams page crash (API response parsing)
- [ ] Daily Top 20 explore gallery (backend curation API)
- [ ] Favorites feature
- [ ] B-end admin panel (Vite + Ant Design) for artist pool management
- [ ] Process manager (systemd/pm2) for production stability
- [ ] Domain DNS fix (dreamrecorder.xyz)
