import requests
import json
from datetime import datetime

def fetch_render_data(base_url):
    """
    Render에서 실행 중인 앱의 데이터를 추출
    base_url: https://your-app.onrender.com
    """
    
    print(f"🔄 {base_url}에서 데이터 가져오는 중...")
    
    backup_data = {
        'backup_date': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'database_type': 'SQLite',
        'posts': [],
        'comments': []
    }
    
    try:
        # 자유게시판 가져오기
        print("📝 자유게시판 게시글 가져오는 중...")
        response = requests.get(f"{base_url}/board/free", timeout=10)
        if response.status_code == 200:
            # HTML 파싱 필요... 복잡함
            print("⚠️  HTML 파싱이 필요합니다.")
            print("   대신 수동으로 게시글을 복사하는 것을 권장합니다.")
        
        # 프로젝트게시판 가져오기
        print("📝 프로젝트게시판 게시글 가져오는 중...")
        response = requests.get(f"{base_url}/board/project", timeout=10)
        if response.status_code == 200:
            print("⚠️  HTML 파싱이 필요합니다.")
        
        print("\n" + "="*60)
        print("💡 추천 방법:")
        print("="*60)
        print("1. 게시글이 많지 않다면: 수동 복사")
        print("2. 게시글이 많다면: Render Shell 사용")
        print("3. 또는 임시 API 엔드포인트 추가")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("사용법: python fetch_render_data.py https://your-app.onrender.com")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    fetch_render_data(base_url)
