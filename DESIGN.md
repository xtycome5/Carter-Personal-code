# Dream Recorder - 产品设计文档

## 产品定位

Dream Recorder 是一款 AI 梦境可视化工具。用户输入梦境文字描述，系统自动生成超现实风格的绘画和电影级视频。

定位：纯梦境场景，非通用创作工具。

## 设计语言

参考 wan.video (create.wan.video) 的 professional dark SaaS 风格。

### 色彩系统

| Token | Value | Usage |
|-------|-------|-------|
| --bg-primary | #0c0c14 | 页面背景 |
| --bg-secondary | #14141f | 侧边栏/次级区域 |
| --bg-elevated | #1a1a2e | 弹层/卡片内层 |
| --bg-card | #1e1e32 | 卡片背景 |
| --accent | #7c5cfc | 主强调色 |
| --accent-glow | rgba(124,92,252,0.15) | 发光效果 |
| --border-subtle | rgba(255,255,255,0.06) | 细微边框 |
| --border-hover | rgba(255,255,255,0.12) | 悬停边框 |
| --text-primary | #f0f0f5 | 主文字 |
| --text-secondary | #9ca3af | 次级文字 |
| --text-muted | #6b7280 | 辅助文字 |

### 设计原则

- 干净现代 SaaS 感，不要 glass-morphism、不要粒子效果
- 大留白、宽松间距
- 圆角 12-16px
- 微妙的 border 区分层级，不用阴影
- 动效克制：仅 framer-motion 入场淡入，不做复杂动画

## 页面路由

| 路由 | 功能 | 状态 |
|------|------|------|
| `/` | 重定向（登录→/create，未登录→/auth） | ✅ |
| `/auth` | 登录/注册（分屏布局：左渐变艺术图，右表单） | ✅ |
| `/create` | 主页：梦境输入 + Daily Top 20 占位 | ✅ |
| `/dreams` | My Dreams 网格列表 | ✅ |
| `/dreams/[id]` | 梦境详情（图片+视频并排，文字在下） | ✅ |
| `/explore` | Daily Top 20 画廊 | 占位 |
| `/favorites` | 收藏 | 占位 |

## 布局结构

### 全局布局
- 左侧固定侧边栏：72px 宽，icon-only，深色背景
- 图标：Create / Explore / My Dreams / Favorites
- 底部：用户头像 + 登出
- 主内容区：`margin-left: 72px`，自适应宽度

### /auth 登录页
- 分屏：左 45% 渐变艺术大图，右 55% 表单
- 表单：Email + Password → 登录按钮 → OR 分隔线 → Google + GitHub
- 深色背景，无侧边栏

### /create 主页
- Hero 区："Visualize Your Dreams" + 描述输入框
- 输入区：大文本框 + Generate 按钮
- 下方：Daily Top 20 画廊区域（占位）

### /dreams/[id] 详情页
- 上方两栏并排（1:1 比例）：
  - 左 = 图片（有图显示，无图则"Generate Image"按钮）
  - 右 = 视频框（始终显示）：
    - 有视频 → 播放器
    - 有图无视频 → 框内"Bring it to life" CTA 按钮
    - 无图 → 灰色"先生成图片"提示
- 下方：
  - 左 = 用户原始描述 + AI Creative Brief
  - 右 = Regenerate 按钮 + About 信息卡

## AI 生成流程

### 用户操作流

```
用户输入文字 → 点击 Generate
    → 后端自动执行 Prompt Pipeline
    → 返回 generation_id
    → 前端轮询 task status (每 5 秒)
    → SUCCEEDED → 展示图片
    → 用户点击视频框 CTA → 生成 R2V 视频
    → 轮询完成 → 展示视频
```

### Prompt Pipeline 详解

**Call 1: Creative Director Agent**
- 模型：qwen-plus, temperature 0.7
- 输入：用户原始梦境文字
- 输出：DreamAnalysis JSON（18 个字段）
  - emotion, intensity, color_palette, lighting, time_of_day
  - weather_atmosphere, spatial_scale, camera_perspective
  - subjects, background_elements, textures_materials
  - movement_quality, sound_suggestion, symbolic_elements
  - compositional_focus, contrast_pairs, narrative_arc, overall_mood
- 约束：response_format = json_object，确保结构化输出

**Call 2: Prompt Expansion**
- 模型：qwen-plus, temperature 0.85
- Image prompt：
  - 从 18 画家池随机取 3 位
  - 动态构建 system prompt，融合画家风格描述
  - 输出：英文绘画提示词（存入 dream.enhanced_content）
- Video prompt：
  - FPV（第一人称视角）系统约束
  - 禁止出现人体部位（手、脚、手臂等）
  - 摄影语言：镜头mm、运动速度、色温、烟雾密度%
  - 输出：英文电影运动提示词（存入 generation.prompt）

### 画家池 (18 位)

| 分类 | 画家 |
|------|------|
| 超现实核心 | Dalí, Magritte, Ernst, Varo, Carrington |
| 表现主义/扭曲 | Munch, Schiele, Bacon |
| 诗意失重 | Chagall, Redon, Klimt, Mucha |
| 神秘象征 | Bosch, Blake, Beksiński |
| 现代梦幻 | Kusama, de Chirico, Sage |

每次生图随机取 3 位，无权重（均匀随机）。未来通过 B 端后台管理增删。

### 生成模型

| 用途 | 模型 | 参数 |
|------|------|------|
| 文生图 | wan2.7-image | 1024x1024 |
| 参考生图 | wan2.7-image-pro | reference + prompt |
| 参考生视频 | happyhorse-1.0-r2v | 10s, 720P, FPV |

注意：不再支持 T2V（文生视频）。所有视频必须基于已生成的图片作为参考。

## 存储架构

### OSS Bucket

- Bucket: `dream-recorder-media`
- Region: ap-southeast-5 (Jakarta)
- ACL: public-read
- 路径: `images/{user_id}/{generation_id}.png`, `videos/{user_id}/{generation_id}.mp4`

### 持久化流程

```
DashScope 生成完成（SUCCEEDED）
    → 返回临时 URL（24h 内过期）
    → storage_service.persist():
        1. httpx 下载到内存
        2. oss2 上传到 bucket
        3. 返回永久 public URL
    → 更新 generation.result_url
```

## API 接口

### 认证

```
POST /api/auth/register          注册（email + password）
POST /api/auth/login             登录 → JWT token
GET  /api/auth/me                当前用户信息
GET  /api/auth/oauth/google      Google OAuth 跳转
GET  /api/auth/oauth/github      GitHub OAuth 跳转
```

### 梦境

```
POST   /api/dreams               创建梦境
GET    /api/dreams               列表（分页，返回 {dreams: [...], total, page}）
GET    /api/dreams/{id}          详情（含 generations 数组）
PUT    /api/dreams/{id}          更新
DELETE /api/dreams/{id}          删除
```

### 生成

```
POST /api/generate/enhance       预览 AI 扩写
POST /api/generate/image         生成图片（自动执行 prompt pipeline）
POST /api/generate/video         生成视频（需先有完成的图片，否则 400）
GET  /api/generate/task/{id}     轮询任务状态
```

## 数据库模型

### users
- id (UUID), email, password_hash, nickname, avatar_url
- oauth_provider, oauth_id, created_at

### dreams
- id (UUID), user_id (FK), title, content, enhanced_content
- mood, tags (JSONB), is_public, created_at

### generations
- id (UUID), dream_id (FK), user_id (FK)
- type (image/video), style, prompt, negative_prompt
- status (processing/completed/failed), task_id, result_url
- metadata_json (JSONB: size, mode, duration, reference_image...)
- created_at

## 开发规划

### 已完成 (Phase 1)
- [x] 用户系统（Email + JWT + Google + GitHub OAuth）
- [x] 梦境 CRUD
- [x] Creative Director Agent（意图分析 + 结构化输出）
- [x] 18 画家池 + 随机 3-pick
- [x] FPV 视频约束（无身体部位）
- [x] Image-first flow（必须先生图再生视频）
- [x] OSS 永久存储
- [x] C 端 UI 重设计（wan.video 风格）
- [x] 部署上线（ECS + Nginx）

### 进行中 (Phase 2)
- [ ] Daily Top 20 后端 API（人工筛选或自动评分）
- [ ] Favorites 功能
- [ ] 域名 DNS 修复 (dreamrecorder.xyz)
- [ ] 进程管理（systemd 或 pm2）

### 规划中 (Phase 3)
- [ ] B 端管理后台（Vite + Ant Design）
  - 画家池增删管理
  - 内容审核
  - 用户管理
- [ ] 用量统计 & 额度系统
- [ ] 梦境社区广场
- [ ] 语音输入
