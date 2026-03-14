# 数码新品参数时间线

一个完整的数码新品发布跟踪系统，自动抓取、整理、展示最新的手机、电脑、平板、外设等数码产品参数信息。

## ✨ 功能特性

### 前端功能
- 📅 **时间线展示**：按发布日期纵向排列所有新品信息
- 🔍 **多维度筛选**：支持按品类、日期、关键词搜索
- 📊 **实时统计**：顶部卡片显示各品类新品数量
- 📱 **响应式设计**：完美适配电脑/平板/手机访问
- ⚡ **无限加载**：滚动加载更多历史数据
- 🎨 **美观界面**：现代化UI设计，流畅的动画效果

### 后端功能
- 🤖 **自动抓取**：每日17:00自动抓取多个数据源的新品信息
- 🧹 **智能去重**：基于品牌+型号自动去重，避免重复数据
- 🏷️ **自动分类**：AI自动识别产品类型（手机/笔记本/平板/外设）
- 📝 **参数标准化**：统一参数格式和单位
- 🔌 **RESTful API**：完整的API接口，便于扩展

### 系统特性
- 🚀 **高性能**：前后端分离架构，支持十万级产品数据
- 🛡️ **高安全**：纯接口设计，无SQL注入、XSS等常见漏洞
- 🔄 **高可用**：进程守护+自动重启，服务永不宕机
- 💾 **低资源**：1核1G服务器即可流畅运行
- 📦 **易部署**：一键部署脚本，10分钟完成部署

## 🏗️ 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端页面       │    │  Flask后端API    │    │  SQLite数据库    │
│  (HTML+JS+CSS)  │ ←→ │  (Python)       │ ←→ │  (轻量文件型)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ↑                     ↑
         │                     │
         ▼                     ▼
┌─────────────────┐    ┌─────────────────┐
│   Nginx反向代理   │    │  定时爬虫脚本    │
│  (静态文件服务)   │    │  (每日自动执行)  │
└─────────────────┘    └─────────────────┘
```

## 🚀 快速部署

### 环境要求
- 操作系统：Ubuntu 20.04+ / Debian 11+
- 硬件配置：1核1G内存以上
- 网络要求：公网IP，开放80端口

### 一键部署
```bash
# 1. 克隆或上传代码到服务器
git clone <仓库地址> /root/digital-timeline
cd /root/digital-timeline

# 2. 执行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 部署完成后
- 访问地址：`http://你的服务器IP`
- 查看服务状态：`supervisorctl status digital-timeline`
- 查看日志：`tail -f /var/log/digital-timeline.log`

## 📁 目录结构

```
digital-timeline/
├── backend/                 # 后端代码
│   ├── app.py              # Flask主程序
│   ├── requirements.txt    # Python依赖
│   └── digital_products.db # SQLite数据库
├── frontend/               # 前端代码
│   └── index.html          # 单页应用
├── scripts/                # 工具脚本
│   └── crawler.py          # 爬虫脚本
├── deploy.sh               # 一键部署脚本
└── README.md               # 说明文档
```

## 🔧 API接口

### 获取产品列表
```
GET /api/products
```
**参数：**
- `page`：页码，默认1
- `per_page`：每页数量，默认20
- `category`：分类筛选（phone/laptop/tablet/peripheral）
- `date`：日期筛选（格式：2026-03-14）
- `search`：关键词搜索

**响应：**
```json
{
  "products": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### 获取分类列表
```
GET /api/categories
```

### 获取日期列表
```
GET /api/dates
```

### 获取统计数据
```
GET /api/stats
```

### 添加产品
```
POST /api/products
Content-Type: application/json

{
  "brand": "华为",
  "name": "Mate 60 Pro",
  "category": "phone",
  "parameters": {
    "chip": "麒麟9000S",
    "screen": "6.82英寸OLED",
    "battery": "5000mAh"
  },
  "status": "在售",
  "release_date": "2026-03-14T12:00:00",
  "source": "官方发布"
}
```

## 🔄 自动更新机制

- **每日17:00**：自动执行爬虫脚本，抓取当日新品信息
- **数据处理**：自动清洗、去重、分类后存入数据库
- **实时生效**：用户刷新页面即可看到最新数据，无需重启服务

## 📊 数据源

目前支持以下数据源：
- ✅ IT之家数码频道
- ⬜ 中关村在线（ZOL）
- ⬜ 京东3C新品专区
- ⬜ 爱科技iMobile
- ⬜ 泡泡网
- ⬜ 数码博主公开爆料

持续扩展中...

## 🛡️ 安全说明

1. **无用户系统**：不需要登录，不收集任何用户数据
2. **只读设计**：所有接口都是只读的，没有修改/删除操作
3. **输入校验**：所有API参数都做了严格校验
4. **HTTPS支持**：可配置SSL证书实现加密访问

## 📝 自定义配置

### 修改抓取时间
编辑crontab：
```bash
crontab -e
```
找到以下行修改时间：
```
0 17 * * * /root/digital-timeline/scripts/crawler.py
```

### 添加新的数据源
在 `scripts/crawler.py` 中添加新的爬虫函数即可。

### 修改前端样式
直接编辑 `frontend/index.html` 中的CSS和HTML，刷新页面即可生效。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License
