# Dream Recorder - 梦境记录器 产品设计文档

## 产品概述

Dream Recorder 是一款 AI 驱动的梦境可视化应用。用户醒来后描述自己的梦境，AI 会将文字描述转化为精美的图片和视频，帮助用户"回放"和保存梦境。

灵感来源：MODEM 工作室的 Dream Recorder 概念产品。

---

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                    Frontend                          │
│         Next.js 14 + Tailwind CSS + Framer Motion   │
│         (暗色梦幻主题 / 紫蓝渐变风格)               │
└────────────────────────┬────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────┐
│                    Backend                           │
│              Python FastAPI + SQLAlchemy             │
│         JWT Auth / OAuth2 (Google & GitHub)          │
└────────┬───────────────┬───────────────┬────────────┘
         │               │               │
    ┌────▼────┐   ┌──────▼──────┐  ┌─────▼─────┐
    │PostgreSQL│   │ DashScope   │  │  OSS/S3   │
    │ Database │   │   AI API    │  │  Storage  │
    └─────────┘   └─────────────┘  └───────────┘
```

---

## 核心功能模块

### 1. 用户系统
- **注册**：邮箱 + 密码注册，邮箱验证
- **登录**：邮箱密码 / Google OAuth / GitHub OAuth
- **个人中心**：头像、昵称、梦境统计

### 2. 梦境记录
- **文字输入**：用户用文字描述梦境内容
- **AI 增强描述**：Qwen 模型自动优化和扩展用户的描述，生成更丰富的提示词
- **标签系统**：自动/手动标记梦境关键词（如：飞翔、追逐、水下等）
- **情绪标记**：记录梦境的情绪基调（奇幻、恐怖、温馨、悲伤等）

### 3. AI 生图（核心功能一）
使用阿里云万相 wan2.6-image 模型

**场景设计：**
| 场景 | 说明 | 风格参数 |
|------|------|---------|
| 梦境重现 | 还原梦中的主要场景 | 超现实主义 + 柔焦 |
| 梦中人物 | 生成梦中出现的角色 | 人像 + 幻想风 |
| 情绪画卷 | 基于梦境情绪生成抽象画 | 抽象表现主义 |
| 梦境符号 | 提取梦中象征物并可视化 | 符号主义 + 暗色调 |
| 平行梦境 | 同一梦境的多种视觉解读 | 多风格变体 |

**风格选项：**
- 水彩梦幻 (Watercolor Dreamscape)
- 赛博朋克 (Cyberpunk Dream)
- 古典油画 (Classical Painting)
- 超现实达利 (Surrealist Dalí)
- 宫崎骏风 (Ghibli Style)
- 暗黑哥特 (Dark Gothic)

### 4. AI 生视频（核心功能二）
使用阿里云万相 wan2.7-t2v 模型

**场景设计：**
| 场景 | 说明 | 时长 |
|------|------|------|
| 梦境回放 | 将整个梦境叙述转为短视频 | 5-10秒 |
| 梦境片段 | 聚焦梦中某个关键时刻 | 3-5秒 |
| 梦境循环 | 生成可循环播放的梦境动画 | 3-5秒 |
| 梦境延续 | "如果梦继续下去会怎样？" | 5-10秒 |
| 梦日记封面 | 为每日梦境生成动态封面 | 3秒 |

### 5. 梦境画廊
- **时间轴视图**：按日期排列的梦境记录
- **瀑布流画廊**：所有生成的图片/视频浏览
- **梦境日历**：日历视图标记有梦的日期
- **搜索和筛选**：按标签、情绪、日期筛选

### 6. 社交分享
- 生成分享卡片（图片 + 梦境摘要）
- 公开/私密设置
- 梦境社区广场（后期）

---

## 页面设计

### 页面清单
1. **Landing Page** - 产品介绍落地页
2. **登录/注册页** - 邮箱注册 + 社交登录
3. **主面板 (Dashboard)** - 最近梦境 + 快速记录入口
4. **梦境记录页** - 文字输入 + AI 生成选项
5. **生成结果页** - 查看 AI 生成的图片/视频
6. **梦境画廊** - 所有历史梦境浏览
7. **梦境详情页** - 单条梦境的完整内容
8. **个人中心** - 账号设置 + 统计

### UI 风格
- **色彩**：深空蓝（#0a0a1a）为底，紫罗兰渐变（#6366f1 → #a855f7）为强调色
- **字体**：中文思源黑体，英文 Inter/Outfit
- **动效**：微妙的星尘粒子背景 + 页面流畅过渡
- **卡片**：毛玻璃效果 (backdrop-blur) + 微光边框
- **整体氛围**：如同置身星空下的梦境世界

---

## API 设计

### 认证相关
```
POST /api/auth/register      - 邮箱注册
POST /api/auth/login         - 邮箱登录
POST /api/auth/oauth/google  - Google OAuth
POST /api/auth/oauth/github  - GitHub OAuth
GET  /api/auth/me            - 获取当前用户信息
```

### 梦境相关
```
POST   /api/dreams           - 创建梦境记录
GET    /api/dreams           - 获取梦境列表（分页）
GET    /api/dreams/{id}      - 获取梦境详情
PUT    /api/dreams/{id}      - 更新梦境
DELETE /api/dreams/{id}      - 删除梦境
```

### AI 生成相关
```
POST /api/generate/enhance   - AI 增强梦境描述
POST /api/generate/image     - 生成梦境图片
POST /api/generate/video     - 生成梦境视频
GET  /api/generate/task/{id} - 查询生成任务状态
```

### 用户相关
```
GET  /api/users/stats        - 用户统计
PUT  /api/users/profile      - 更新个人信息
```

---

## 数据库设计

### users 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| email | VARCHAR | 邮箱（唯一） |
| password_hash | VARCHAR | 密码哈希 |
| nickname | VARCHAR | 昵称 |
| avatar_url | VARCHAR | 头像 |
| oauth_provider | VARCHAR | OAuth 来源 |
| oauth_id | VARCHAR | OAuth ID |
| created_at | TIMESTAMP | 注册时间 |

### dreams 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户外键 |
| title | VARCHAR | 梦境标题 |
| content | TEXT | 梦境描述（原始） |
| enhanced_content | TEXT | AI 增强后的描述 |
| mood | VARCHAR | 情绪标记 |
| tags | JSONB | 标签数组 |
| is_public | BOOLEAN | 是否公开 |
| created_at | TIMESTAMP | 创建时间 |

### generations 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| dream_id | UUID | 梦境外键 |
| user_id | UUID | 用户外键 |
| type | VARCHAR | image / video |
| style | VARCHAR | 生成风格 |
| prompt | TEXT | 实际使用的提示词 |
| status | VARCHAR | pending/processing/completed/failed |
| task_id | VARCHAR | DashScope 任务ID |
| result_url | VARCHAR | 生成结果URL |
| metadata | JSONB | 元数据（分辨率等） |
| created_at | TIMESTAMP | 创建时间 |

---

## 阿里云 AI 模型配置

### 文本增强（Qwen）
- Endpoint: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions`
- Model: `qwen-plus`（可切换）
- 用途：优化用户的梦境描述，生成适合图像/视频模型的 prompt

### 图片生成（万相）
- Endpoint: `https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/image-generation/generation`
- Model: `wan2.6-image`
- 调用方式：异步（X-DashScope-Async: enable）
- 查询结果：GET `/api/v1/tasks/{task_id}`

### 视频生成（万相）
- Endpoint: `https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis`
- Model: `wan2.7-t2v-2026-04-25`
- 调用方式：异步（X-DashScope-Async: enable）
- 查询结果：GET `/api/v1/tasks/{task_id}`

---

## 开发计划

### Phase 1 - MVP Demo（当前）
- [x] 产品设计文档
- [ ] 前端页面基础框架
- [ ] 后端 API 基础框架
- [ ] 用户注册登录
- [ ] 梦境记录 CRUD
- [ ] AI 生图功能
- [ ] AI 生视频功能
- 不限制使用量

### Phase 2 - 完善
- [ ] 用量统计与额度系统
- [ ] 免费/付费额度切换
- [ ] 梦境社区广场
- [ ] 语音输入梦境
- [ ] 数据分析面板

### Phase 3 - 部署上线
- [ ] 阿里云资源开设
- [ ] CI/CD 配置
- [ ] 域名与 HTTPS
- [ ] 性能优化
