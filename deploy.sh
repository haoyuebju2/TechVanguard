#!/bin/bash

# 数码新品时间线部署脚本
# 支持Ubuntu/Debian系统

echo "🚀 开始部署数码新品参数时间线系统..."

# 安装系统依赖
echo "📦 安装系统依赖..."
apt update
apt install -y python3 python3-pip python3-venv nginx supervisor

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据库
echo "🗄️ 初始化数据库..."
python3 -c "from app import init_db; init_db()"

# 导入初始数据
echo "📥 导入初始测试数据..."
cd ../scripts
python3 crawler.py

# 配置Supervisor
echo "⚙️ 配置进程守护..."
cat > /etc/supervisor/conf.d/digital-timeline.conf << EOF
[program:digital-timeline]
directory=/root/digital-timeline/backend
command=/root/digital-timeline/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
user=root
autostart=true
autorestart=true
startretries=3
stdout_logfile=/var/log/digital-timeline.log
stderr_logfile=/var/log/digital-timeline.err.log
EOF

# 配置Nginx
echo "🌐 配置Nginx..."
cat > /etc/nginx/sites-available/digital-timeline << EOF
server {
    listen 80;
    server_name _;

    root /root/digital-timeline/frontend;
    index index.html;

    # API请求转发到后端
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 启用gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
}
EOF

# 启用站点
ln -sf /etc/nginx/sites-available/digital-timeline /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试配置并重启服务
echo "🔄 启动服务..."
nginx -t && systemctl restart nginx
supervisorctl reread
supervisorctl update
supervisorctl start digital-timeline

# 配置定时任务
echo "⏰ 配置定时抓取任务..."
(crontab -l 2>/dev/null; echo "0 17 * * * cd /root/digital-timeline/scripts && /root/digital-timeline/backend/venv/bin/python crawler.py >> /var/log/digital-timeline-cron.log 2>&1") | crontab -

echo "✅ 部署完成！"
echo "🌐 访问地址：http://你的服务器IP"
echo "📅 每日17:00自动抓取最新新品数据"
echo "📋 服务状态查看：supervisorctl status digital-timeline"
echo "📜 日志查看：tail -f /var/log/digital-timeline.log"
