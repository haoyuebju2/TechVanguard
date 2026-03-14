import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime, timedelta
import sqlite3

# 请求头
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

# 保存产品到数据库
def save_product(product):
    conn = sqlite3.connect('/root/digital-timeline/backend/digital_products.db')
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
        print(保存产品失败:, str(e))
        return False
    finally:
        conn.close()

# 抓取IT之家历史数据
def crawl_ithome():
    print(开始抓取IT之家历史数据...)
    count = 0
    
    for page in range(1, 100):  # 前100页，大概1年的数据
        try:
            url = https://digi.ithome.com/list_ + str(page) + .html
            response = requests.get(url, headers=get_headers(), timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            items = soup.select('.cate_list li')
            if not items:
                break
                
            for item in items:
                try:
                    title = item.select_one('h2 a').get_text(strip=True)
                    
                    # 只处理数码产品相关
                    keywords = ['手机', '笔记本', '平板', '显示器', '键盘', '鼠标', '充电器', '耳机', '相机']
                    if not any(k in title for k in keywords):
                        continue
                    
                    # 分类
                    category = 'peripheral'
                    if '手机' in title:
                        category = 'phone'
                    elif '笔记本' in title or '电脑' in title:
                        category = 'laptop'
                    elif '平板' in title:
                        category = 'tablet'
                    
                    # 提取品牌
                    brand = ''
                    name = title
                    brands = ['华为', '小米', 'OPPO', 'vivo', '苹果', '三星', '联想', '戴尔', '惠普', '华硕', '荣耀', '红米', '一加']
                    for b in brands:
                        if b in title:
                            brand = b
                            name = title.replace(b, '').strip()
                            break
                    
                    # 摘要
                    summary = item.select_one('.content').get_text(strip=True) if item.select_one('.content') else ''
                    
                    # 参数
                    params = {'description': summary[:200]}
                    
                    # 发布时间
                    release_date = (datetime.now() - timedelta(days=page)).isoformat()
                    
                    product = {
                        'brand': brand,
                        'name': name,
                        'category': category,
                        'parameters': params,
                        'status': '在售',
                        'release_date': release_date,
                        'source': 'IT之家'
                    }
                    
                    if save_product(product):
                        count += 1
                        print(新增产品:, brand, name)
                    
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(处理条目失败:, str(e))
                    continue
            
            print(第, page, 页抓取完成，累计新增, count, 款)
            time.sleep(1)
            
        except Exception as e:
            print(抓取页面失败:, str(e))
            time.sleep(3)
            continue
    
    print(抓取完成，共新增, count, 款产品)
    return count

if __name__ == __main__:
    crawl_ithome()
