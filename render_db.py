"""
Render PostgreSQL 직접 관리 스크립트
"""
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL이 설정되지 않았습니다!")
    exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def show_connection_info():
    """연결 정보 표시"""
    from urllib.parse import urlparse
    parsed = urlparse(DATABASE_URL)
    
    print("=" * 80)
    print("Render PostgreSQL 연결 정보")
    print("=" * 80)
    print(f"Host: {parsed.hostname}")
    print(f"Port: {parsed.port or 5432}")
    print(f"User: {parsed.username}")
    print(f"Database: {parsed.path[1:]}")
    print(f"Password: {'*' * 20}")
    print("=" * 80)
    print()
    
    # psql 명령어 생성
    print("로컬 CMD에서 접속하려면:")
    print("-" * 80)
    print(f'psql -h {parsed.hostname} -p {parsed.port or 5432} -U {parsed.username} -d {parsed.path[1:]}')
    print("-" * 80)
    print()

def connect():
    """데이터베이스 연결"""
    return psycopg2.connect(DATABASE_URL)

def list_users():
    """사용자 목록"""
    conn = connect()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT id, username, email, email_verified, created_at 
        FROM users 
        ORDER BY created_at DESC
    ''')
    users = cursor.fetchall()
    
    print("📋 등록된 사용자:")
    print("=" * 100)
    print(f"{'ID':<5} | {'아이디':<20} | {'이메일':<35} | {'인증상태':<10} | {'가입일'}")
    print("-" * 100)
    
    if not users:
        print("등록된 사용자가 없습니다.")
    else:
        for user in users:
            verified = "✓ 인증됨" if user['email_verified'] else "✗ 미인증"
            created = user['created_at'].strftime('%Y-%m-%d %H:%M') if user['created_at'] else 'N/A'
            print(f"{user['id']:<5} | {user['username']:<20} | {user['email']:<35} | {verified:<10} | {created}")
    
    print("-" * 100)
    print(f"총 {len(users)}명\n")
    
    cursor.close()
    conn.close()

def list_posts():
    """게시글 목록"""
    conn = connect()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT p.id, p.title, p.author, p.board_type, p.user_id, p.created_at,
               u.username as registered_user
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
        LIMIT 20
    ''')
    posts = cursor.fetchall()
    
    print("📝 최근 게시글:")
    print("=" * 100)
    print(f"{'ID':<5} | {'제목':<30} | {'작성자':<15} | {'유형':<8} | {'등록일'}")
    print("-" * 100)
    
    if not posts:
        print("게시글이 없습니다.")
    else:
        for post in posts:
            if post['user_id']:
                author = f"{post['author']} (✓회원)"
            else:
                author = f"{post['author']} (익명)"
            
            board_name = "자유" if post['board_type'] == 'free' else "프로젝트"
            created = post['created_at'].strftime('%Y-%m-%d %H:%M') if post['created_at'] else 'N/A'
            title = post['title'][:28] + '..' if len(post['title']) > 30 else post['title']
            
            print(f"{post['id']:<5} | {title:<30} | {author:<15} | {board_name:<8} | {created}")
    
    print("-" * 100)
    print(f"총 {len(posts)}개\n")
    
    cursor.close()
    conn.close()

def list_comments():
    """댓글 목록"""
    conn = connect()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT c.id, c.content, c.author, c.user_id, c.created_at, 
               p.title as post_title, p.id as post_id
        FROM comments c
        JOIN posts p ON c.post_id = p.id
        ORDER BY c.created_at DESC
        LIMIT 20
    ''')
    comments = cursor.fetchall()
    
    print("💬 최근 댓글:")
    print("=" * 100)
    print(f"{'ID':<5} | {'댓글 내용':<35} | {'작성자':<15} | {'게시글':<20} | {'등록일'}")
    print("-" * 100)
    
    if not comments:
        print("댓글이 없습니다.")
    else:
        for comment in comments:
            if comment['user_id']:
                author = f"{comment['author']} (✓회원)"
            else:
                author = f"{comment['author']} (익명)"
            
            content = comment['content'][:33] + '..' if len(comment['content']) > 35 else comment['content']
            # HTML 태그 제거
            content = content.replace('<p>', '').replace('</p>', '').replace('<br>', ' ')
            
            post_title = comment['post_title'][:18] + '..' if len(comment['post_title']) > 20 else comment['post_title']
            created = comment['created_at'].strftime('%Y-%m-%d %H:%M') if comment['created_at'] else 'N/A'
            
            print(f"{comment['id']:<5} | {content:<35} | {author:<15} | {post_title:<20} | {created}")
    
    print("-" * 100)
    print(f"총 {len(comments)}개\n")
    
    cursor.close()
    conn.close()

def delete_user():
    """사용자 삭제"""
    list_users()
    
    print("삭제할 사용자 ID를 입력하세요 (취소: 0):")
    user_id = input(">>> ").strip()
    
    if user_id == '0':
        print("취소되었습니다.")
        return
    
    try:
        user_id = int(user_id)
    except ValueError:
        print("❌ 올바른 숫자를 입력하세요.")
        return
    
    conn = connect()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 사용자 정보 확인
    cursor.execute('SELECT username, email FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ ID {user_id} 사용자를 찾을 수 없습니다.")
        cursor.close()
        conn.close()
        return
    
    confirm = input(f"\n정말 '{user['username']}' ({user['email']}) 사용자를 삭제하시겠습니까? (yes/no): ").strip()
    
    if confirm.lower() == 'yes':
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        print(f"✅ 사용자 삭제 완료!")
    else:
        print("취소되었습니다.")
    
    cursor.close()
    conn.close()

def verify_user():
    """사용자 이메일 강제 인증"""
    list_users()
    
    print("인증할 사용자 ID를 입력하세요 (취소: 0):")
    user_id = input(">>> ").strip()
    
    if user_id == '0':
        print("취소되었습니다.")
        return
    
    try:
        user_id = int(user_id)
    except ValueError:
        print("❌ 올바른 숫자를 입력하세요.")
        return
    
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET email_verified = TRUE, verification_token = NULL
        WHERE id = %s
    ''', (user_id,))
    
    if cursor.rowcount > 0:
        conn.commit()
        print(f"✅ ID {user_id} 사용자 이메일 인증 완료!")
    else:
        print(f"❌ ID {user_id} 사용자를 찾을 수 없습니다.")
    
    cursor.close()
    conn.close()

def execute_sql():
    """SQL 쿼리 실행"""
    print("SQL 쿼리를 입력하세요 (종료: exit, 도움말: help):")
    print()
    
    conn = connect()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    while True:
        query = input("\nSQL> ").strip()
        
        if query.lower() == 'exit':
            break
        
        if query.lower() == 'help':
            print("""
도움말:
  SELECT * FROM users;              - 모든 사용자 조회
  SELECT * FROM posts;              - 모든 게시글 조회
  SELECT * FROM comments;           - 모든 댓글 조회
  DELETE FROM users WHERE id = 1;   - ID 1 사용자 삭제
  UPDATE users SET email_verified = TRUE WHERE id = 1;  - 이메일 인증
  \\dt                              - 테이블 목록
  exit                              - 종료
            """)
            continue
        
        if not query:
            continue
        
        try:
            cursor.execute(query)
            
            if query.upper().startswith('SELECT') or query.startswith('\\'):
                results = cursor.fetchall()
                if results:
                    print(f"\n결과: {len(results)}행")
                    print("-" * 80)
                    for i, row in enumerate(results[:10], 1):  # 처음 10개만
                        print(f"{i}. {dict(row)}")
                    if len(results) > 10:
                        print(f"... 외 {len(results) - 10}개")
                    print("-" * 80)
                else:
                    print("결과 없음")
            else:
                conn.commit()
                print(f"✅ {cursor.rowcount}행 영향받음")
                
        except Exception as e:
            conn.rollback()
            print(f"❌ 오류: {e}")
    
    cursor.close()
    conn.close()
    print("\nSQL 모드 종료")

if __name__ == '__main__':
    import sys
    
    print()
    show_connection_info()
    
    if len(sys.argv) < 2:
        print("사용법:")
        print("=" * 80)
        print("  python render_db.py info         # 연결 정보 확인")
        print("  python render_db.py users        # 사용자 목록 (ID, 이메일 포함)")
        print("  python render_db.py posts        # 게시글 목록")
        print("  python render_db.py comments     # 댓글 목록")
        print("  python render_db.py delete       # 사용자 삭제")
        print("  python render_db.py verify       # 사용자 강제 인증")
        print("  python render_db.py sql          # SQL 직접 실행")
        print("=" * 80)
        print()
        sys.exit(0)
    
    command = sys.argv[1]
    
    try:
        if command == 'info':
            pass  # 이미 출력됨
        elif command == 'users':
            list_users()
        elif command == 'posts':
            list_posts()
        elif command == 'comments':
            list_comments()
        elif command == 'delete':
            delete_user()
        elif command == 'verify':
            verify_user()
        elif command == 'sql':
            execute_sql()
        else:
            print("❌ 잘못된 명령어입니다.")
    except psycopg2.OperationalError as e:
        print(f"❌ 연결 실패: {e}")
        print("\n확인사항:")
        print("1. DATABASE_URL이 Render PostgreSQL URL인지 확인")
        print("2. 인터넷 연결 확인")
        print("3. Render PostgreSQL 서비스가 실행 중인지 확인")
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
