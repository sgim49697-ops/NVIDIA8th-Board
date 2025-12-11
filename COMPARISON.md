# 📊 수정 전후 비교

## 1️⃣ 익명 글쓰기 제한

### 수정 전 (write 함수)
```python
@app.route('/write/<board_type>', methods=['GET', 'POST'])
def write(board_type):
    if board_type not in ['free', 'project']:
        return "잘못된 게시판입니다.", 404
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        # 로그인 여부에 따라 처리
        if 'user_id' in session:
            user_id = session['user_id']
            author = session['username']
            password_hash = None
        else:
            # ❌ 익명 사용자도 글 작성 가능
            user_id = None
            author = request.form['author']
            password = request.form['password']
            password_hash = generate_password_hash(password)
        
        # ... 파일 업로드 및 저장 로직 ...
```

### 수정 후 (write 함수)
```python
@app.route('/write/<board_type>', methods=['GET', 'POST'])
def write(board_type):
    if board_type not in ['free', 'project']:
        return "잘못된 게시판입니다.", 404
    
    if request.method == 'POST':
        # ⭐ 익명 사용자 즉시 차단
        if 'user_id' not in session:
            flash('로그인 후 글을 작성할 수 있습니다.', 'error')
            return redirect(url_for('login'))
        
        title = request.form['title']
        content = request.form['content']
        
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        # ✅ 로그인 사용자만 여기까지 도달
        user_id = session['user_id']
        author = session['username']
        password_hash = None
        
        # ... 파일 업로드 및 저장 로직 ...
    
    # ⭐ GET 요청 시에도 로그인 확인
    is_logged_in = 'user_id' in session
    
    if not is_logged_in:
        flash('글을 작성하려면 로그인이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    return render_template('write.html', ...)
```

---

## 2️⃣ 썸네일 우선순위 변경

### 수정 전 (board 함수)
```python
@app.route('/board/<board_type>')
def board(board_type):
    if board_type not in ['free', 'project']:
        return "잘못된 게시판입니다.", 404
    
    board_name = '자유게시판' if board_type == 'free' else '프로젝트게시판'
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        'SELECT * FROM posts WHERE board_type = %s ORDER BY created_at DESC',
        (board_type,)
    )
    posts = [dict(row) for row in cursor.fetchall()]
    
    # ❌ 썸네일 처리 없음 - 템플릿에서 cloudinary_url만 사용
    
    cursor.close()
    conn.close()
    
    return render_template('board.html', posts=posts, board_type=board_type, board_name=board_name)
```

### 수정 후 (board 함수)
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

@app.route('/board/<board_type>')
def board(board_type):
    if board_type not in ['free', 'project']:
        return "잘못된 게시판입니다.", 404
    
    board_name = '자유게시판' if board_type == 'free' else '프로젝트게시판'
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        'SELECT * FROM posts WHERE board_type = %s ORDER BY created_at DESC',
        (board_type,)
    )
    posts = [dict(row) for row in cursor.fetchall()]
    
    # ⭐ 각 게시글에 썸네일 추가 (본문 이미지 우선, 없으면 첨부 파일)
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
    
    cursor.close()
    conn.close()
    
    return render_template('board.html', posts=posts, board_type=board_type, board_name=board_name)
```

---

## 3️⃣ 템플릿 변경 (board.html)

### 수정 전
```html
<div class="post-thumbnail {% if not post['cloudinary_url'] %}placeholder{% endif %}">
    {% if post['cloudinary_url'] %}
        <!-- ❌ 첨부 파일만 확인 -->
        <img src="{{ post['cloudinary_url'] }}" alt="썸네일">
    {% else %}
        📄
    {% endif %}
</div>
```

### 수정 후
```html
<div class="post-thumbnail {% if not post['thumbnail'] %}placeholder{% endif %}">
    {% if post['thumbnail'] %}
        <!-- ✅ 본문 이미지 또는 첨부 파일 (우선순위 적용) -->
        <img src="{{ post['thumbnail'] }}" alt="썸네일">
    {% else %}
        📄
    {% endif %}
</div>
```

---

## 📈 시나리오별 동작 비교

### 시나리오 1: 비로그인 사용자가 글쓰기 시도

**수정 전:**
```
1. /write/free 접속 → ✅ 접근 가능
2. 작성자명, 비밀번호 입력란 표시
3. 글 작성 가능
```

**수정 후:**
```
1. /write/free 접속 → 🚫 즉시 리다이렉트
2. 로그인 페이지로 이동
3. "글을 작성하려면 로그인이 필요합니다" 메시지
4. 로그인 후에만 글쓰기 가능
```

---

### 시나리오 2: 본문에 이미지가 있는 게시글

**수정 전:**
```
본문: <img src="image1.jpg"> <img src="image2.jpg">
첨부: photo.png

게시판 썸네일: photo.png (첨부 파일만 확인)
```

**수정 후:**
```
본문: <img src="image1.jpg"> <img src="image2.jpg">
첨부: photo.png

게시판 썸네일: image1.jpg ✅ (본문의 첫 번째 이미지 우선)
```

---

### 시나리오 3: 첨부 파일만 있는 게시글

**수정 전:**
```
본문: 텍스트만
첨부: photo.png

게시판 썸네일: photo.png ✅
```

**수정 후:**
```
본문: 텍스트만
첨부: photo.png

게시판 썸네일: photo.png ✅ (동일하게 작동)
```

---

### 시나리오 4: 이미지가 전혀 없는 게시글

**수정 전:**
```
본문: 텍스트만
첨부: 없음

게시판 썸네일: 📄 플레이스홀더 ✅
```

**수정 후:**
```
본문: 텍스트만
첨부: 없음

게시판 썸네일: 📄 플레이스홀더 ✅ (동일하게 작동)
```

---

## 🎯 핵심 차이점

| 구분 | 수정 전 | 수정 후 |
|------|---------|---------|
| **익명 글쓰기** | ✅ 가능 | 🚫 불가능 (로그인 필수) |
| **썸네일 우선순위** | 첨부 파일만 | 본문 이미지 → 첨부 파일 |
| **사용자 경험** | 익명 게시글 많음 | 로그인 유도, 품질 향상 |
| **시각적 품질** | 첨부된 이미지만 | 본문의 대표 이미지 우선 |

---

## 💡 추가 개선 제안

현재 변경사항만으로도 충분하지만, 추가로 고려할 수 있는 개선사항:

1. **다중 이미지 썸네일** (선택사항)
   - 게시글에 이미지가 여러 개일 때 여러 개 표시

2. **썸네일 캐싱** (성능 개선)
   - 자주 조회되는 썸네일을 캐시에 저장

3. **이미지 크기 최적화** (성능 개선)
   - Cloudinary를 통해 썸네일용 작은 이미지 생성

필요하시면 말씀해주세요!
