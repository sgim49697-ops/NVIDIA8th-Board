import os
import json
from datetime import datetime

# 환경 감지
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    def get_db_connection():
        return psycopg2.connect(DATABASE_URL)
else:
    import sqlite3
    
    def get_db_connection():
        conn = sqlite3.connect('board.db')
        conn.row_factory = sqlite3.Row
        return conn

def backup_database():
    """데이터베이스를 JSON 파일로 백업"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backup_{timestamp}.json'
    
    print(f"🔄 백업 시작... ({backup_file})")
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) if USE_POSTGRES else conn.cursor()
    
    # 게시글 백업
    cursor.execute('SELECT * FROM posts ORDER BY id')
    posts = [dict(row) for row in cursor.fetchall()]
    
    # 댓글 백업
    cursor.execute('SELECT * FROM comments ORDER BY id')
    comments = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    # JSON으로 저장
    backup_data = {
        'backup_date': timestamp,
        'database_type': 'PostgreSQL' if USE_POSTGRES else 'SQLite',
        'posts_count': len(posts),
        'comments_count': len(comments),
        'posts': posts,
        'comments': comments
    }
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ 백업 완료!")
    print(f"   파일: {backup_file}")
    print(f"   게시글: {len(posts)}개")
    print(f"   댓글: {len(comments)}개")
    
    return backup_file

def restore_database(backup_file):
    """JSON 백업 파일에서 데이터베이스 복원"""
    
    if not os.path.exists(backup_file):
        print(f"❌ 백업 파일을 찾을 수 없습니다: {backup_file}")
        return
    
    print(f"🔄 복원 시작... ({backup_file})")
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 기존 데이터 삭제 확인
    confirm = input("⚠️  기존 데이터를 모두 삭제하고 복원하시겠습니까? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 복원 취소")
        return
    
    # 기존 데이터 삭제
    cursor.execute('DELETE FROM comments')
    cursor.execute('DELETE FROM posts')
    
    # 게시글 복원
    for post in backup_data['posts']:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO posts (id, board_type, title, author, password, content, filename, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (post['id'], post['board_type'], post['title'], post['author'], 
                  post['password'], post['content'], post['filename'], post['created_at']))
        else:
            cursor.execute('''
                INSERT INTO posts (id, board_type, title, author, password, content, filename, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (post['id'], post['board_type'], post['title'], post['author'], 
                  post['password'], post['content'], post['filename'], post['created_at']))
    
    # 댓글 복원
    for comment in backup_data['comments']:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO comments (id, post_id, author, password, content, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (comment['id'], comment['post_id'], comment['author'], 
                  comment['password'], comment['content'], comment['created_at']))
        else:
            cursor.execute('''
                INSERT INTO comments (id, post_id, author, password, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (comment['id'], comment['post_id'], comment['author'], 
                  comment['password'], comment['content'], comment['created_at']))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ 복원 완료!")
    print(f"   게시글: {len(backup_data['posts'])}개")
    print(f"   댓글: {len(backup_data['comments'])}개")

def list_backups():
    """백업 파일 목록 보기"""
    backups = [f for f in os.listdir('.') if f.startswith('backup_') and f.endswith('.json')]
    
    if not backups:
        print("❌ 백업 파일이 없습니다.")
        return
    
    print(f"\n📁 백업 파일 목록 ({len(backups)}개):")
    print("=" * 60)
    
    for backup in sorted(backups, reverse=True):
        try:
            with open(backup, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📄 {backup}")
            print(f"   - 날짜: {data['backup_date']}")
            print(f"   - DB: {data['database_type']}")
            print(f"   - 게시글: {data['posts_count']}개, 댓글: {data['comments_count']}개")
            print()
        except:
            print(f"❌ {backup} (손상된 파일)")
    
    print("=" * 60)

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🗄️  데이터베이스 백업/복원 도구")
    print("=" * 60)
    print()
    
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python backup_db.py backup           # 백업")
        print("  python backup_db.py restore <파일>   # 복원")
        print("  python backup_db.py list             # 백업 목록")
        print()
        print("예시:")
        print("  python backup_db.py backup")
        print("  python backup_db.py restore backup_20251209_120000.json")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'backup':
        backup_database()
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("❌ 복원할 백업 파일을 지정하세요.")
            print("   예: python backup_db.py restore backup_20251209_120000.json")
            sys.exit(1)
        restore_database(sys.argv[2])
    elif command == 'list':
        list_backups()
    else:
        print(f"❌ 알 수 없는 명령어: {command}")
        print("   사용 가능한 명령어: backup, restore, list")
        sys.exit(1)
