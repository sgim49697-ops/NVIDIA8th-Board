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
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_TIMEOUT'] = 50

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

def extract_first_image(html_content):
    """HTML 콘텐츠에서 첫 번째 이미지 URL 추출"""
    if not html_content:
        return None
    
    # <img> 태그에서 src 추출
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    match = re.search(img_pattern, html_content, re.IGNORECASE)
    
    if match:
        return match.group(1)
    return None

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
            author VARCHAR(50) NOT NULL,
            password VARCHAR(200),
            content TEXT NOT NULL,
            filename VARCHAR(200),
            cloudinary_url VARCHAR(500),
            cloudinary_public_id VARCHAR(200),
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            ip_address VARCHAR(50),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # comments 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            author VARCHAR(50) NOT NULL,
            password VARCHAR(200),
            content TEXT NOT NULL,
            parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            ip_address VARCHAR(50),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ 데이터베이스 초기화 완료!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # 한글, 영문, 숫자, 밑줄(_)만 허용 (3-50자)
        if not re.match(r'^[가-힣a-zA-Z0-9_]{3,50}$', username):
            flash('아이디는 한글, 영문, 숫자, 밑줄(_)만 사용 가능합니다 (3-50자)', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 8:
            flash('비밀번호는 8자 이상이어야 합니다.', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        token = serializer.dumps(email, salt='email-confirm')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password, verification_token) VALUES (%s, %s, %s, %s)',
                (username, email, hashed_password, token)
            )
            conn.commit()
            
            # 이메일 전송
            confirm_url = url_for('confirm_email', token=token, _external=True)
            msg = Message('이메일 인증', recipients=[email])
            msg.body = f'다음 링크를 클릭하여 이메일을 인증해주세요:\n{confirm_url}\n\n이 링크는 1시간 동안 유효합니다.'
            try:
                mail.send(msg)
                flash('인증 이메일이 발송되었습니다.', 'success')
            except Exception as mail_error:
                print(f"❌ 이메일 발송 실패: {mail_error}")
                flash('회원가입은 완료되었으나 이메일 발송 실패.', 'warning')
            
            flash('회원가입이 완료되었습니다! 이메일을 확인하여 인증을 완료해주세요.', 'success')
            return redirect(url_for('login'))
            
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if 'username' in str(e):
                flash('이미 사용 중인 아이디입니다.', 'error')
            elif 'email' in str(e):
                flash('이미 사용 중인 이메일입니다.', 'error')
            else:
                flash('회원가입 중 오류가 발생했습니다.', 'error')
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash('인증 링크가 만료되었습니다.', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE users SET email_verified = TRUE, verification_token = NULL WHERE email = %s',
        (email,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('이메일 인증이 완료되었습니다! 로그인해주세요.', 'success')
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
        
        if user and check_password_hash(user['password'], password):
            if not user['email_verified']:
                flash('이메일 인증이 필요합니다. 이메일을 확인해주세요.', 'error')
                return redirect(url_for('login'))
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('로그인되었습니다.', 'success')
            return redirect(url_for('index'))
        
        flash('아이디 또는 비밀번호가 일치하지 않습니다.', 'error')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('index'))

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT id, username, email, created_at FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.close()
        conn.close()
        return "사용자를 찾을 수 없습니다.", 404
    
    cursor.execute(
        'SELECT * FROM posts WHERE user_id = %s ORDER BY created_at DESC',
        (user_id,)
    )
    posts = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    is_own_profile = session.get('user_id') == user_id
    
    return render_template('user_profile.html', user=dict(user), posts=posts, is_own_profile=is_own_profile)

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
    
    # 각 게시글에 썸네일 추가 (본문 이미지 우선, 없으면 첨부 파일)
    for post in posts:
        # 1순위: 본문에서 첫 번째 이미지 추출
        content_image = extract_first_image(post.get('content', ''))
        
        if content_image:
            post['thumbnail'] = content_image
        elif post.get('cloudinary_url'):
            # 2순위: 첨부 파일
            post['thumbnail'] = post['cloudinary_url']
        else:
            post['thumbnail'] = None
    
    cursor.close()
    conn.close()
    
    return render_template('board.html', posts=posts, board_type=board_type, board_name=board_name)

@app.route('/write/<board_type>', methods=['GET', 'POST'])
def write(board_type):
    if board_type not in ['free', 'project']:
        return "잘못된 게시판입니다.", 404
    
    if request.method == 'POST':
        # ⭐ 익명 사용자 글 작성 제한 추가
        if 'user_id' not in session:
            flash('로그인 후 글을 작성할 수 있습니다.', 'error')
            return redirect(url_for('login'))
        
        title = request.form['title']
        content = request.form['content']
        
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        # 로그인 사용자만 글 작성 가능
        user_id = session['user_id']
        author = session['username']
        password_hash = None
        
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
    
    # ⭐ 로그인하지 않은 경우 로그인 페이지로 리다이렉트
    if not is_logged_in:
        flash('글을 작성하려면 로그인이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
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

@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    # ⭐ 로그인하지 않은 사용자는 댓글 작성 불가
    if 'user_id' not in session:
        flash('로그인 후 댓글을 작성할 수 있습니다.', 'error')
        return redirect(url_for('view_post', post_id=post_id))
    
    content = request.form['content']
    parent_id = request.form.get('parent_id')
    
    ip_address = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')
    
    # 로그인 사용자만 여기까지 도달
    user_id = session['user_id']
    author = session['username']
    password_hash = None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO comments (post_id, author, password, content, parent_id, user_id, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (post_id, author, password_hash, content, parent_id, user_id, ip_address, user_agent))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('댓글이 작성되었습니다.', 'success')
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    
    if post is None:
        cursor.close()
        conn.close()
        return "게시글을 찾을 수 없습니다.", 404
    
    post = dict(post)
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        is_admin = password == ADMIN_PASSWORD
        
        # 권한 확인
        if 'user_id' in session:
            if post['user_id'] != session['user_id'] and not is_admin:
                flash('수정 권한이 없습니다.', 'error')
                cursor.close()
                conn.close()
                return redirect(url_for('view_post', post_id=post_id))
        else:
            if not post['password'] or not check_password_hash(post['password'], password):
                if not is_admin:
                    flash('비밀번호가 일치하지 않습니다.', 'error')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('edit_post', post_id=post_id))
        
        title = request.form['title']
        content = request.form['content']
        
        file = request.files.get('file')
        
        if file and file.filename:
            if post['cloudinary_public_id']:
                try:
                    cloudinary.uploader.destroy(post['cloudinary_public_id'])
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
                
                cursor.execute('''
                    UPDATE posts 
                    SET title = %s, content = %s, filename = %s, 
                        cloudinary_url = %s, cloudinary_public_id = %s
                    WHERE id = %s
                ''', (title, content, filename, cloudinary_url, cloudinary_public_id, post_id))
            except Exception as e:
                flash(f'파일 업로드 실패: {str(e)}', 'error')
                cursor.close()
                conn.close()
                return redirect(url_for('edit_post', post_id=post_id))
        else:
            cursor.execute('''
                UPDATE posts 
                SET title = %s, content = %s
                WHERE id = %s
            ''', (title, content, post_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('게시글이 수정되었습니다.', 'success')
        return redirect(url_for('view_post', post_id=post_id))
    
    cursor.close()
    conn.close()
    
    is_author = False
    if 'user_id' in session and post['user_id'] == session['user_id']:
        is_author = True
    
    board_name = '자유게시판' if post['board_type'] == 'free' else '프로젝트게시판'
    return render_template('edit.html', post=post, board_name=board_name, is_author=is_author)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    password = request.form.get('password', '')
    is_admin = password == ADMIN_PASSWORD
    
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
    if 'user_id' in session:
        if post['user_id'] != session['user_id'] and not is_admin:
            flash('삭제 권한이 없습니다.', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('view_post', post_id=post_id))
    else:
        if not post['password'] or not check_password_hash(post['password'], password):
            if not is_admin:
                flash('비밀번호가 일치하지 않습니다.', 'error')
                cursor.close()
                conn.close()
                return redirect(url_for('view_post', post_id=post_id))
    
    # Cloudinary 파일 삭제
    if post['cloudinary_public_id']:
        try:
            cloudinary.uploader.destroy(post['cloudinary_public_id'])
        except:
            pass
    
    cursor.execute('DELETE FROM posts WHERE id = %s', (post_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('게시글이 삭제되었습니다.', 'success')
    return redirect(url_for('board', board_type=post['board_type']))

@app.route('/comment/<int:comment_id>/edit', methods=['POST'])
def edit_comment(comment_id):
    content = request.form['content']
    password = request.form.get('password', '')
    is_admin = password == ADMIN_PASSWORD
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM comments WHERE id = %s', (comment_id,))
    comment = cursor.fetchone()
    
    if comment is None:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': '댓글을 찾을 수 없습니다.'})
    
    comment = dict(comment)
    
    # 권한 확인
    if 'user_id' in session:
        if comment['user_id'] != session['user_id'] and not is_admin:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '수정 권한이 없습니다.'})
    else:
        if not comment['password'] or not check_password_hash(comment['password'], password):
            if not is_admin:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '비밀번호가 일치하지 않습니다.'})
    
    cursor.execute('UPDATE comments SET content = %s WHERE id = %s', (content, comment_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': '댓글이 수정되었습니다.'})

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    password = request.form.get('password', '')
    is_admin = password == ADMIN_PASSWORD
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM comments WHERE id = %s', (comment_id,))
    comment = cursor.fetchone()
    
    if comment is None:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': '댓글을 찾을 수 없습니다.'})
    
    comment = dict(comment)
    post_id = comment['post_id']
    
    # 권한 확인
    if 'user_id' in session:
        if comment['user_id'] != session['user_id'] and not is_admin:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '삭제 권한이 없습니다.'})
    else:
        if not comment['password'] or not check_password_hash(comment['password'], password):
            if not is_admin:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '비밀번호가 일치하지 않습니다.'})
    
    cursor.execute('DELETE FROM comments WHERE id = %s', (comment_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': '댓글이 삭제되었습니다.', 'redirect': url_for('view_post', post_id=post_id)})

@app.route('/admin/delete-user', methods=['POST'])
def admin_delete_user():
    admin_password = request.form.get('admin_password', '')
    user_id = request.form.get('user_id')
    
    if admin_password != ADMIN_PASSWORD:
        flash('관리자 비밀번호가 일치하지 않습니다.', 'error')
        return redirect(url_for('user_profile', user_id=user_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 사용자 삭제 (CASCADE로 관련 게시글/댓글도 자동 삭제)
    cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    # 삭제된 사용자가 로그인 중이면 로그아웃
    if session.get('user_id') == int(user_id):
        session.clear()
    
    flash('사용자가 삭제되었습니다.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/delete-anonymous', methods=['POST'])
def admin_delete_anonymous():
    admin_password = request.form.get('admin_password', '')
    post_id = request.form.get('post_id')
    
    if admin_password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'message': '관리자 비밀번호가 일치하지 않습니다.'})
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    
    if not post:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': '게시글을 찾을 수 없습니다.'})
    
    post = dict(post)
    
    # Cloudinary 파일 삭제
    if post['cloudinary_public_id']:
        try:
            cloudinary.uploader.destroy(post['cloudinary_public_id'])
        except:
            pass
    
    cursor.execute('DELETE FROM posts WHERE id = %s', (post_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': '게시글이 삭제되었습니다.', 'redirect': url_for('board', board_type=post['board_type'])})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
