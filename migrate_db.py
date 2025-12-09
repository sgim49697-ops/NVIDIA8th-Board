import sqlite3
import os

def migrate_database():
    """기존 데이터베이스를 새 구조로 마이그레이션"""
    
    if not os.path.exists('board.db'):
        print("❌ board.db 파일이 없습니다. 마이그레이션이 필요없습니다.")
        return
    
    print("🔄 데이터베이스 마이그레이션을 시작합니다...")
    
    conn = sqlite3.connect('board.db')
    cursor = conn.cursor()
    
    # 1. board_type 컬럼이 있는지 확인
    cursor.execute("PRAGMA table_info(posts)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'board_type' in columns:
        print("✅ board_type 컬럼이 이미 존재합니다.")
    else:
        print("📝 board_type 컬럼 추가 중...")
        # 기존 테이블 백업
        cursor.execute("""
            CREATE TABLE posts_backup AS SELECT * FROM posts
        """)
        
        # 기존 테이블 삭제
        cursor.execute("DROP TABLE posts")
        
        # 새 구조로 테이블 생성
        cursor.execute("""
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_type TEXT NOT NULL DEFAULT 'free',
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                password TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL,
                filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 데이터 복원 (기본값으로 'free' 게시판에, 비밀번호는 'legacy1234' 해시값)
        from werkzeug.security import generate_password_hash
        default_password_hash = generate_password_hash('legacy1234')
        
        cursor.execute("""
            INSERT INTO posts (id, board_type, title, author, password, content, filename, created_at)
            SELECT id, 'free', title, author, ?, content, filename, created_at
            FROM posts_backup
        """, (default_password_hash,))
        
        # 백업 테이블 삭제
        cursor.execute("DROP TABLE posts_backup")
        
        print(f"✅ {cursor.rowcount}개의 게시글을 마이그레이션했습니다.")
        print("⚠️  기존 게시글 비밀번호: legacy1234")
    
    # 2. password 컬럼 확인
    cursor.execute("PRAGMA table_info(posts)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'password' not in columns:
        print("❌ password 컬럼이 없습니다. 데이터베이스를 완전히 새로 만드는 것을 권장합니다.")
        conn.close()
        return
    
    # 3. comments 테이블 생성
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='comments'
    """)
    
    if cursor.fetchone():
        print("✅ comments 테이블이 이미 존재합니다.")
    else:
        print("📝 comments 테이블 생성 중...")
        cursor.execute("""
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                password TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        """)
        print("✅ comments 테이블을 생성했습니다.")
    
    conn.commit()
    conn.close()
    
    print("\n✅ 마이그레이션 완료!")
    print("=" * 50)
    print("📌 중요 정보:")
    print("   - 기존 게시글은 모두 '자유게시판'으로 분류됩니다")
    print("   - 기존 게시글 비밀번호: legacy1234")
    print("   - 관리자 비밀번호: admin1234")
    print("=" * 50)

if __name__ == "__main__":
    migrate_database()
