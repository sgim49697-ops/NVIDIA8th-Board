import os
import psycopg2

# Render 환경 변수에서 DATABASE_URL 가져오기
DATABASE_URL = os.environ.get('DATABASE_URL')


def fix_database():
    print("🔧 데이터베이스 구조 업데이트 시작...")

    if not DATABASE_URL:
        print("❌ 에러: DATABASE_URL 환경변수가 없습니다.")
        return

    # postgres:// 로 시작하면 postgresql:// 로 변경 (Render 호환성)
    db_url = DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # 1. comments 테이블에 parent_id 컬럼 추가 (대댓글용)
        print("1. comments 테이블 수정 중 (parent_id)...")
        cursor.execute("""
            ALTER TABLE comments 
            ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE;
        """)

        # 2. posts 테이블에 Cloudinary 관련 컬럼 추가
        print("2. posts 테이블 수정 중 (cloudinary columns)...")
        cursor.execute("""
            ALTER TABLE posts 
            ADD COLUMN IF NOT EXISTS cloudinary_url TEXT;
        """)

        cursor.execute("""
            ALTER TABLE posts 
            ADD COLUMN IF NOT EXISTS cloudinary_public_id TEXT;
        """)

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ 데이터베이스 업데이트가 완료되었습니다!")
        print("이제 대댓글과 Cloudinary 업로드가 정상 작동할 것입니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == '__main__':
    fix_database()