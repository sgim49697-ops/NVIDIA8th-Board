"""
데이터베이스 초기화 스크립트
1. 데이터베이스 생성
2. 테이블 생성
3. 기존 사용자 삭제
"""
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL이 설정되지 않았습니다!")
    exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# DATABASE_URL 파싱
from urllib.parse import urlparse

parsed = urlparse(DATABASE_URL)

db_params = {
    'host': parsed.hostname,
    'port': parsed.port or 5432,
    'user': parsed.username,
    'password': parsed.password,
    'database': parsed.path[1:]  # flask_board
}

print("=" * 60)
print("데이터베이스 초기화")
print("=" * 60)
print(f"호스트: {db_params['host']}")
print(f"포트: {db_params['port']}")
print(f"사용자: {db_params['user']}")
print(f"데이터베이스: {db_params['database']}")
print("=" * 60)
print()

try:
    # 1. postgres DB로 연결 (기본 DB)
    print("[1/4] postgres 데이터베이스 연결 중...")
    conn = psycopg2.connect(
        host=db_params['host'],
        port=db_params['port'],
        user=db_params['user'],
        password=db_params['password'],
        database='postgres'  # 기본 DB
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    print("✅ 연결 성공")

    # 2. flask_board DB 존재 확인
    print("\n[2/4] flask_board 데이터베이스 확인 중...")
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_params['database'],))
    exists = cursor.fetchone()

    if exists:
        print(f"✅ {db_params['database']} 데이터베이스가 이미 존재합니다.")
    else:
        print(f"데이터베이스가 없습니다. 생성 중...")
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(db_params['database'])
        ))
        print(f"✅ {db_params['database']} 데이터베이스 생성 완료")

    cursor.close()
    conn.close()

    # 3. flask_board DB로 연결
    print(f"\n[3/4] {db_params['database']} 데이터베이스 연결 중...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("✅ 연결 성공")

    # 4. 테이블 생성 (app.py의 init_db 함수 내용)
    print("\n[4/4] 테이블 생성 중...")

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
    print("✅ users 테이블")

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
    print("✅ posts 테이블")

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
    print("✅ comments 테이블")

    conn.commit()

    # 기존 데이터 확인
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM posts')
    post_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM comments')
    comment_count = cursor.fetchone()[0]

    print("\n" + "=" * 60)
    print("✅ 초기화 완료!")
    print("=" * 60)
    print(f"사용자: {user_count}명")
    print(f"게시글: {post_count}개")
    print(f"댓글: {comment_count}개")
    print("=" * 60)

    # ksg6346 사용자 삭제 (존재하면)
    if user_count > 0:
        print("\n중복 사용자 삭제 중...")
        cursor.execute("DELETE FROM users WHERE username = 'ksg6346'")
        if cursor.rowcount > 0:
            conn.commit()
            print("✅ 'ksg6346' 사용자 삭제 완료")
        else:
            print("ℹ️  'ksg6346' 사용자 없음")

    cursor.close()
    conn.close()

    print("\n이제 회원가입을 진행하세요!")

except psycopg2.OperationalError as e:
    print(f"❌ 연결 실패: {e}")
    print("\nDATABASE_URL을 확인하세요:")
    print(f"  현재: {DATABASE_URL[:50]}...")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback

    traceback.print_exc()