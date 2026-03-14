from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# 数据库初始化
def init_db():
    conn = sqlite3.connect('digital_products.db')
    c = conn.cursor()
    
    # 产品表
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  brand TEXT NOT NULL,
                  name TEXT NOT NULL,
                  category TEXT NOT NULL,
                  parameters TEXT NOT NULL,
                  status TEXT NOT NULL,
                  release_date TEXT NOT NULL,
                  source TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  UNIQUE(brand, name))''')
    
    # 分类表
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  icon TEXT NOT NULL)''')
    
    # 插入默认分类
    default_categories = [
        ('phone', 'fa-mobile'),
        ('laptop', 'fa-laptop'),
        ('tablet', 'fa-tablet'),
        ('peripheral', 'fa-keyboard-o')
    ]
    for name, icon in default_categories:
        c.execute('INSERT OR IGNORE INTO categories (name, icon) VALUES (?, ?)', (name, icon))
    
    conn.commit()
    conn.close()

# 数据库操作工具类
class DB:
    def __enter__(self):
        self.conn = sqlite3.connect('digital_products.db')
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

# API接口
@app.route('/api/products', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category', 'all')
    date = request.args.get('date', 'all')
    search = request.args.get('search', '')
    
    offset = (page - 1) * per_page
    
    with DB() as c:
        # 构建查询条件
        conditions = []
        params = []
        
        if category != 'all':
            conditions.append('category = ?')
            params.append(category)
        
        if date != 'all':
            conditions.append('release_date LIKE ?')
            params.append(f'{date}%')
        
        if search:
            conditions.append('(brand LIKE ? OR name LIKE ? OR parameters LIKE ?)')
            search_term = f'%{search}%'
            params.extend([search_term, search_term, search_term])
        
        where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        
        # 查询数据
        query = f'''SELECT * FROM products {where_clause} 
                    ORDER BY release_date DESC, created_at DESC 
                    LIMIT ? OFFSET ?'''
        params.extend([per_page, offset])
        c.execute(query, params)
        products = [dict(row) for row in c.fetchall()]
        
        # 解析参数JSON
        for product in products:
            product['parameters'] = json.loads(product['parameters'])
        
        # 查询总数
        count_query = f'SELECT COUNT(*) as total FROM products {where_clause}'
        c.execute(count_query, params[:-2] if params else [])
        total = c.fetchone()['total']
    
    return jsonify({
        'products': products,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        }
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    with DB() as c:
        c.execute('SELECT * FROM categories')
        categories = [dict(row) for row in c.fetchall()]
    
    return jsonify({'categories': categories})

@app.route('/api/dates', methods=['GET'])
def get_dates():
    with DB() as c:
        c.execute('''SELECT DISTINCT DATE(release_date) as date 
                     FROM products 
                     ORDER BY date DESC''')
        dates = [row['date'] for row in c.fetchall()]
    
    return jsonify({'dates': dates})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    with DB() as c:
        # 总产品数
        c.execute('SELECT COUNT(*) as total FROM products')
        total = c.fetchone()['total']
        
        # 各分类数量
        c.execute('''SELECT category, COUNT(*) as count 
                     FROM products 
                     GROUP BY category''')
        category_counts = {row['category']: row['count'] for row in c.fetchall()}
        
        # 今日新增
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''SELECT COUNT(*) as count 
                     FROM products 
                     WHERE DATE(release_date) = ?''', (today,))
        today_new = c.fetchone()['count']
    
    return jsonify({
        'total': total,
        'category_counts': category_counts,
        'today_new': today_new
    })

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    
    required_fields = ['brand', 'name', 'category', 'parameters', 'status', 'release_date', 'source']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    try:
        with DB() as c:
            c.execute('''INSERT OR IGNORE INTO products 
                         (brand, name, category, parameters, status, release_date, source, created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (data['brand'],
                       data['name'],
                       data['category'],
                       json.dumps(data['parameters'], ensure_ascii=False),
                       data['status'],
                       data['release_date'],
                       data['source'],
                       datetime.now().isoformat()))
            
            if c.rowcount == 0:
                return jsonify({'message': 'Product already exists'}), 200
            
            product_id = c.lastrowid
        
        return jsonify({'id': product_id, 'message': 'Product added successfully'}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 静态文件服务
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(f'frontend/{path}'):
        return send_from_directory('frontend', path)
    else:
        return send_from_directory('frontend', 'index.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
