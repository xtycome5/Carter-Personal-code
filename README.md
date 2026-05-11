# Dream Recorder - 梦境记录器

AI 驱动的梦境可视化应用。描述你的梦，AI 帮你生成精美图片和视频。

## 技术栈

- **前端**: Next.js 15 + TypeScript + Tailwind CSS + Framer Motion
- **后端**: Python FastAPI + SQLAlchemy + PostgreSQL
- **AI**: 阿里云百炼 DashScope API (Qwen + 万相)
- **认证**: JWT + OAuth2 (Google / GitHub)

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 复制环境变量文件
cp backend/.env.example backend/.env

# 2. 编辑 .env 文件，填入你的 DashScope API Key
# DASHSCOPE_API_KEY=your-api-key-here

# 3. 启动所有服务
docker-compose up -d

# 前端: http://localhost:3000
# 后端: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 方式二：手动启动

#### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入配置

# 确保 PostgreSQL 运行中，且创建了 dreamrecorder 数据库
# createdb dreamrecorder

# 启动
uvicorn app.main:app --reload --port 8000
```

#### 前端

```bash
cd frontend
npm install

# 配置 API 地址
cp .env.local.example .env.local

# 启动开发服务器
npm run dev
```

## 项目结构

```
Dream Recorder/
├── DESIGN.md                 # 产品设计文档
├── docker-compose.yml        # Docker 编排
├── backend/                  # Python FastAPI 后端
│   ├── app/
│   │   ├── api/routes/       # API 路由
│   │   │   ├── auth.py       # 认证接口
│   │   │   ├── dreams.py     # 梦境 CRUD
│   │   │   └── generate.py   # AI 生成
│   │   ├── core/             # 配置 & 安全
│   │   ├── db/               # 数据库连接
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── schemas/          # Pydantic 模型
│   │   ├── services/         # AI 服务封装
│   │   └── main.py           # 入口
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/                 # Next.js 前端
    ├── src/
    │   ├── app/              # 页面
    │   │   ├── page.tsx      # 落地页
    │   │   ├── auth/         # 登录注册
    │   │   ├── dashboard/    # 仪表板
    │   │   ├── record/       # 记录梦境
    │   │   ├── dreams/[id]/  # 梦境详情
    │   │   └── gallery/      # 画廊
    │   ├── components/       # 组件
    │   ├── lib/              # API 封装
    │   └── stores/           # 状态管理
    ├── tailwind.config.ts
    └── Dockerfile
```

## AI 功能说明

### 文本增强（Qwen）
用户输入的梦境描述 → Qwen 模型优化为英文 Prompt → 用于图片/视频生成

### 图片生成（万相 wan2.6-image）
支持 6 种风格：超现实、水彩、赛博朋克、古典油画、宫崎骏、暗黑哥特

### 视频生成（万相 wan2.7-t2v）
支持 720P/1080P，2-15 秒时长，多种画面比例

## 后续计划

- [ ] 用量统计 & 额度系统（免费/付费）
- [ ] 梦境社区广场
- [ ] 语音输入
- [ ] 阿里云部署（ECS + RDS + OSS）
