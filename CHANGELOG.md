# 📝 게시판 업데이트 - 변경사항 요약

## 🔒 보안 확인 결과
✅ **안전합니다!** 업로드된 파일에는 중요한 환경변수가 노출되어 있지 않습니다.
- `DATABASE_URL`, `ADMIN_PASSWORD`, `SECRET_KEY` 등 모두 환경변수로 관리됨
- `.env` 파일 없음

---

## ✨ 주요 변경사항

### 1️⃣ 익명 사용자 글 작성 제한

**변경 전:**
- 로그인/비로그인 모두 글 작성 가능
- 비로그인 시 작성자명과 비밀번호 입력

**변경 후:**
- ✅ 로그인한 사용자만 글 작성 가능
- 비로그인 시 자동으로 로그인 페이지로 리다이렉트
- 친절한 안내 메시지 표시

**적용 코드 (app.py):**
```python
@app.route('/write/<board_type>', methods=['GET', 'POST'])
def write(board_type):
    if board_type not in ['free', 'project']:
        return "잘못된 게시판입니다.", 404
    
    if request.method == 'POST':
        # ⭐ 익명 사용자 글 작성 제한 추가
        if 'user_id' not in session:
            flash('로그인 후 글을 작성할 수 있습니다.', 'error')
            return redirect(url_for('login'))
        
        # ... 나머지 로직 (로그인 사용자만 실행됨)
    
    # GET 요청 시에도 로그인 확인
    is_logged_in = 'user_id' in session
    
    if not is_logged_in:
        flash('글을 작성하려면 로그인이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    return render_template('write.html', ...)
```

---

### 2️⃣ 썸네일 우선순위 변경

**변경 전:**
```
📷 썸네일 = 첨부 파일(cloudinary_url)만 표시
```

**변경 후:**
```
📷 썸네일 우선순위:
  1순위: 본문 내 첫 번째 이미지 (Quill.js 에디터에서 직접 삽입한 이미지)
  2순위: 첨부 파일 (file upload로 첨부한 이미지)
  없음: 📄 플레이스홀더
```

**적용 코드:**

**app.py에 이미지 추출 함수 추가:**
```python
def extract_first_image(html_content):
    """HTML 콘텐츠에서 첫 번째 이미지 URL 추출"""
    if not html_content:
        return None
    
    # <img> 태그에서 src 추출
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    match = re.search(img_pattern, html_content, re.IGNORECASE)
    
    if match:
        return match.group(1)
    return None
```

**board 함수에서 썸네일 처리:**
```python
@app.route('/board/<board_type>')
def board(board_type):
    # ... 게시글 조회 ...
    
    # 각 게시글에 썸네일 추가 (본문 이미지 우선, 없으면 첨부 파일)
    for post in posts:
        # 1순위: 본문에서 첫 번째 이미지 추출
        content_image = extract_first_image(post.get('content', ''))
        
        if content_image:
            post['thumbnail'] = content_image
        elif post.get('cloudinary_url'):
            # 2순위: 첨부 파일
            post['thumbnail'] = post['cloudinary_url']
        else:
            post['thumbnail'] = None
    
    return render_template('board.html', posts=posts, ...)
```

**board.html에서 thumbnail 사용:**
```html
<div class="post-thumbnail {% if not post['thumbnail'] %}placeholder{% endif %}">
    {% if post['thumbnail'] %}
        <img src="{{ post['thumbnail'] }}" alt="썸네일">
    {% else %}
        📄
    {% endif %}
</div>
```

---

## 📦 수정된 파일 목록

1. **app.py** (주요 변경)
   - `extract_first_image()` 함수 추가
   - `write()` 함수: 익명 사용자 제한 로직 추가
   - `board()` 함수: 썸네일 추출 로직 추가

2. **templates/board.html**
   - 썸네일 표시 로직 변경 (`post['thumbnail']` 사용)

---

## 🚀 적용 방법

### 방법 1: 전체 파일 교체 (권장)

```powershell
# 1. 백업
cd C:\Project_bulletin\Nvidia8Board
copy app.py app.py.backup
copy templates\board.html templates\board.html.backup

# 2. 새 파일로 교체
copy app.py app.py
copy templates\board.html templates\board.html

# 3. 서버 재시작
python app.py
```

### 방법 2: 수동 수정

#### app.py 수정:

**1단계: extract_first_image 함수 추가 (70번 라인 부근)**
```python
def extract_first_image(html_content):
    """HTML 콘텐츠에서 첫 번째 이미지 URL 추출"""
    if not html_content:
        return None
    
    # <img> 태그에서 src 추출
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    match = re.search(img_pattern, html_content, re.IGNORECASE)
    
    if match:
        return match.group(1)
    return None
```

**2단계: board 함수 수정 (323번 라인)**
```python
@app.route('/board/<board_type>')
def board(board_type):
    # ... 기존 코드 ...
    
    posts = [dict(row) for row in cursor.fetchall()]
    
    # ⭐ 이 부분 추가
    for post in posts:
        content_image = extract_first_image(post.get('content', ''))
        
        if content_image:
            post['thumbnail'] = content_image
        elif post.get('cloudinary_url'):
            post['thumbnail'] = post['cloudinary_url']
        else:
            post['thumbnail'] = None
    # ⭐ 추가 끝
    
    cursor.close()
    conn.close()
    
    return render_template('board.html', posts=posts, board_type=board_type, board_name=board_name)
```

**3단계: write 함수 수정 (344번 라인)**
```python
@app.route('/write/<board_type>', methods=['GET', 'POST'])
def write(board_type):
    if board_type not in ['free', 'project']:
        return "잘못된 게시판입니다.", 404
    
    if request.method == 'POST':
        # ⭐ 이 부분 추가
        if 'user_id' not in session:
            flash('로그인 후 글을 작성할 수 있습니다.', 'error')
            return redirect(url_for('login'))
        # ⭐ 추가 끝
        
        # ... 기존 코드 (로그인 사용자만 실행됨) ...
        user_id = session['user_id']
        author = session['username']
        password_hash = None
        
        # ... 나머지 코드 ...
    
    board_name = '자유게시판' if board_type == 'free' else '프로젝트게시판'
    is_logged_in = 'user_id' in session
    
    # ⭐ 이 부분 추가
    if not is_logged_in:
        flash('글을 작성하려면 로그인이 필요합니다.', 'error')
        return redirect(url_for('login'))
    # ⭐ 추가 끝
    
    return render_template('write.html', board_type=board_type, board_name=board_name, is_logged_in=is_logged_in)
```

#### board.html 수정:

**104-110번 라인 수정:**
```html
<!-- 변경 전 -->
<div class="post-thumbnail {% if not post['cloudinary_url'] %}placeholder{% endif %}">
    {% if post['cloudinary_url'] %}
        <img src="{{ post['cloudinary_url'] }}" alt="썸네일">
    {% else %}
        📄
    {% endif %}
</div>

<!-- 변경 후 -->
<div class="post-thumbnail {% if not post['thumbnail'] %}placeholder{% endif %}">
    {% if post['thumbnail'] %}
        <img src="{{ post['thumbnail'] }}" alt="썸네일">
    {% else %}
        📄
    {% endif %}
</div>
```

---

## 🧪 테스트 방법

### 1. 익명 글쓰기 제한 테스트

1. **로그아웃 상태에서 테스트:**
   ```
   http://localhost:5000/write/free
   ```
   - ✅ 로그인 페이지로 자동 리다이렉트
   - ✅ "글을 작성하려면 로그인이 필요합니다" 메시지 표시

2. **로그인 후 테스트:**
   - ✅ 글쓰기 페이지 정상 접근
   - ✅ 작성자명/비밀번호 입력란 없음
   - ✅ 게시글 작성 완료

### 2. 썸네일 우선순위 테스트

**테스트 케이스 1: 본문에 이미지만 있는 경우**
1. 글쓰기에서 Quill 에디터의 이미지 버튼(🖼️)으로 이미지 삽입
2. 첨부 파일 없이 작성
3. 게시판에서 확인 → ✅ 본문 이미지가 썸네일로 표시

**테스트 케이스 2: 첨부 파일만 있는 경우**
1. 글쓰기에서 본문에 이미지 없음
2. 첨부 파일로 이미지 업로드
3. 게시판에서 확인 → ✅ 첨부 파일이 썸네일로 표시

**테스트 케이스 3: 둘 다 있는 경우**
1. 본문에 이미지 여러 개 삽입
2. 첨부 파일도 업로드
3. 게시판에서 확인 → ✅ 본문의 **첫 번째** 이미지가 썸네일로 표시

**테스트 케이스 4: 이미지 없음**
1. 텍스트만 작성
2. 게시판에서 확인 → ✅ 📄 플레이스홀더 표시

---

## 🎯 기대 효과

### 익명 글쓰기 제한
- ✅ 스팸 게시글 방지
- ✅ 사용자 책임감 향상
- ✅ 커뮤니티 품질 개선
- ✅ 로그인 유도 효과

### 썸네일 우선순위 개선
- ✅ 사용자가 본문에서 신중하게 선택한 이미지 우선 표시
- ✅ 게시판 목록의 시각적 품질 향상
- ✅ 더 직관적인 게시글 미리보기
- ✅ 첨부 파일 기반 썸네일도 여전히 지원

---

## 📌 참고사항

### Quill.js 이미지 처리
- Quill.js는 이미지를 Base64 또는 URL로 삽입
- `extract_first_image()` 함수는 두 형식 모두 지원
- Base64 이미지도 썸네일로 정상 표시됨

### 성능 고려사항
- 이미지 추출은 정규식으로 빠르게 처리
- 데이터베이스 쿼리는 기존과 동일
- 썸네일 생성은 게시판 로드 시 한 번만 실행

### 하위 호환성
- 기존 게시글도 정상 작동
- 첨부 파일만 있는 기존 글은 여전히 썸네일 표시
- 데이터베이스 스키마 변경 없음

---

## ❓ 문제 해결

### 썸네일이 표시되지 않을 때
1. 브라우저 캐시 삭제 (Ctrl + Shift + Delete)
2. 서버 재시작
3. 콘솔에서 에러 확인

### 로그인 리다이렉트가 작동하지 않을 때
1. 세션 확인: `session.get('user_id')` 값 확인
2. Flash 메시지 표시 여부 확인
3. 로그 확인

---

## 📞 추가 지원

추가 수정이 필요하거나 문제가 발생하면 말씀해주세요!
