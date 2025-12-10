from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Cloudinary 설정
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# 관리자 비밀번호
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')

# PostgreSQL/SQLite 자동 전환
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    import sqlite3

def get_db_connection():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect('board.db')
        conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        # posts 테이블 (cloudinary_url, cloudinary_public_id 추가)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                board_type VARCHAR(20) NOT NULL,
                title VARCHAR(200) NOT NULL,
                author VARCHAR(100) NOT NULL,
                password VARCHAR(200) NOT NULL,
                content TEXT,
                filename VARCHAR(200),
                cloudinary_url TEXT,
                cloudinary_public_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # comments 테이블 (parent_id 추가 - 대댓글용)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
                parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
                author VARCHAR(100) NOT NULL,
                password VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_type TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                password TEXT NOT NULL,
                content TEXT,
                filename TEXT,
                cloudinary_url TEXT,
                cloudinary_public_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                parent_id INTEGER,
                author TEXT NOT NULL,
                password TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES comments (id) ON DELETE CASCADE
            )
        ''')
    
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    cursor.execute(
        "SELECT * FROM posts WHERE board_type = %s ORDER BY created_at DESC LIMIT 5" if USE_POSTGRES
        else "SELECT * FROM posts WHERE board_type = ? ORDER BY created_at DESC LIMIT 5",
        ('project',)
    )
    recent_projects = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template('index.html', recent_projects=recent_projects)

@app.route('/board/<board_type>')
def board(board_type):
    if board_type not in ['free', 'project']:
        return "잘못된 게시판입니다.", 404
    
    board_name = '자유게시판' if board_type == 'free' else '프로젝트게시판'
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    cursor.execute(
        'SELECT * FROM posts WHERE board_type = %s ORDER BY created_at DESC' if USE_POSTGRES
        else 'SELECT * FROM posts WHERE board_type = ? ORDER BY created_at DESC',
        (board_type,)
    )
    posts = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
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
        
        password_hash = generate_password_hash(password)
        
        file = request.files.get('file')
        cloudinary_url = None
        cloudinary_public_id = None
        filename = None
        
        if file and file.filename:
            filename = secure_filename(file.filename)
            
            # Cloudinary 업로드
            try:
                upload_result = cloudinary.uploader.upload(
                    file,
                    folder=f"nvidia8th_board/{board_type}",
                    resource_type="auto"
                )
                cloudinary_url = upload_result['secure_url']
                cloudinary_public_id = upload_result['public_id']
            except Exception as e:
                flash(f'파일 업로드 실패: {str(e)}', 'error')
                return redirect(url_for('write', board_type=board_type))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO posts (board_type, title, author, password, content, filename, cloudinary_url, cloudinary_public_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (board_type, title, author, password_hash, content, filename, cloudinary_url, cloudinary_public_id))
        else:
            cursor.execute('''
                INSERT INTO posts (board_type, title, author, password, content, filename, cloudinary_url, cloudinary_public_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (board_type, title, author, password_hash, content, filename, cloudinary_url, cloudinary_public_id))
        
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
    
    post = dict(post)
    
    # 댓글 및 대댓글 조회
    cursor.execute(
        'SELECT * FROM comments WHERE post_id = %s ORDER BY created_at ASC' if USE_POSTGRES
        else 'SELECT * FROM comments WHERE post_id = ? ORDER BY created_at ASC',
        (post_id,)
    )
    all_comments = [dict(row) for row in cursor.fetchall()]
    
    # 댓글 계층 구조 생성
    comments = []
    comment_dict = {}
    
    for comment in all_comments:
        comment['replies'] = []
        comment_dict[comment['id']] = comment
        
        if comment['parent_id'] is None:
            comments.append(comment)
        else:
            if comment['parent_id'] in comment_dict:
                comment_dict[comment['parent_id']]['replies'].append(comment)
    
    cursor.close()
    conn.close()
    
    return render_template('view.html', post=post, comments=comments)

@app.route('/post/<int:post_id>/edit', methods=['POST'])
def edit_post(post_id):
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
    
    cursor.close()
    conn.close()
    
    return render_template('edit.html', post=dict(post))

@app.route('/post/<int:post_id>/update', methods=['POST'])
def update_post(post_id):
    title = request.form['title']
    content = request.form['content']
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
    
    # 파일 수정 처리
    file = request.files.get('file')
    cloudinary_url = post['cloudinary_url']
    cloudinary_public_id = post['cloudinary_public_id']
    filename = post['filename']
    
    # 기존 파일 삭제 체크박스
    if request.form.get('delete_file') == 'on':
        if cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(cloudinary_public_id)
            except:
                pass
        cloudinary_url = None
        cloudinary_public_id = None
        filename = None
    
    # 새 파일 업로드
    if file and file.filename:
        # 기존 파일 삭제
        if cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(cloudinary_public_id)
            except:
                pass
        
        filename = secure_filename(file.filename)
        try:
            upload_result = cloudinary.uploader.upload(
                file,
                folder=f"nvidia8th_board/{post['board_type']}",
                resource_type="auto"
            )
            cloudinary_url = upload_result['secure_url']
            cloudinary_public_id = upload_result['public_id']
        except Exception as e:
            flash(f'파일 업로드 실패: {str(e)}', 'error')
    
    if USE_POSTGRES:
        cursor.execute('''
            UPDATE posts 
            SET title = %s, content = %s, filename = %s, cloudinary_url = %s, cloudinary_public_id = %s
            WHERE id = %s
        ''', (title, content, filename, cloudinary_url, cloudinary_public_id, post_id))
    else:
        cursor.execute('''
            UPDATE posts 
            SET title = ?, content = ?, filename = ?, cloudinary_url = ?, cloudinary_public_id = ?
            WHERE id = ?
        ''', (title, content, filename, cloudinary_url, cloudinary_public_id, post_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('게시글이 수정되었습니다.', 'success')
    return redirect(url_for('view_post', post_id=post_id))

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
    
    # Cloudinary 파일 삭제
    if post['cloudinary_public_id']:
        try:
            cloudinary.uploader.destroy(post['cloudinary_public_id'])
        except:
            pass
    
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
    parent_id = request.form.get('parent_id')
    
    if parent_id:
        parent_id = int(parent_id)
    else:
        parent_id = None
    
    password_hash = generate_password_hash(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute('''
            INSERT INTO comments (post_id, parent_id, author, password, content)
            VALUES (%s, %s, %s, %s, %s)
        ''', (post_id, parent_id, author, password_hash, content))
    else:
        cursor.execute('''
            INSERT INTO comments (post_id, parent_id, author, password, content)
            VALUES (?, ?, ?, ?, ?)
        ''', (post_id, parent_id, author, password_hash, content))
    
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

# 백업 API (Cloudinary 파일 정보 포함)
@app.route('/admin/backup')
def admin_backup():
    admin_password = request.args.get('password')
    
    if admin_password != ADMIN_PASSWORD:
        return "Unauthorized", 401
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    cursor.execute('SELECT * FROM posts ORDER BY id')
    posts = [dict(row) for row in cursor.fetchall()]
    
    # datetime 객체를 문자열로 변환
    for post in posts:
        if post.get('created_at') and hasattr(post['created_at'], 'isoformat'):
            post['created_at'] = post['created_at'].isoformat()
    
    cursor.execute('SELECT * FROM comments ORDER BY id')
    comments = [dict(row) for row in cursor.fetchall()]
    
    for comment in comments:
        if comment.get('created_at') and hasattr(comment['created_at'], 'isoformat'):
            comment['created_at'] = comment['created_at'].isoformat()
    
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

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
