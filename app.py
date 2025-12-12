from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from functools import wraps
import os
import re
from datetime import datetime
import cloudinary
import cloudinary.uploader
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

app = Flask(__name__)

# 환경변수 검증
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("❌ SECRET_KEY 환경변수가 설정되지 않았습니다!")

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    raise ValueError("❌ ADMIN_PASSWORD 환경변수가 설정되지 않았습니다!")

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL 환경변수가 설정되지 않았습니다! PostgreSQL 연결 정보가 필요합니다.")

# postgres:// → postgresql:// 변환
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Flask-Mail 설정
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_TIMEOUT'] = 120  # 타임아웃 30초 설정

if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
    raise ValueError("❌ MAIL_USERNAME 또는 MAIL_PASSWORD 환경변수가 설정되지 않았습니다!")

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Cloudinary 설정
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

def get_db_connection():
    """PostgreSQL 데이터베이스 연결"""
    return psycopg2.connect(DATABASE_URL)

def get_client_ip():
    """실제 클라이언트 IP 가져오기"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def login_required(f):
    """로그인 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    """데이터베이스 초기화 (PostgreSQL 전용)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # users 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            email_verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # posts 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            board_type VARCHAR(20) NOT NULL,
            title VARCHAR(200) NOT NULL,
            author VARCHAR(100) NOT NULL,
            password VARCHAR(200),
            content TEXT,
            filename VARCHAR(200),
            cloudinary_url TEXT,
            cloudinary_public_id TEXT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # comments 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
            parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
            author VARCHAR(100) NOT NULL,
            password VARCHAR(200),
            content TEXT NOT NULL,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ PostgreSQL 데이터베이스 초기화 완료")

# ==================== 회원 시스템 ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # 아이디 유효성 검사 (한글, 영문, 숫자, 밑줄 허용)
        if not re.match(r'^[가-힣a-zA-Z0-9_]{3,50}$', username):
            flash('아이디는 한글, 영문, 숫자, 밑줄(_)만 사용 가능합니다 (3-50자)', 'error')
            return redirect(url_for('register'))

        if len(password) < 8:
            flash('비밀번호는 8자 이상이어야 합니다.', 'error')
            return redirect(url_for('register'))
        
        password_hash = generate_password_hash(password)
        token = serializer.dumps(email, salt='email-confirm')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password, verification_token)
                VALUES (%s, %s, %s, %s)
            ''', (username, email, password_hash, token))
            
            conn.commit()
            
            # 이메일 발송을 별도로 try-except 처리
            try:
                # 인증 이메일 발송
                confirm_url = url_for('confirm_email', token=token, _external=True)
                msg = Message('NVIDIA 8th 게시판 - 이메일 인증', recipients=[email])
                msg.body = f'''
안녕하세요 {username}님,

NVIDIA 8th 게시판 가입을 환영합니다!

아래 링크를 클릭하여 이메일을 인증해주세요:
{confirm_url}

※ 이 링크는 1시간 동안 유효합니다.

감사합니다.
'''
                mail.send(msg)
                flash('인증 이메일이 발송되었습니다. 이메일을 확인해주세요.', 'success')
                
            except Exception as mail_error:
                # 이메일 발송 실패해도 회원가입은 완료됨
                print(f"❌ 이메일 발송 실패: {type(mail_error).__name__}: {str(mail_error)}")
                flash('회원가입은 완료되었으나 인증 이메일 발송에 실패했습니다. 관리자에게 문의하세요.', 'warning')
            
            return redirect(url_for('login'))
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 회원가입 오류: {type(e).__name__}: {str(e)}")
            flash(f'회원가입 실패: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('register.html')

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash('인증 링크가 만료되었습니다. 다시 가입해주세요.', 'error')
        return redirect(url_for('register'))
    except:
        flash('잘못된 인증 링크입니다.', 'error')
        return redirect(url_for('register'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET email_verified = TRUE, verification_token = NULL
        WHERE email = %s
    ''', (email,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('이메일 인증이 완료되었습니다. 로그인해주세요.', 'success')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            user = dict(user)
            if check_password_hash(user['password'], password):
                if not user['email_verified']:
                    flash('이메일 인증을 먼저 완료해주세요.', 'error')
                    return redirect(url_for('login'))
                
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash(f'{username}님 환영합니다!', 'success')
                return redirect(url_for('index'))
        
        flash('아이디 또는 비밀번호가 일치하지 않습니다.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username')
    session.clear()
    if username:
        flash(f'{username}님 로그아웃되었습니다.', 'success')
    return redirect(url_for('index'))

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT id, username, created_at FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.close()
        conn.close()
        return "사용자를 찾을 수 없습니다.", 404
    
    user = dict(user)
    
    # 작성 글
    cursor.execute('''
        SELECT id, title, board_type, created_at 
        FROM posts 
        WHERE user_id = %s 
        ORDER BY created_at DESC
        LIMIT 20
    ''', (user_id,))
    posts = [dict(row) for row in cursor.fetchall()]
    
    # 작성 댓글
    cursor.execute('''
        SELECT c.id, c.content, c.created_at, p.id as post_id, p.title as post_title
        FROM comments c
        JOIN posts p ON c.post_id = p.id
        WHERE c.user_id = %s
        ORDER BY c.created_at DESC
        LIMIT 20
    ''', (user_id,))
    comments = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template('user_profile.html', user=user, posts=posts, comments=comments)

# ==================== 게시판 ====================

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        "SELECT * FROM posts WHERE board_type = %s ORDER BY created_at DESC LIMIT 5",
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        'SELECT * FROM posts WHERE board_type = %s ORDER BY created_at DESC',
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
        content = request.form['content']
        
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        # 로그인 여부에 따라 처리
        if 'user_id' in session:
            user_id = session['user_id']
            author = session['username']
            password_hash = None
        else:
            user_id = None
            author = request.form['author']
            password = request.form['password']
            password_hash = generate_password_hash(password)
        
        file = request.files.get('file')
        cloudinary_url = None
        cloudinary_public_id = None
        filename = None
        
        if file and file.filename:
            filename = secure_filename(file.filename)
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
        
        cursor.execute('''
            INSERT INTO posts (board_type, title, author, password, content, filename, 
                              cloudinary_url, cloudinary_public_id, user_id, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (board_type, title, author, password_hash, content, filename, 
              cloudinary_url, cloudinary_public_id, user_id, ip_address, user_agent))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('게시글이 작성되었습니다.', 'success')
        return redirect(url_for('board', board_type=board_type))
    
    board_name = '자유게시판' if board_type == 'free' else '프로젝트게시판'
    is_logged_in = 'user_id' in session
    return render_template('write.html', board_type=board_type, board_name=board_name, is_logged_in=is_logged_in)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    
    if post is None:
        cursor.close()
        conn.close()
        return "게시글을 찾을 수 없습니다.", 404
    
    post = dict(post)
    
    # 댓글 및 대댓글 조회
    cursor.execute(
        'SELECT * FROM comments WHERE post_id = %s ORDER BY created_at ASC',
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
    
    # 작성자 확인
    is_author = False
    if 'user_id' in session and post['user_id'] == session['user_id']:
        is_author = True
    
    return render_template('view.html', post=post, comments=comments, is_author=is_author)

@app.route('/post/<int:post_id>/edit', methods=['POST'])
def edit_post(post_id):
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    
    if post is None:
        cursor.close()
        conn.close()
        return "게시글을 찾을 수 없습니다.", 404
    
    post = dict(post)
    
    # 권한 확인
    is_admin = password == ADMIN_PASSWORD
    is_author = False
    
    if post['user_id'] and 'user_id' in session and post['user_id'] == session['user_id']:
        is_author = True
    elif post['password']:
        is_author = check_password_hash(post['password'], password)
    
    if not (is_admin or is_author):
        cursor.close()
        conn.close()
        flash('비밀번호가 일치하지 않습니다.', 'error')
        return redirect(url_for('view_post', post_id=post_id))
    
    cursor.close()
    conn.close()
    
    return render_template('edit.html', post=post)

@app.route('/post/<int:post_id>/update', methods=['POST'])
def update_post(post_id):
    title = request.form['title']
    content = request.form['content']
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    
    if post is None:
        cursor.close()
        conn.close()
        return "게시글을 찾을 수 없습니다.", 404
    
    post = dict(post)
    
    # 권한 확인
    is_admin = password == ADMIN_PASSWORD
    is_author = False
    
    if post['user_id'] and 'user_id' in session and post['user_id'] == session['user_id']:
        is_author = True
    elif post['password']:
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
    
    if request.form.get('delete_file') == 'on':
        if cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(cloudinary_public_id)
            except:
                pass
        cloudinary_url = None
        cloudinary_public_id = None
        filename = None
    
    if file and file.filename:
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
    
    cursor.execute('''
        UPDATE posts 
        SET title = %s, content = %s, filename = %s, cloudinary_url = %s, cloudinary_public_id = %s
        WHERE id = %s
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    
    if post is None:
        cursor.close()
        conn.close()
        return "게시글을 찾을 수 없습니다.", 404
    
    post = dict(post)
    
    # 권한 확인
    is_admin = password == ADMIN_PASSWORD
    is_author = False
    
    if post['user_id'] and 'user_id' in session and post['user_id'] == session['user_id']:
        is_author = True
    elif post['password']:
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
    
    cursor.execute('DELETE FROM comments WHERE post_id = %s', (post_id,))
    cursor.execute('DELETE FROM posts WHERE id = %s', (post_id,))
    
    conn.commit()
    board_type = post['board_type']
    cursor.close()
    conn.close()
    
    flash('게시글이 삭제되었습니다.', 'success')
    return redirect(url_for('board', board_type=board_type))

@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    content = request.form['content']
    parent_id = request.form.get('parent_id')
    
    if parent_id:
        parent_id = int(parent_id)
    else:
        parent_id = None
    
    ip_address = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')
    
    # 로그인 여부에 따라 처리
    if 'user_id' in session:
        user_id = session['user_id']
        author = session['username']
        password_hash = None
    else:
        user_id = None
        author = request.form['author']
        password = request.form['password']
        password_hash = generate_password_hash(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO comments (post_id, parent_id, author, password, content, user_id, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (post_id, parent_id, author, password_hash, content, user_id, ip_address, user_agent))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('댓글이 작성되었습니다.', 'success')
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM comments WHERE id = %s', (comment_id,))
    comment = cursor.fetchone()
    
    if comment is None:
        cursor.close()
        conn.close()
        flash('댓글을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))
    
    comment = dict(comment)
    
    # 권한 확인
    is_admin = password == ADMIN_PASSWORD
    is_author = False
    
    if comment['user_id'] and 'user_id' in session and comment['user_id'] == session['user_id']:
        is_author = True
    elif comment['password']:
        is_author = check_password_hash(comment['password'], password)
    
    if not (is_admin or is_author):
        cursor.close()
        conn.close()
        flash('비밀번호가 일치하지 않습니다.', 'error')
        return redirect(url_for('view_post', post_id=comment['post_id']))
    
    post_id = comment['post_id']
    
    cursor.execute('DELETE FROM comments WHERE id = %s', (comment_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('댓글이 삭제되었습니다.', 'success')
    return redirect(url_for('view_post', post_id=post_id))

# ==================== 관리자 ====================

@app.route('/admin/backup')
def admin_backup():
    admin_password = request.args.get('password')
    
    if admin_password != ADMIN_PASSWORD:
        return "Unauthorized", 401
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM posts ORDER BY id')
    posts = [dict(row) for row in cursor.fetchall()]
    
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
        'database_type': 'PostgreSQL',
        'posts_count': len(posts),
        'comments_count': len(comments),
        'posts': posts,
        'comments': comments
    }
    
    return jsonify(backup_data)

@app.route('/admin/user-activity')
def admin_user_activity():
    password = request.args.get('password')
    if password != ADMIN_PASSWORD:
        return "Unauthorized", 401
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT 
            u.id, u.username, u.email, u.created_at,
            COUNT(DISTINCT p.id) as post_count,
            COUNT(DISTINCT c.id) as comment_count
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
        LEFT JOIN comments c ON u.id = c.user_id
        GROUP BY u.id, u.username, u.email, u.created_at
        ORDER BY u.created_at DESC
    ''')
    users = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    html = '<h1>사용자 활동 현황</h1><table border="1"><tr><th>ID</th><th>아이디</th><th>이메일</th><th>게시글</th><th>댓글</th><th>가입일</th></tr>'
    for user in users:
        html += f'<tr><td>{user["id"]}</td><td><a href="/user/{user["id"]}">{user["username"]}</a></td><td>{user["email"]}</td><td>{user["post_count"]}</td><td>{user["comment_count"]}</td><td>{user["created_at"]}</td></tr>'
    html += '</table>'
    
    return html

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
