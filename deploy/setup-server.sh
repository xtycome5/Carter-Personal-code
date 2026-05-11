#!/bin/bash
# ============================================================
# Dream Recorder - 服务器初始化 & 应用部署脚本
# 
# 在 ECS 上运行此脚本完成：
# 1. 安装 Docker + Docker Compose
# 2. 安装 PostgreSQL
# 3. 克隆代码 & 配置环境
# 4. 启动服务
#
# 用法: ssh root@YOUR_IP 'bash -s' < deploy/setup-server.sh
# 或者: 拷贝到服务器后运行
# ============================================================

set -e

PROJECT_DIR="/opt/dreamrecorder"
REPO_URL="https://github.com/xtycome5/Carter-Personal-code.git"

# ============ 颜色 ============
GREEN='\033[0;32m'
NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }

# ============ 系统更新 & 基础工具 ============
info "更新系统 & 安装基础工具..."
apt-get update -qq
apt-get install -y -qq git curl wget nginx certbot python3-certbot-nginx \
    python3 python3-pip python3-venv postgresql postgresql-contrib \
    nodejs npm 2>/dev/null

# 安装 Node 20 (如果系统版本太旧)
if [[ $(node --version 2>/dev/null | cut -d'.' -f1 | tr -d 'v') -lt 18 ]]; then
    info "安装 Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

# ============ 配置 PostgreSQL ============
info "配置 PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

sudo -u postgres psql -c "CREATE DATABASE dreamrecorder;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || true

# 允许密码认证
PG_HBA=$(sudo -u postgres psql -t -c "SHOW hba_file;" | xargs)
sed -i 's/local.*all.*postgres.*peer/local all postgres md5/' "$PG_HBA" 2>/dev/null || true
systemctl restart postgresql

# ============ 克隆代码 ============
info "克隆代码仓库..."
if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR" && git pull
else
    git clone "$REPO_URL" "$PROJECT_DIR"
fi
cd "$PROJECT_DIR"

# ============ 配置后端 ============
info "配置后端..."
cd "$PROJECT_DIR/backend"

python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

# 生成 .env（如果不存在）
if [ ! -f .env ]; then
    cp .env.example .env
    # 生成随机 SECRET_KEY
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/your-secret-key-change-in-production/$SECRET/" .env
    sed -i "s|postgresql+asyncpg://postgres:postgres@localhost:5432/dreamrecorder|postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/dreamrecorder|" .env
    
    echo ""
    echo "=========================================="
    echo "  请编辑 /opt/dreamrecorder/backend/.env"
    echo "  填入 DASHSCOPE_API_KEY"
    echo "=========================================="
fi

deactivate

# ============ 配置前端 ============
info "配置前端..."
cd "$PROJECT_DIR/frontend"
npm install --production=false 2>/dev/null
npm run build 2>/dev/null || info "前端 build 稍后手动执行"

# 创建前端 .env.local
cat > .env.local <<'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# ============ 创建 Systemd 服务 ============
info "创建系统服务..."

# 后端服务
cat > /etc/systemd/system/dreamrecorder-backend.service <<EOF
[Unit]
Description=Dream Recorder Backend API
After=postgresql.service network.target
Requires=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/backend
Environment=PATH=$PROJECT_DIR/backend/venv/bin:/usr/bin
ExecStart=$PROJECT_DIR/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 前端服务
cat > /etc/systemd/system/dreamrecorder-frontend.service <<EOF
[Unit]
Description=Dream Recorder Frontend
After=network.target dreamrecorder-backend.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/frontend
ExecStart=/usr/bin/npm run start -- -p 3000
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=NEXT_PUBLIC_API_URL=http://127.0.0.1:8000

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dreamrecorder-backend
systemctl enable dreamrecorder-frontend

# ============ 配置 Nginx 反代 ============
info "配置 Nginx..."
cat > /etc/nginx/sites-available/dreamrecorder <<'EOF'
server {
    listen 80;
    server_name _;

    # 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    # 后端 API 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF

ln -sf /etc/nginx/sites-available/dreamrecorder /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# ============ 完成 ============
echo ""
echo "============================================"
echo -e "${GREEN}  服务器初始化完成！${NC}"
echo "============================================"
echo ""
echo "  后续步骤："
echo "  1. 编辑 $PROJECT_DIR/backend/.env 填入 DASHSCOPE_API_KEY"
echo "  2. 启动服务:"
echo "     systemctl start dreamrecorder-backend"
echo "     systemctl start dreamrecorder-frontend"
echo ""
echo "  常用命令:"
echo "     systemctl status dreamrecorder-backend"
echo "     systemctl restart dreamrecorder-backend"
echo "     journalctl -u dreamrecorder-backend -f  # 查看日志"
echo ""
echo "  更新代码:"
echo "     cd $PROJECT_DIR && git pull"
echo "     systemctl restart dreamrecorder-backend"
echo "     cd frontend && npm run build"
echo "     systemctl restart dreamrecorder-frontend"
echo "============================================"
