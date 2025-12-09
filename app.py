from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB 제한
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'py', 'ipynb', 'pth', 'pt', 'h5', 'pkl', 'csv', 'xlsx', 'json'}

# 관리자 비밀번호 (환경변수로 설정 가능)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')

# 업로드 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 데이터베이스 설정
DATABASE_URL = os.environ.get('DATABASE_URL')

# PostgreSQL인지 SQLite인지 판단
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Render의 DATABASE_URL은 postgres://로 시작하는데, psycopg2는 postgresql://을 사용
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    def get_db_connection():
        conn = psycopg2.connect(DATABASE_URL)
        return conn
else:
    import sqlite3
    
    def get_db_connection():
        conn = sqlite3.connect('board.db')
        conn.row_factory = sqlite3.Row
        return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        # PostgreSQL용 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                board_type VARCHAR(20) NOT NULL,
                title TEXT NOT NULL,
                author VARCHAR(100) NOT NULL,
                password TEXT NOT NULL,
                content TEXT NOT NULL,
                filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                post_id INTEGER NOT NULL,
                author VARCHAR(100) NOT NULL,
                password TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
            )
        ''')
    else:
        # SQLite용 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_type TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                password TEXT NOT NULL,
                content TEXT NOT NULL,
                filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                password TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')
    
    conn.commit()
    cursor.close()
    conn.close()

def dict_from_row(row):
    """데이터베이스 row를 dict로 변환"""
    if USE_POSTGRES:
        return dict(row)
    else:
        return dict(row)

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    cursor.execute(
        "SELECT * FROM posts WHERE board_type = %s ORDER BY id DESC LIMIT 3" if USE_POSTGRES 
        else "SELECT * FROM posts WHERE board_type = ? ORDER BY id DESC LIMIT 3",
        ('project',)
    )
    project_posts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('index.html', project_posts=project_posts)

@app.route('/board/<board_type>')
def board(board_type):
    if board_type not in ['free', 'project']:
        return "잘못된 게시판입니다.", 404
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    cursor.execute(
        'SELECT * FROM posts WHERE board_type = %s ORDER BY id DESC' if USE_POSTGRES
        else 'SELECT * FROM posts WHERE board_type = ? ORDER BY id DESC',
        (board_type,)
    )
    posts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    board_name = '자유게시판' if board_type == 'free' else '프로젝트게시판'
    return render_template('board.html', posts=posts, board_type=board_type, board_name=board_name)

@app.route('/write/<board_type>', methods=['GET', 'POST'])
def write(board_type):
    if board_type not in ['free', 'project']:
        return "잘못된 게시판입니다.", 404
    
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        password = request.form['password']
        content = request.form['content']
        file = request.files.get('file')
        
        password_hash = generate_password_hash(password)
        
        filename = None
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO posts (board_type, title, author, password, content, filename) VALUES (%s, %s, %s, %s, %s, %s)' if USE_POSTGRES
            else 'INSERT INTO posts (board_type, title, author, password, content, filename) VALUES (?, ?, ?, ?, ?, ?)',
            (board_type, title, author, password_hash, content, filename)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('게시글이 작성되었습니다.', 'success')
        return redirect(url_for('board', board_type=board_type))
    
    board_name = '자유게시판' if board_type == 'free' else '프로젝트게시판'
    return render_template('write.html', board_type=board_type, board_name=board_name)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    cursor.execute(
        'SELECT * FROM posts WHERE id = %s' if USE_POSTGRES else 'SELECT * FROM posts WHERE id = ?',
        (post_id,)
    )
    post = cursor.fetchone()
    
    if post is None:
        cursor.close()
        conn.close()
        return "게시글을 찾을 수 없습니다.", 404
    
    cursor.execute(
        'SELECT * FROM comments WHERE post_id = %s ORDER BY id ASC' if USE_POSTGRES
        else 'SELECT * FROM comments WHERE post_id = ? ORDER BY id ASC',
        (post_id,)
    )
    comments = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('view.html', post=post, comments=comments)

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    cursor.execute(
        'SELECT * FROM posts WHERE id = %s' if USE_POSTGRES else 'SELECT * FROM posts WHERE id = ?',
        (post_id,)
    )
    post = cursor.fetchone()
    
    if post is None:
        cursor.close()
        conn.close()
        return "게시글을 찾을 수 없습니다.", 404
    
    if request.method == 'POST':
        password = request.form['password']
        
        is_admin = password == ADMIN_PASSWORD
        is_author = check_password_hash(post['password'], password)
        
        if not (is_admin or is_author):
            cursor.close()
            conn.close()
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return redirect(url_for('view_post', post_id=post_id))
        
        title = request.form['title']
        content = request.form['content']
        file = request.files.get('file')
        
        filename = post['filename']
        if file and file.filename and allowed_file(file.filename):
            if filename:
                old_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(old_file):
                    os.remove(old_file)
            
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        cursor.execute(
            'UPDATE posts SET title = %s, content = %s, filename = %s WHERE id = %s' if USE_POSTGRES
            else 'UPDATE posts SET title = ?, content = ?, filename = ? WHERE id = ?',
            (title, content, filename, post_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('게시글이 수정되었습니다.', 'success')
        return redirect(url_for('view_post', post_id=post_id))
    
    cursor.close()
    conn.close()
    return render_template('edit.html', post=post)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    cursor.execute(
        'SELECT * FROM posts WHERE id = %s' if USE_POSTGRES else 'SELECT * FROM posts WHERE id = ?',
        (post_id,)
    )
    post = cursor.fetchone()
    
    if post is None:
        cursor.close()
        conn.close()
        return "게시글을 찾을 수 없습니다.", 404
    
    is_admin = password == ADMIN_PASSWORD
    is_author = check_password_hash(post['password'], password)
    
    if not (is_admin or is_author):
        cursor.close()
        conn.close()
        flash('비밀번호가 일치하지 않습니다.', 'error')
        return redirect(url_for('view_post', post_id=post_id))
    
    if post['filename']:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], post['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
    
    cursor.execute(
        'DELETE FROM comments WHERE post_id = %s' if USE_POSTGRES else 'DELETE FROM comments WHERE post_id = ?',
        (post_id,)
    )
    cursor.execute(
        'DELETE FROM posts WHERE id = %s' if USE_POSTGRES else 'DELETE FROM posts WHERE id = ?',
        (post_id,)
    )
    
    conn.commit()
    
    board_type = post['board_type']
    cursor.close()
    conn.close()
    
    flash('게시글이 삭제되었습니다.', 'success')
    return redirect(url_for('board', board_type=board_type))

@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    author = request.form['author']
    password = request.form['password']
    content = request.form['content']
    
    password_hash = generate_password_hash(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO comments (post_id, author, password, content) VALUES (%s, %s, %s, %s)' if USE_POSTGRES
        else 'INSERT INTO comments (post_id, author, password, content) VALUES (?, ?, ?, ?)',
        (post_id, author, password_hash, content)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('댓글이 작성되었습니다.', 'success')
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    cursor.execute(
        'SELECT * FROM comments WHERE id = %s' if USE_POSTGRES else 'SELECT * FROM comments WHERE id = ?',
        (comment_id,)
    )
    comment = cursor.fetchone()
    
    if comment is None:
        cursor.close()
        conn.close()
        flash('댓글을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))
    
    is_admin = password == ADMIN_PASSWORD
    is_author = check_password_hash(comment['password'], password)
    
    if not (is_admin or is_author):
        cursor.close()
        conn.close()
        flash('비밀번호가 일치하지 않습니다.', 'error')
        return redirect(url_for('view_post', post_id=comment['post_id']))
    
    post_id = comment['post_id']
    
    cursor.execute(
        'DELETE FROM comments WHERE id = %s' if USE_POSTGRES else 'DELETE FROM comments WHERE id = ?',
        (comment_id,)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('댓글이 삭제되었습니다.', 'success')
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 백업/복원 API 엔드포인트
@app.route('/admin/backup')
def admin_backup():
    """관리자 전용: 데이터베이스 백업"""
    admin_password = request.args.get('password')
    
    if admin_password != ADMIN_PASSWORD:
        return "Unauthorized", 401
    
    from flask import jsonify
    from datetime import datetime
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    # 게시글 백업
    cursor.execute('SELECT * FROM posts ORDER BY id')
    posts = [dict(row) for row in cursor.fetchall()]
    
    # 댓글 백업
    cursor.execute('SELECT * FROM comments ORDER BY id')
    comments = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    backup_data = {
        'backup_date': datetime.now().isoformat(),
        'database_type': 'PostgreSQL' if USE_POSTGRES else 'SQLite',
        'posts_count': len(posts),
        'comments_count': len(comments),
        'posts': posts,
        'comments': comments
    }
    
    return jsonify(backup_data)

@app.route('/admin/restore', methods=['POST'])
def admin_restore():
    """관리자 전용: 데이터베이스 복원"""
    admin_password = request.form.get('password')
    
    if admin_password != ADMIN_PASSWORD:
        return "Unauthorized", 401
    
    import json
    
    # JSON 파일 업로드
    if 'backup_file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['backup_file']
    if file.filename == '':
        return "No file selected", 400
    
    backup_data = json.load(file)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 기존 데이터 삭제
    cursor.execute('DELETE FROM comments')
    cursor.execute('DELETE FROM posts')
    
    # 게시글 복원
    for post in backup_data['posts']:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO posts (id, board_type, title, author, password, content, filename, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (post['id'], post['board_type'], post['title'], post['author'], 
                  post['password'], post['content'], post.get('filename'), post['created_at']))
        else:
            cursor.execute('''
                INSERT INTO posts (id, board_type, title, author, password, content, filename, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (post['id'], post['board_type'], post['title'], post['author'], 
                  post['password'], post['content'], post.get('filename'), post['created_at']))
    
    # 댓글 복원
    for comment in backup_data['comments']:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO comments (id, post_id, author, password, content, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (comment['id'], comment['post_id'], comment['author'], 
                  comment['password'], comment['content'], comment['created_at']))
        else:
            cursor.execute('''
                INSERT INTO comments (id, post_id, author, password, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (comment['id'], comment['post_id'], comment['author'], 
                  comment['password'], comment['content'], comment['created_at']))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return f"Restored {len(backup_data['posts'])} posts and {len(backup_data['comments'])} comments"

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
