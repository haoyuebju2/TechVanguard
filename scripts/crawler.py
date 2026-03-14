import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
import sqlite3
import feedparser

# 请求头
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }

# 数据库操作
def save_product(product):
    conn = sqlite3.connect('../backend/digital_products.db')
    c = conn.cursor()
    
    try:
        c.execute('''INSERT OR IGNORE INTO products 
                     (brand, name, category, parameters, status, release_date, source, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (product['brand'],
                   product['name'],
                   product['category'],
                   json.dumps(product['parameters'], ensure_ascii=False),
                   product['status'],
                   product['release_date'],
                   product['source'],
                   datetime.now().isoformat()))
        
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        print(f"保存产品失败: {e}")
        return False
    finally:
        conn.close()

# IT之家爬虫
def crawl_ithome():
    print("开始抓取IT之家...")
    url = "https://digi.ithome.com/"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = soup.select('.cate_list li')
        count = 0
        
        for item in items[:20]:  # 只抓前20条
            try:
                title = item.select_one('h2 a').get_text(strip=True)
                link = item.select_one('h2 a')['href']
                time_str = item.select_one('.post_time').get_text(strip=True)
                
                # 判断是否是数码产品相关
                if any(keyword in title for keyword in ['手机', '笔记本', '平板', '显示器', '键盘', '鼠标', '充电器', '耳机', '相机', '芯片', '处理器']):
                    # 分类识别
                    category = 'peripheral'
                    if '手机' in title:
                        category = 'phone'
                    elif '笔记本' in title or '电脑' in title or '游戏本' in title:
                        category = 'laptop'
                    elif '平板' in title or 'iPad' in title:
                        category = 'tablet'
                    
                    # 提取品牌和型号
                    brand = ''
                    name = title
                    brands = ['华为', '小米', 'OPPO', 'vivo', '苹果', '三星', '联想', '戴尔', '惠普', '华硕', 'AOC', '罗技', '雷柏', '飞傲', '绿联', '倍思']
                    for b in brands:
                        if b in title:
                            brand = b
                            name = title.replace(b, '').strip()
                            break
                    
                    # 提取摘要
                    summary = item.select_one('.content').get_text(strip=True) if item.select_one('.content') else ''
                    
                    # 构建参数
                    params = {}
                    if '骁龙' in summary:
                        params['chip'] = [s for s in summary.split('，') if '骁龙' in s][0] if any('骁龙' in s for s in summary.split('，')) else '骁龙处理器'
                    if '英寸' in summary:
                        params['screen'] = [s for s in summary.split('，') if '英寸' in s][0] if any('英寸' in s for s in summary.split('，')) else ''
                    if 'mAh' in summary:
                        params['battery'] = [s for s in summary.split('，') if 'mAh' in s][0] if any('mAh' in s for s in summary.split('，')) else ''
                    if '元' in summary:
                        params['price'] = [s for s in summary.split('，') if '元' in s][0] if any('元' in s for s in summary.split('，')) else ''
                    
                    if not params:
                        params['description'] = summary[:200]
                    
                    # 状态判断
                    status = '爆料'
                    if '发布' in title or '上市' in title:
                        status = '在售'
                    elif '预约' in title or '预售' in title:
                        status = '预约中'
                    
                    product = {
                        'brand': brand,
                        'name': name,
                        'category': category,
                        'parameters': params,
                        'status': status,
                        'release_date': datetime.now().isoformat(),
                        'source': 'IT之家'
                    }
                    
                    if save_product(product):
                        count += 1
                        print(f"新增产品: {brand} {name}")
                    
                    time.sleep(random.uniform(0.5, 1.5))
                    
            except Exception as e:
                print(f"处理条目失败: {e}")
                continue
        
        print(f"IT之家抓取完成，新增{count}款产品")
        return count
        
    except Exception as e:
        print(f"IT之家抓取失败: {e}")
        return 0

# 初始化测试数据
def init_test_data():
    print("初始化测试数据...")
    
    test_products = [
        {
            'brand': '华为',
            'name': '畅享90 Plus / 90 Pro Max',
            'category': 'phone',
            'parameters': {
                'chip': '海思麒麟8系芯片',
                'battery': '巨鲸大电池，续航能力突出',
                'design': 'Plus版采用后盖同色矩形模组，Pro Max版为圆形模组'
            },
            'status': '预约中',
            'release_date': '2026-03-14T13:12:00',
            'source': 'IT之家'
        },
        {
            'brand': '三星',
            'name': '阔折叠新机',
            'category': 'phone',
            'parameters': {
                'screen': '7.6英寸内折叠大屏',
                'chip': '骁龙8 Elite Gen 5（8E5）处理器',
                'battery': '双电芯典型值4800mAh±电池',
                'design': '或采用横向优先设计'
            },
            'status': '爆料',
            'release_date': '2026-03-14T15:24:00',
            'source': '数码闲聊站'
        },
        {
            'brand': 'OPPO',
            'name': 'Pad 5 Pro',
            'category': 'tablet',
            'parameters': {
                'chip': '骁龙8 Elite Gen 5芯片',
                'screen': '13.2英寸超大屏幕',
                'battery': '典型值13000mAh±大容量电池'
            },
            'status': '爆料',
            'release_date': '2026-03-14T11:15:00',
            'source': '数码闲聊站'
        },
        {
            'brand': '联想',
            'name': 'Yoga Slim 7a',
            'category': 'laptop',
            'parameters': {
                'chip': 'AMD Gorgon Point处理器',
                'screen': '14英寸1100尼特OLED面板',
                'price': '起售价1160欧元（约合人民币9171元）'
            },
            'status': '海外上市',
            'release_date': '2026-03-14T10:49:00',
            'source': 'IT之家'
        },
        {
            'brand': 'AOC',
            'name': '爱攻7 Pro AGP277KX 显示器',
            'category': 'peripheral',
            'parameters': {
                'screen': '27英寸双模FastIPS面板',
                'refresh_rate': '支持一键切换：5K@180Hz / 2K@350Hz',
                'certification': '通过DisplayHDR 400认证',
                'price': '售价5999元'
            },
            'status': '预约中',
            'release_date': '2026-03-14T13:28:00',
            'source': 'IT之家'
        },
        {
            'brand': 'OPPO',
            'name': '磁吸小涡轮2代 50W无线充电器',
            'category': 'peripheral',
            'parameters': {
                'power': '50W无线快充',
                'design': '内置360°桌面支架，悬浮式设计',
                'modes': '支持清凉充/静音充/仅散热三种模式'
            },
            'status': '预约中',
            'release_date': '2026-03-14T17:41:00',
            'source': 'IT之家'
        }
    ]
    
    count = 0
    for product in test_products:
        if save_product(product):
            count += 1
    
    print(f"初始化完成，新增{count}款测试产品")

if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 初始化测试数据
    init_test_data()
    
    # 抓取IT之家
    crawl_ithome()
    
    print("抓取任务完成")
