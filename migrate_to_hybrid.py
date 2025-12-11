"""
데이터베이스 마이그레이션 스크립트
기존 게시판에 하이브리드 인증 시스템 추가

실행 방법:
    python migrate_to_hybrid.py
"""

import os
import sys

# PostgreSQL/SQLite 자동 감지
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    import sqlite3

def migrate():
    print("=" * 60)
    print("하이브리드 인증 시스템 마이그레이션")
    print("=" * 60)
    print()
    
    if USE_POSTGRES:
        print("✓ PostgreSQL 감지")
        conn = psycopg2.connect(DATABASE_URL)
    else:
        print("✓ SQLite 감지")
        conn = sqlite3.connect('board.db')
    
    cursor = conn.cursor()
    
    try:
        # 1. users 테이블 생성
        print("\n[1/4] users 테이블 생성 중...")
        if USE_POSTGRES:
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
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email_verified INTEGER DEFAULT 0,
                    verification_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        print("✓ users 테이블 생성 완료")
        
        # 2. posts 테이블에 컬럼 추가
        print("\n[2/4] posts 테이블 업데이트 중...")
        
        if USE_POSTGRES:
            # PostgreSQL: ADD COLUMN IF NOT EXISTS 지원
            try:
                cursor.execute('ALTER TABLE posts ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL')
                cursor.execute('ALTER TABLE posts ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)')
                cursor.execute('ALTER TABLE posts ADD COLUMN IF NOT EXISTS user_agent TEXT')
                print("✓ posts 테이블 컬럼 추가 완료")
            except Exception as e:
                print(f"  ℹ️  posts 테이블 컬럼이 이미 존재합니다: {e}")
        else:
            # SQLite: 컬럼 존재 확인 후 추가
            cursor.execute("PRAGMA table_info(posts)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'user_id' not in columns:
                cursor.execute('ALTER TABLE posts ADD COLUMN user_id INTEGER')
                print("✓ posts.user_id 컬럼 추가")
            else:
                print("  ℹ️  posts.user_id 이미 존재")
            
            if 'ip_address' not in columns:
                cursor.execute('ALTER TABLE posts ADD COLUMN ip_address TEXT')
                print("✓ posts.ip_address 컬럼 추가")
            else:
                print("  ℹ️  posts.ip_address 이미 존재")
            
            if 'user_agent' not in columns:
                cursor.execute('ALTER TABLE posts ADD COLUMN user_agent TEXT')
                print("✓ posts.user_agent 컬럼 추가")
            else:
                print("  ℹ️  posts.user_agent 이미 존재")
        
        # 3. comments 테이블에 컬럼 추가
        print("\n[3/4] comments 테이블 업데이트 중...")
        
        if USE_POSTGRES:
            try:
                cursor.execute('ALTER TABLE comments ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL')
                cursor.execute('ALTER TABLE comments ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)')
                cursor.execute('ALTER TABLE comments ADD COLUMN IF NOT EXISTS user_agent TEXT')
                print("✓ comments 테이블 컬럼 추가 완료")
            except Exception as e:
                print(f"  ℹ️  comments 테이블 컬럼이 이미 존재합니다: {e}")
        else:
            cursor.execute("PRAGMA table_info(comments)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'user_id' not in columns:
                cursor.execute('ALTER TABLE comments ADD COLUMN user_id INTEGER')
                print("✓ comments.user_id 컬럼 추가")
            else:
                print("  ℹ️  comments.user_id 이미 존재")
            
            if 'ip_address' not in columns:
                cursor.execute('ALTER TABLE comments ADD COLUMN ip_address TEXT')
                print("✓ comments.ip_address 컬럼 추가")
            else:
                print("  ℹ️  comments.ip_address 이미 존재")
            
            if 'user_agent' not in columns:
                cursor.execute('ALTER TABLE comments ADD COLUMN user_agent TEXT')
                print("✓ comments.user_agent 컬럼 추가")
            else:
                print("  ℹ️  comments.user_agent 이미 존재")
        
        conn.commit()
        
        # 4. 기존 데이터 확인
        print("\n[4/4] 기존 데이터 확인 중...")
        cursor.execute('SELECT COUNT(*) FROM posts')
        post_count = cursor.fetchone()[0]
        print(f"✓ 기존 게시글 {post_count}개 유지됨 (user_id=NULL로 익명 게시글)")
        
        cursor.execute('SELECT COUNT(*) FROM comments')
        comment_count = cursor.fetchone()[0]
        print(f"✓ 기존 댓글 {comment_count}개 유지됨 (user_id=NULL로 익명 댓글)")
        
        print("\n" + "=" * 60)
        print("✅ 마이그레이션 완료!")
        print("=" * 60)
        print()
        print("다음 단계:")
        print("1. app_hybrid.py를 app.py로 복사")
        print("2. 템플릿 파일들 교체 (templates/ 폴더)")
        print("3. requirements_hybrid.txt를 requirements.txt로 복사")
        print("4. 환경변수 설정:")
        print("   - MAIL_USERNAME=your-email@gmail.com")
        print("   - MAIL_PASSWORD=your-app-password")
        print("5. pip install -r requirements.txt")
        print("6. python app.py")
        print()
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print()
    response = input("마이그레이션을 시작하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        migrate()
    else:
        print("마이그레이션이 취소되었습니다.")
