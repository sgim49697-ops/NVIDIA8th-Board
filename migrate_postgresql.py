"""
PostgreSQL 전용 마이그레이션 스크립트
기존 게시판에 하이브리드 인증 시스템 추가

실행 방법:
    python migrate_postgresql.py
"""

from dotenv import load_dotenv
import os
import sys
import psycopg2

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다!")
    print()
    print("설정 방법:")
    print("  Windows CMD:")
    print("    set DATABASE_URL=postgresql://user:pass@host:port/dbname")
    print()
    print("  Windows PowerShell:")
    print("    $env:DATABASE_URL=\"postgresql://user:pass@host:port/dbname\"")
    print()
    print("  Linux/Mac:")
    print("    export DATABASE_URL=postgresql://user:pass@host:port/dbname")
    sys.exit(1)

# postgres:// → postgresql:// 변환
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def migrate():
    print("=" * 60)
    print("PostgreSQL 하이브리드 인증 시스템 마이그레이션")
    print("=" * 60)
    print()
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✓ PostgreSQL 연결 성공")
        cursor = conn.cursor()
        
        # 1. users 테이블 생성
        print("\n[1/4] users 테이블 생성 중...")
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
        print("✓ users 테이블 생성 완료")
        
        # 2. posts 테이블에 컬럼 추가
        print("\n[2/4] posts 테이블 업데이트 중...")
        try:
            cursor.execute('ALTER TABLE posts ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL')
            cursor.execute('ALTER TABLE posts ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)')
            cursor.execute('ALTER TABLE posts ADD COLUMN IF NOT EXISTS user_agent TEXT')
            print("✓ posts 테이블 컬럼 추가 완료")
        except Exception as e:
            print(f"  ℹ️  posts 테이블 컬럼이 이미 존재합니다: {e}")
        
        # 3. comments 테이블에 컬럼 추가
        print("\n[3/4] comments 테이블 업데이트 중...")
        try:
            cursor.execute('ALTER TABLE comments ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL')
            cursor.execute('ALTER TABLE comments ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)')
            cursor.execute('ALTER TABLE comments ADD COLUMN IF NOT EXISTS user_agent TEXT')
            print("✓ comments 테이블 컬럼 추가 완료")
        except Exception as e:
            print(f"  ℹ️  comments 테이블 컬럼이 이미 존재합니다: {e}")
        
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
        print("1. app_postgresql.py를 app.py로 복사")
        print("2. 템플릿 파일들 교체 (templates/ 폴더)")
        print("3. requirements_postgresql.txt를 requirements.txt로 복사")
        print("4. 환경변수 설정:")
        print("   - MAIL_USERNAME=your-email@gmail.com")
        print("   - MAIL_PASSWORD=your-app-password")
        print("   - SECRET_KEY=(새로 생성)")
        print("   - ADMIN_PASSWORD=(새로 생성)")
        print("5. pip install -r requirements.txt")
        print("6. python app.py")
        print()
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ PostgreSQL 연결 실패: {e}")
        print()
        print("DATABASE_URL을 확인해주세요:")
        print(f"  현재 설정: {DATABASE_URL[:30]}...")
        sys.exit(1)
    
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
    print(f"연결 대상: {DATABASE_URL[:50]}...")
    print()
    response = input("마이그레이션을 시작하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        migrate()
    else:
        print("마이그레이션이 취소되었습니다.")
