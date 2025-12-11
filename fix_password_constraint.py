"""
posts와 comments 테이블의 password 컬럼 NULL 허용으로 변경
"""
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL이 설정되지 않았습니다!")
    exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    print("=" * 60)
    print("password 컬럼 NULL 허용으로 변경")
    print("=" * 60)

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("\n[1/2] posts 테이블 수정 중...")
    cursor.execute('ALTER TABLE posts ALTER COLUMN password DROP NOT NULL')
    print("✅ posts.password → NULL 허용")

    print("\n[2/2] comments 테이블 수정 중...")
    cursor.execute('ALTER TABLE comments ALTER COLUMN password DROP NOT NULL')
    print("✅ comments.password → NULL 허용")

    conn.commit()

    print("\n" + "=" * 60)
    print("✅ 수정 완료!")
    print("=" * 60)
    print("\n이제 로그인 사용자도 글을 쓸 수 있습니다!")

    cursor.close()
    conn.close()

except psycopg2.OperationalError as e:
    print(f"❌ 연결 실패: {e}")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback

    traceback.print_exc()