from flask import Flask, request, redirect, url_for, send_from_directory, session, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Конфигурация базы данных
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root', 
    'database': 'web'
}

# Статические файлы
@app.route('/<path:filename>')
def static_files(filename):
    if filename == 'index.html':
        return render_index()
    elif filename == 'admin/index.html':
        return render_admin_index()
    elif filename == 'category.html':
        return render_category_page()
    return send_from_directory('.', filename)

UPLOAD_FOLDER = 'uploads/articles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Создайте папку если ее нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        # Генерируем уникальное имя файла
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{file_ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        return f"/{UPLOAD_FOLDER}/{filename}"
    return None


def render_index():
    try:
        # Получаем категории для главной страницы
        categories = get_categories()
        
        # Читаем index.html
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Генерируем HTML для категорий
        categories_html = ''
        for category in categories:
            categories_html += f'''
            <div class="category-card">
                <h3>{category['name']}</h3>
                <p>{category['description'] or 'Описание отсутствует'}</p>
                <a href="/category.html?id={category['id']}" class="btn-view">Смотреть статьи</a>
            </div>
            '''

        categories_html += '</div>'
        
        # Заменяем placeholder на категории
        if '<!-- CATEGORIES -->' in content:
            content = content.replace('<!-- CATEGORIES -->', categories_html)
        
        # Обработка авторизации
        if session.get('logged_in'):
            user_html = f'''
            <div class="user-menu">
                <div class="user-icon">
                    <img src="uploads/user.png" width="30" height="30" alt="User">
                    <span>{session.get('username', 'User')}</span>
                </div>
                <div class="dropdown-menu">
                    <a href="/logout" class="logout-btn">Выйти</a>
                </div>
            </div>
            '''
            
            if session.get('role') == 'admin':
                admin_button = '<a href="/admin/index.html" class="header-admin">Админ панель</a>'
                user_html = admin_button + user_html
        else:
            # ДОБАВЬ ЭТОТ БЛОК - кнопки для неавторизованных пользователей
            user_html = '''
            <a href="login.html" class="header-login">Войти</a>
            <a href="register.html" class="header-register">Зарегистрироваться</a>
            '''
        
        # Заменяем placeholder на кнопки авторизации
        if '<!-- AUTH_BUTTONS -->' in content:
            content = content.replace('<!-- AUTH_BUTTONS -->', user_html)
        
        return content
    except Exception as e:
        return f"Error rendering index: {str(e)}", 500

def render_category_page():
    try:
        category_id = request.args.get('id')
        if not category_id:
            return "Категория не найдена", 404
        
        # Получаем информацию о категории и статьи
        category = get_category_by_id(category_id)
        articles = get_articles_by_category(category_id)
        
        if not category:
            return "Категория не найдена", 404
        
        # Читаем category.html
        with open('category.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем заголовок категории
        content = content.replace('<!-- CATEGORY_NAME -->', category['name'])
        content = content.replace('<!-- CATEGORY_DESCRIPTION -->', category['description'] or '')
        
        # Генерируем HTML для статей
        # В функции category_page() замените генерацию articles_html на:
        articles_html = ''
        for article in articles:
            # Форматируем дату
            created_date = article['created_at'].strftime('%d.%m.%Y') if article['created_at'] else 'Неизвестно'
            
            articles_html += f'''
            <div class="article-card">
                <h3 class="article-card-title">{article['title']}</h3>
                <p class="article-card-meta">
                    Автор: {article['author_name']}<br>
                    Дата: {created_date}<br>
                    Просмотры: {article['views_count']}
                </p>
                <p class="article-card-excerpt">
                    {article['excerpt'] or article['content'][:100] + '...'}
                </p>
                <a href="/article.html?id={article['id']}" class="btn-read">Читать</a>
            </div>
            '''

        if not articles_html:
            articles_html = '<p class="no-articles">В этой категории пока нет статей.</p>'

        content = content.replace('<!-- ARTICLES_LIST -->', articles_html)
        
        return content
    except Exception as e:
        return f"Error rendering category: {str(e)}", 500


def render_admin_index():
    try:
        if not session.get('logged_in') or session.get('role') != 'admin':
            return redirect('/login.html')
        
        stats = get_admin_stats()
        categories = get_categories_with_count()
        users = get_all_users()
        articles = get_all_articles_with_details()
        
        with open('admin/index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Обновляем статистику
        content = content.replace('<h3>0</h3>', f'<h3>{stats["users_count"]}</h3>')
        content = content.replace('<h3>0</h3>', f'<h3>{stats["articles_count"]}</h3>')
        content = content.replace('<h3>0</h3>', f'<h3>{stats["categories_count"]}</h3>')
        
        # Генерируем таблицу категорий
        categories_html = ''
        for category in categories:
            safe_name = category['name'].replace("'", "&#39;").replace('"', "&quot;")
            safe_description = (category['description'] or '').replace("'", "&#39;").replace('"', "&quot;")
            
            categories_html += f'''
            <tr>
                <td>{category['id']}</td>
                <td>{category['name']}</td>
                <td>{category['description'] or ''}</td>
                <td>{category['articles_count']}</td>
                <td class="actions">
                    <button class="btn-edit" onclick="openCategoryModal({{
                        id: {category['id']},
                        name: '{safe_name}',
                        slug: '{category['slug']}',
                        description: '{safe_description}'
                    }})">Редактировать</button>
                    <button class="btn-delete" onclick="deleteCategory({category['id']})">Удалить</button>
                </td>
            </tr>
            '''
        content = content.replace('<!-- CATEGORIES_TABLE -->', categories_html)
        
        # Генерируем таблицу пользователей
        users_html = ''
        for user in users:
            role_class = 'role-admin' if user['role'] == 'admin' else 'role-user'
            active_class = 'status-active' if user['is_active'] == 1 else 'status-inactive'
            active_text = 'Активен' if user['is_active'] == 1 else 'Неактивен'
            user_selected = 'selected' if user['role'] == 'user' else ''
            admin_selected = 'selected' if user['role'] == 'admin' else ''
            active_selected = 'selected' if user['is_active'] == 1 else ''
            inactive_selected = 'selected' if user['is_active'] == 0 else ''
            
            users_html += f'''
            <tr id="userRow_{user['id']}">
                <td>{user['id']}</td>
                <td>
                    <span class="view-mode" id="usernameView_{user['id']}">{user['user_name']}</span>
                    <input type="text" class="edit-mode" id="usernameEdit_{user['id']}" value="{user['user_name']}" style="display: none;">
                </td>
                <td>
                    <span class="view-mode" id="emailView_{user['id']}">{user['email']}</span>
                    <input type="email" class="edit-mode" id="emailEdit_{user['id']}" value="{user['email']}" style="display: none;">
                </td>
                <td>
                    <span class="view-mode {role_class}" id="roleView_{user['id']}">{user['role']}</span>
                    <select class="edit-mode" id="roleEdit_{user['id']}" style="display: none;">
                        <option value="user" {user_selected}>user</option>
                        <option value="admin" {admin_selected}>admin</option>
                    </select>
                </td>
                <td>
                    <span class="{active_class}" id="activeView_{user['id']}">{active_text}</span>
                    <select class="edit-mode" id="activeEdit_{user['id']}" style="display: none;">
                        <option value="1" {active_selected}>Активен</option>
                        <option value="0" {inactive_selected}>Неактивен</option>
                    </select>
                </td>
                <td>{user['created_at'].strftime('%Y-%m-%d') if user['created_at'] else ''}</td>
                <td class="actions">
                    <button class="btn-edit" id="editBtn_{user['id']}" onclick="startEditUser({user['id']})">Редактировать</button>
                    <button class="btn-save" id="saveBtn_{user['id']}" onclick="saveUser({user['id']})" style="display: none;">Сохранить</button>
                    <button class="btn-cancel" id="cancelBtn_{user['id']}" onclick="cancelEditUser({user['id']})" style="display: none;">Отмена</button>
                    <button class="btn-delete" onclick="deleteUser({user['id']})">Удалить</button>
                </td>
            </tr>
            '''
        content = content.replace('<!-- USERS_TABLE -->', users_html)
        
        # Генерируем таблицу статей
        # Генерируем таблицу статей
        articles_html = ''
        for article in articles:
            status_class = 'status-published' if article['status'] == 'published' else 'status-draft'
            status_text = 'Опубликовано' if article['status'] == 'published' else 'Черновик'
            created_date = article['created_at'].strftime('%d.%m.%Y') if article['created_at'] else ''
            updated_date = article['updated_at'].strftime('%d.%m.%Y') if article['updated_at'] else ''
            
            short_content = (article['content'][:50] + '...') if len(article['content']) > 50 else article['content']
            short_excerpt = (article['excerpt'][:30] + '...') if article['excerpt'] and len(article['excerpt']) > 30 else (article['excerpt'] or '')
            
            # Добавляем выбор статуса
            published_selected = 'selected' if article['status'] == 'published' else ''
            draft_selected = 'selected' if article['status'] == 'draft' else ''
            
            articles_html += f'''
            <tr id="articleRow_{article['id']}">
                <td>{article['id']}</td>
                <td>{article['title']}</td>
                <td>{article['slug']}</td>
                <td title="{article['content']}">{short_content}</td>
                <td>{short_excerpt}</td>
                <td>{article['author_name']} (ID: {article['author_id']})</td>
                <td>{article['category_name']} (ID: {article['category_id']})</td>
                <td>
                    <span class="view-mode {status_class}" id="statusView_{article['id']}">{status_text}</span>
                    <select class="edit-mode" id="statusEdit_{article['id']}" style="display: none;">
                        <option value="published" {published_selected}>Опубликовано</option>
                        <option value="draft" {draft_selected}>Черновик</option>
                    </select>
                </td>
                <td>
                    {f'<img src="{article["featured_image"]}" width="50" height="50" style="object-fit: cover; border-radius: 4px;">' if article['featured_image'] else 'Нет'}
                </td>
                <td>{article['views_count']}</td>
                <td>{created_date}</td>
                <td>{updated_date}</td>
                <td class="actions">
                    <button class="btn-edit" id="editArticleBtn_{article['id']}" onclick="startEditArticle({article['id']})">Изменить статус</button>
                    <button class="btn-save" id="saveArticleBtn_{article['id']}" onclick="saveArticleStatus({article['id']})" style="display: none;">Сохранить</button>
                    <button class="btn-cancel" id="cancelArticleBtn_{article['id']}" onclick="cancelEditArticle({article['id']})" style="display: none;">Отмена</button>
                    <button class="btn-delete" onclick="deleteArticle({article['id']})">Удалить</button>
                </td>
            </tr>
            '''
        content = content.replace('<!-- ARTICLES_TABLE -->', articles_html)
        
        # Генерируем опции категорий для модального окна
        # categories_options = ''
        # for category in categories:
        #     categories_options += f'<option value="{category["id"]}">{category["name"]}</option>'
        # content = content.replace('<!-- CATEGORIES_OPTIONS -->', categories_options)
        
        return content
    except Exception as e:
        return f"Error rendering admin panel: {str(e)}", 500

# Функции для работы с базой данных
def get_categories():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM categories ORDER BY name")
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return categories
    except mysql.connector.Error:
        return []

def get_category_by_id(category_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        category = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return category
    except mysql.connector.Error:
        return None

def get_articles_by_category(category_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        sql = """
        SELECT a.*, u.user_name as author_name 
        FROM articles a 
        LEFT JOIN users u ON a.author_id = u.id 
        WHERE a.category_id = %s AND a.status = 'published'
        ORDER BY a.created_at DESC
        """
        cursor.execute(sql, (category_id,))
        articles = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return articles
    except mysql.connector.Error:
        return []
    
def get_categories_with_count():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        sql = """
        SELECT c.*, COUNT(a.id) as articles_count 
        FROM categories c 
        LEFT JOIN articles a ON c.id = a.category_id 
        GROUP BY c.id 
        ORDER BY c.name
        """
        cursor.execute(sql)
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return categories
    except mysql.connector.Error:
        return []

def get_all_users():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Получаем ВСЕХ пользователей включая неактивных
        cursor.execute("SELECT id, user_name, email, role, created_at, is_active FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return users
    except mysql.connector.Error:
        return []

def get_all_articles():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        sql = """
        SELECT a.*, u.user_name as author_name, c.name as category_name 
        FROM articles a 
        LEFT JOIN users u ON a.author_id = u.id 
        LEFT JOIN categories c ON a.category_id = c.id 
        ORDER BY a.created_at DESC
        """
        cursor.execute(sql)
        articles = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return articles
    except mysql.connector.Error:
        return []

def get_admin_stats():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        categories_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            'users_count': users_count,
            'articles_count': articles_count,
            'categories_count': categories_count
        }
        
    except mysql.connector.Error:
        return {
            'users_count': 0,
            'articles_count': 0,
            'categories_count': 0
        }

# API для работы с категориями
@app.route('/api/categories', methods=['GET', 'POST'])
def api_categories():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        categories = get_categories()
        return jsonify(categories)
    
    elif request.method == 'POST':
        name = request.json.get('name')
        slug = request.json.get('slug')
        description = request.json.get('description')
        
        if not name or not slug:
            return jsonify({'error': 'Name and slug are required'}), 400
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Проверяем, нет ли уже категории с таким slug
            cursor.execute("SELECT id FROM categories WHERE slug = %s", (slug,))
            existing_category = cursor.fetchone()
            
            if existing_category:
                return jsonify({'error': 'Категория с таким slug уже существует'}), 400
            
            sql = "INSERT INTO categories (name, slug, description) VALUES (%s, %s, %s)"
            cursor.execute(sql, (name, slug, description))
            conn.commit()
            category_id = cursor.lastrowid
            
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'id': category_id})
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500


@app.route('/api/categories/<int:category_id>', methods=['PUT', 'DELETE'])
def api_category(category_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'PUT':
        name = request.json.get('name')
        slug = request.json.get('slug')
        description = request.json.get('description')
        
        if not name or not slug:
            return jsonify({'error': 'Name and slug are required'}), 400
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Проверяем, нет ли другой категории с таким slug
            cursor.execute("SELECT id FROM categories WHERE slug = %s AND id != %s", (slug, category_id))
            existing_category = cursor.fetchone()
            
            if existing_category:
                return jsonify({'error': 'Категория с таким slug уже существует'}), 400
            
            sql = "UPDATE categories SET name = %s, slug = %s, description = %s WHERE id = %s"
            cursor.execute(sql, (name, slug, description, category_id))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({'success': True})
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500
    
    elif request.method == 'DELETE':
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Проверяем, есть ли статьи в этой категории
            cursor.execute("SELECT COUNT(*) FROM articles WHERE category_id = %s", (category_id,))
            article_count = cursor.fetchone()[0]
            
            if article_count > 0:
                return jsonify({'error': 'Нельзя удалить категорию, в которой есть статьи'}), 400
            
            sql = "DELETE FROM categories WHERE id = %s"
            cursor.execute(sql, (category_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({'success': True})
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500
    





# API для работы с пользователями
@app.route('/api/users', methods=['GET', 'POST'])
def api_users():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        users = get_all_users()
        return jsonify(users)
    
    elif request.method == 'POST':
        username = request.json.get('username')
        email = request.json.get('email')
        password = request.json.get('password')
        role = request.json.get('role', 'user')
        
        if not username or not email or not password:
            return jsonify({'error': 'Имя пользователя, email и пароль обязательны'}), 400
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Проверяем, нет ли уже пользователя с таким именем или email
            cursor.execute("SELECT id FROM users WHERE user_name = %s OR email = %s", (username, email))
            existing_user = cursor.fetchone()
            
            if existing_user:
                return jsonify({'error': 'Пользователь с таким именем или email уже существует'}), 400
            
            password_hash = generate_password_hash(password)
            
            # ИСПРАВЛЕНИЕ: убрал лишний параметр из SQL запроса
            sql = "INSERT INTO users (user_name, email, password_hash, role) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (username, email, password_hash, role))
            
            conn.commit()
            user_id = cursor.lastrowid
            
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'id': user_id})
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500


@app.route('/api/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def api_user(user_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT id, user_name, email, role, created_at FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if user:
                return jsonify(user)
            else:
                return jsonify({'error': 'User not found'}), 404
                
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500
    
    elif request.method == 'PUT':
        username = request.json.get('username')
        email = request.json.get('email')
        password = request.json.get('password')
        role = request.json.get('role')
        is_active = request.json.get('is_active', 1)
        
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            if password:
                password_hash = generate_password_hash(password)
                sql = "UPDATE users SET user_name = %s, email = %s, password_hash = %s, role = %s, is_active = %s WHERE id = %s"
                cursor.execute(sql, (username, email, password_hash, role, is_active, user_id))
            else:
                sql = "UPDATE users SET user_name = %s, email = %s, role = %s, is_active = %s WHERE id = %s"
                cursor.execute(sql, (username, email, role, is_active, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True})
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500
    
    elif request.method == 'DELETE':
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Вместо удаления устанавливаем is_active = 0
            # sql = "UPDATE users SET is_active = 0 WHERE id = %s"
            # удаление пользователя из бд
            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({'success': True})
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500






# Остальные маршруты
@app.route('/')
def index():
    return render_index()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        email = request.form['email']
        
        if password != confirm_password:
            return "Пароли не совпадают", 400
        
        password_hash = generate_password_hash(password)
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            sql = "INSERT INTO users (user_name, email, password_hash, role) VALUES (%s, %s, %s, 'user')"
            values = (username, email, password_hash)
            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/login.html')
        except mysql.connector.Error as err:
            return f"Ошибка базы данных: {err}", 500
    
    return send_from_directory('.', 'register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            sql = "SELECT id, user_name, password_hash, role FROM users WHERE user_name = %s AND is_active = 1"
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                session['logged_in'] = True
                return redirect('/index.html')
            else:
                return "Неверный логин или пароль", 401
        except Exception as e:
            return f"Ошибка: {str(e)}", 500
    
    return send_from_directory('.', 'login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/index.html')



# ---------------article------------------
@app.route('/article.html')
def create_article_page():
    # Если передан параметр id - показываем статью, иначе форму создания
    article_id = request.args.get('id')
    if article_id:
        return show_article_page(article_id)
    else:
        return show_create_article_form()

def show_create_article_form():
    if not session.get('logged_in'):
        return redirect('/login.html')
    
    try:
        categories = get_categories()
        
        with open('article.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Генерируем опции категорий - ТОЛЬКО ЗДЕСЬ
        categories_options = ''
        for category in categories:
            categories_options += f'<option value="{category["id"]}">{category["name"]}</option>'
        
        content = content.replace('<!-- CATEGORIES_OPTIONS -->', categories_options)
        
        # Обработка авторизации
        if session.get('logged_in'):
            user_html = f'''
            <div class="user-menu">
                <div class="user-icon">
                    <img src="uploads/user.png" width="30" height="30" alt="User">
                    <span>{session.get('username', 'User')}</span>
                </div>
                <div class="dropdown-menu">
                    <a href="/logout" class="logout-btn">Выйти</a>
                </div>
            </div>
            '''
        else:
            user_html = '''
            <a href="login.html" class="header-login">Войти</a>
            <a href="register.html" class="header-register">Зарегистрироваться</a>
            '''
        
        content = content.replace('<!-- AUTH_BUTTONS -->', user_html)
        
        return content
    except Exception as e:
        return f"Error rendering create article page: {str(e)}", 500

def show_article_page(article_id):
    # Логика отображения статьи (как было раньше)
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Увеличиваем счетчик просмотров
        cursor.execute("UPDATE articles SET views_count = views_count + 1 WHERE id = %s", (article_id,))
        conn.commit()
        
        # Получаем статью
        sql = """
        SELECT a.*, u.user_name as author_name, c.name as category_name 
        FROM articles a 
        LEFT JOIN users u ON a.author_id = u.id 
        LEFT JOIN categories c ON a.category_id = c.id 
        WHERE a.id = %s
        """
        cursor.execute(sql, (article_id,))
        article = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not article:
            return "Статья не найдена", 404
        
        # Рендерим страницу статьи
        with open('article-view.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заполняем данные статьи
        content = content.replace('<!-- ARTICLE_TITLE -->', article['title'])
        content = content.replace('<!-- ARTICLE_CONTENT -->', article['content'])
        content = content.replace('<!-- ARTICLE_AUTHOR -->', article['author_name'])
        content = content.replace('<!-- ARTICLE_CATEGORY -->', article['category_name'])
        content = content.replace('<!-- ARTICLE_DATE -->', article['created_at'].strftime('%d.%m.%Y') if article['created_at'] else '')
        content = content.replace('<!-- ARTICLE_VIEWS -->', str(article['views_count']))
        
        if article['featured_image']:
            content = content.replace('<!-- ARTICLE_IMAGE -->', f'<img src="{article["featured_image"]}" alt="{article["title"]}" class="article-image">')
        else:
            content = content.replace('<!-- ARTICLE_IMAGE -->', '')
        
        return content
        
    except Exception as e:
        return f"Error rendering article: {str(e)}", 500
    




@app.route('/api/articles', methods=['POST'])
def create_article():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Получаем данные формы
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt')
        category_id = request.form.get('category_id')
        status = request.form.get('status', 'draft')
        featured_image_url = request.form.get('featured_image')
        
        # Обрабатываем загруженный файл
        featured_image_path = None
        if 'featured_image_file' in request.files:
            file = request.files['featured_image_file']
            if file and file.filename != '':
                featured_image_path = save_uploaded_file(file)
        
        # Используем URL если файл не загружен
        if not featured_image_path and featured_image_url:
            featured_image_path = featured_image_url
        
        if not title or not slug or not content or not category_id:
            return jsonify({'error': 'Title, slug, content and category are required'}), 400
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Проверяем, нет ли уже статьи с таким slug
        cursor.execute("SELECT id FROM articles WHERE slug = %s", (slug,))
        existing_article = cursor.fetchone()
        
        if existing_article:
            return jsonify({'error': 'Статья с таким slug уже существует'}), 400
        
        sql = """
        INSERT INTO articles 
        (title, slug, content, excerpt, author_id, category_id, status, featured_image) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            title, slug, content, excerpt, 
            session['user_id'], category_id, status, featured_image_path
        ))
        conn.commit()
        article_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'id': article_id})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    

@app.route('/uploads/articles/<filename>')
def serve_article_image(filename):
    return send_from_directory('uploads/articles', filename)




@app.route('/category.html')
def category_page():
    category_id = request.args.get('id')
    if not category_id:
        return "Категория не найдена", 404
    
    try:
        # Получаем информацию о категории
        category = get_category_by_id(category_id)
        if not category:
            return "Категория не найдена", 404
        
        # Получаем статьи этой категории
        articles = get_articles_by_category(category_id)
        
        # ДЛЯ ОТЛАДКИ: выведем информацию о статьях
        print("=== DEBUG ARTICLES ===")
        for article in articles:
            print(f"Title: {article['title']}")
            print(f"Featured Image: {article.get('featured_image', 'NOT SET')}")
            print(f"Has Image: {bool(article.get('featured_image'))}")
            print("---")
        
        # Читаем шаблон category.html
        with open('category.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем заголовок и описание категории
        content = content.replace('{{category_name}}', category['name'])
        content = content.replace('{{category_description}}', category['description'] or '')
        
        # Генерируем HTML для списка статей
        articles_html = ''
        for article in articles:
            # Форматируем дату
            created_date = article['created_at'].strftime('%d.%m.%Y') if article['created_at'] else 'Неизвестно'
            
            # Проверяем есть ли картинка у статьи
            image_html = ''
            featured_image = article.get('featured_image')
            if featured_image:
                print(f"Adding image for {article['title']}: {featured_image}")  # Отладка
                image_html = f'<div class="article-card-image"><img src="{featured_image}" alt="{article["title"]}"></div>'
            
            articles_html += f'''
            <div class="article-card">
                {image_html}
                <h3 class="article-card-title">{article['title']}</h3>
                <p class="article-card-meta">
                    Автор: {article['author_name']}<br>
                    Дата: {created_date}<br>
                    Просмотры: {article['views_count']}
                </p>
                <p class="article-card-excerpt">
                    {article['excerpt'] or article['content'][:100] + '...'}
                </p>
                <a href="/article.html?id={article['id']}" class="btn-read">Читать</a>
            </div>
            '''
        
        if not articles_html:
            articles_html = '<p class="no-articles">В этой категории пока нет статей.</p>'
        
        content = content.replace('<!-- ARTICLES_LIST -->', articles_html)
        
        # Обработка авторизации
        if session.get('logged_in'):
            user_html = f'''
            <div class="user-menu">
                <div class="user-icon">
                    <img src="uploads/user.png" width="30" height="30" alt="User">
                    <span>{session.get('username', 'User')}</span>
                </div>
                <div class="dropdown-menu">
                    <a href="/logout" class="logout-btn">Выйти</a>
                </div>
            </div>
            '''
            
            if session.get('role') == 'admin':
                admin_button = '<a href="/admin/index.html" class="header-admin">Админ панель</a>'
                user_html = admin_button + user_html
        else:
            user_html = '''
            <a href="login.html" class="header-login">Войти</a>
            <a href="register.html" class="header-register">Зарегистрироваться</a>
            '''
        
        content = content.replace('<!-- AUTH_BUTTONS -->', user_html)
        
        return content
        
    except Exception as e:
        return f"Error rendering category page: {str(e)}", 500








def show_article_page(article_id):
    # Логика отображения статьи (как было раньше)
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Увеличиваем счетчик просмотров
        cursor.execute("UPDATE articles SET views_count = views_count + 1 WHERE id = %s", (article_id,))
        conn.commit()
        
        # Получаем статью
        sql = """
        SELECT a.*, u.user_name as author_name, c.name as category_name 
        FROM articles a 
        LEFT JOIN users u ON a.author_id = u.id 
        LEFT JOIN categories c ON a.category_id = c.id 
        WHERE a.id = %s
        """
        cursor.execute(sql, (article_id,))
        article = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not article:
            return "Статья не найдена", 404
        
        # Рендерим страницу статьи
        with open('article-view.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заполняем данные статьи
        content = content.replace('<!-- ARTICLE_TITLE -->', article['title'])
        content = content.replace('<!-- ARTICLE_CONTENT -->', article['content'])
        content = content.replace('<!-- ARTICLE_AUTHOR -->', article['author_name'])
        content = content.replace('<!-- ARTICLE_CATEGORY -->', article['category_name'])
        content = content.replace('<!-- ARTICLE_DATE -->', article['created_at'].strftime('%d.%m.%Y') if article['created_at'] else '')
        content = content.replace('<!-- ARTICLE_VIEWS -->', str(article['views_count']))
        
        if article['featured_image']:
            content = content.replace('<!-- ARTICLE_IMAGE -->', f'<img src="{article["featured_image"]}" alt="{article["title"]}" class="article-image">')
        else:
            content = content.replace('<!-- ARTICLE_IMAGE -->', '')
        
        # Обработка авторизации
        if session.get('logged_in'):
            user_html = f'''
            <div class="user-menu">
                <div class="user-icon">
                    <img src="uploads/user.png" width="30" height="30" alt="User">
                    <span>{session.get('username', 'User')}</span>
                </div>
                <div class="dropdown-menu">
                    <a href="/logout" class="logout-btn">Выйти</a>
                </div>
            </div>
            '''
            
            if session.get('role') == 'admin':
                admin_button = '<a href="/admin/index.html" class="header-admin">Админ панель</a>'
                user_html = admin_button + user_html
        else:
            user_html = '''
            <a href="login.html" class="header-login">Войти</a>
            <a href="register.html" class="header-register">Зарегистрироваться</a>
            '''
        
        content = content.replace('<!-- AUTH_BUTTONS -->', user_html)
        
        return content
        
    except Exception as e:
        return f"Error rendering article: {str(e)}", 500















# -------------------таблица articles в админке---------------------------------
def get_all_articles_with_details():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        sql = """
        SELECT 
            a.*,
            u.user_name as author_name,
            c.name as category_name
        FROM articles a 
        LEFT JOIN users u ON a.author_id = u.id 
        LEFT JOIN categories c ON a.category_id = c.id 
        ORDER BY a.created_at DESC
        """
        cursor.execute(sql)
        articles = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return articles
    except mysql.connector.Error:
        return []


# ------------------------таблица в article-------------------------------------
@app.route('/api/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        sql = "DELETE FROM articles WHERE id = %s"
        cursor.execute(sql, (article_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/articles/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        sql = """
        UPDATE articles SET 
            title = %s, slug = %s, content = %s, excerpt = %s, 
            category_id = %s, status = %s, featured_image = %s, updated_at = NOW()
        WHERE id = %s
        """
        cursor.execute(sql, (
            data.get('title'), data.get('slug'), data.get('content'), 
            data.get('excerpt'), data.get('category_id'), data.get('status'),
            data.get('featured_image'), article_id
        ))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

# ----------------------------------------------------------
@app.route('/api/update_article_status', methods=['POST'])
def update_article_status():
    try:
        if not session.get('logged_in') or session.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Доступ запрещен'})
        
        data = request.get_json()
        article_id = data.get('article_id')
        new_status = data.get('status')
        
        if not article_id or not new_status:
            return jsonify({'success': False, 'error': 'Неверные данные'})
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # ИСПРАВЛЕНИЕ: используем %s вместо ? для MySQL
        cursor.execute(
            'UPDATE articles SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s',
            (new_status, article_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True)