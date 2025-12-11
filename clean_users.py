"""
Render PostgreSQL 사용자 정리 스크립트
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

try:
    print("=" * 70)
    print("Render PostgreSQL 연결 중...")
    print("=" * 70)

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("✅ 연결 성공!")
    print()

    # 1. 현재 사용자 목록 조회
    print("📋 현재 등록된 사용자:")
    print("-" * 70)

    cursor.execute('''
        SELECT id, username, email, email_verified, created_at 
        FROM users 
        ORDER BY created_at DESC
    ''')
    users = cursor.fetchall()

    if not users:
        print("등록된 사용자가 없습니다.")
    else:
        for user in users:
            verified = "✓ 인증됨" if user['email_verified'] else "✗ 미인증"
            created = user['created_at'].strftime('%Y-%m-%d %H:%M') if user['created_at'] else 'N/A'
            print(f"ID: {user['id']:3d} | {user['username']:15s} | {user['email']:30s} | {verified:10s} | {created}")

    print("-" * 70)
    print(f"총 {len(users)}명")
    print()

    # 2. 삭제 옵션 선택
    print("선택하세요:")
    print("1. 특정 사용자 삭제")
    print("2. 전체 사용자 삭제")
    print("3. 취소")

    choice = input("\n선택 (1/2/3): ").strip()

    if choice == '1':
        username = input("삭제할 사용자명을 입력하세요: ").strip()
        if username:
            cursor.execute('DELETE FROM users WHERE username = %s', (username,))

            if cursor.rowcount > 0:
                conn.commit()
                print(f"\n✅ 사용자 '{username}' 삭제 완료!")
            else:
                print(f"\n❌ 사용자 '{username}'를 찾을 수 없습니다.")
        else:
            print("취소되었습니다.")

    elif choice == '2':
        confirm = input("\n⚠️  정말 모든 사용자를 삭제하시겠습니까? (yes 입력): ").strip()
        if confirm.lower() == 'yes':
            cursor.execute('DELETE FROM users')
            conn.commit()
            print(f"\n✅ 모든 사용자 ({len(users)}명) 삭제 완료!")
        else:
            print("취소되었습니다.")

    else:
        print("취소되었습니다.")

    cursor.close()
    conn.close()

    print("\n작업 완료!")

except psycopg2.OperationalError as e:
    print(f"❌ 연결 실패: {e}")
    print("\nRender PostgreSQL 연결 확인:")
    print("1. Render Dashboard → PostgreSQL 탭 확인")
    print("2. DATABASE_URL이 올바른지 확인")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback

    traceback.print_exc()