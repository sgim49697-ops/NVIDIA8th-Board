"""
기존 uploads 폴더의 파일을 Cloudinary로 마이그레이션하는 스크립트

사용법:
1. 환경변수 설정
2. python migrate_to_cloudinary.py 실행
"""

import os
import cloudinary
import cloudinary.uploader

# PostgreSQL/SQLite 자동 감지
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    import sqlite3

# Cloudinary 설정
CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
API_KEY = os.environ.get('CLOUDINARY_API_KEY')
API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

if not all([CLOUD_NAME, API_KEY, API_SECRET]):
    print("❌ 에러: Cloudinary 환경변수가 설정되지 않았습니다.")
    print("필요한 환경변수:")
    print("  - CLOUDINARY_CLOUD_NAME")
    print("  - CLOUDINARY_API_KEY")
    print("  - CLOUDINARY_API_SECRET")
    exit(1)

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET
)

UPLOADS_DIR = 'uploads'

def get_db_connection():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect('board.db')
        conn.row_factory = sqlite3.Row
        return conn

def migrate_files():
    print("=" * 60)
    print("📦 Cloudinary 파일 마이그레이션 시작")
    print("=" * 60)
    
    # uploads 폴더 확인
    if not os.path.exists(UPLOADS_DIR):
        print(f"❌ {UPLOADS_DIR} 폴더가 없습니다.")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    # 파일이 있는 게시글 조회
    cursor.execute("SELECT id, board_type, filename FROM posts WHERE filename IS NOT NULL")
    posts = [dict(row) for row in cursor.fetchall()]
    
    if not posts:
        print("📝 마이그레이션할 파일이 없습니다.")
        cursor.close()
        conn.close()
        return
    
    print(f"📝 마이그레이션할 게시글: {len(posts)}개\n")
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for idx, post in enumerate(posts, 1):
        post_id = post['id']
        board_type = post['board_type']
        filename = post['filename']
        file_path = os.path.join(UPLOADS_DIR, filename)
        
        print(f"[{idx}/{len(posts)}] {filename}... ", end="")
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            print("❌ 파일 없음")
            skip_count += 1
            continue
        
        try:
            # Cloudinary 업로드
            result = cloudinary.uploader.upload(
                file_path,
                folder=f"nvidia8th_board/{board_type}",
                resource_type="auto",
                use_filename=True
            )
            
            cloudinary_url = result['secure_url']
            cloudinary_public_id = result['public_id']
            
            # DB 업데이트
            if USE_POSTGRES:
                cursor.execute("""
                    UPDATE posts 
                    SET cloudinary_url = %s, cloudinary_public_id = %s
                    WHERE id = %s
                """, (cloudinary_url, cloudinary_public_id, post_id))
            else:
                cursor.execute("""
                    UPDATE posts 
                    SET cloudinary_url = ?, cloudinary_public_id = ?
                    WHERE id = ?
                """, (cloudinary_url, cloudinary_public_id, post_id))
            
            conn.commit()
            print(f"✅ 업로드 완료")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 실패: {str(e)}")
            fail_count += 1
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("📊 마이그레이션 완료")
    print("=" * 60)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"⏭️  스킵: {skip_count}개 (파일 없음)")
    print(f"📁 총합: {len(posts)}개")
    print("=" * 60)
    
    if success_count > 0:
        print("\n✨ 마이그레이션이 성공적으로 완료되었습니다!")
        print("이제 안전하게 재배포할 수 있습니다.")

if __name__ == '__main__':
    try:
        migrate_files()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 에러 발생: {str(e)}")
