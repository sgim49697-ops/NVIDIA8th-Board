# 🎯 NVIDIA 8th 게시판 - 기능 업그레이드 가이드

## ✨ 추가된 기능

### 1. Cloudinary 파일 백업 (무료 25GB)
- 모든 첨부파일이 Cloudinary에 업로드됨
- 재배포해도 파일 유지
- 이미지 자동 최적화
- 백업 API에 Cloudinary URL 포함

### 2. 대댓글 기능
- 댓글에 답글 작성 가능
- 계층 구조로 표시
- 대댓글도 삭제 가능

### 3. 썸네일 미리보기
- 게시판 목록에서 이미지 미리보기
- 80x80px 정사각형 썸네일
- 이미지가 없으면 📄 아이콘 표시

### 4. 첨부파일 수정
- 글 수정 시 파일 변경 가능
- 기존 파일 삭제 가능
- 새 파일 업로드로 교체 가능

---

## 📋 수정된 파일 목록

### 1. requirements.txt
- cloudinary==1.41.0 추가

### 2. app.py (전체 수정)
- Cloudinary 연동
- 대댓글 (parent_id) 추가
- 파일 업로드/수정/삭제 Cloudinary 처리
- 백업 API에 Cloudinary 정보 포함

### 3. templates/board.html (썸네일)
- 게시글 목록에 썸네일 표시
- Cloudinary 이미지 사용
- 반응형 디자인

### 4. templates/view.html (대댓글)
- 대댓글 작성 폼
- 대댓글 목록 표시
- 계층 구조 UI

### 5. templates/edit.html (파일 수정)
- 현재 파일 표시
- 파일 삭제 체크박스
- 새 파일 업로드 폼

---

## 🚀 배포 방법

### 1단계: Cloudinary 가입
```
1. https://cloudinary.com 접속
2. Sign Up (무료)
3. Dashboard에서 정보 확인:
   - Cloud name
   - API Key
   - API Secret
```

### 2단계: Render 환경변수 추가
```
Render Dashboard → nvidia8th-board → Environment

추가할 환경변수:
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 3단계: 파일 업로드
```bash
# 로컬에서
cd C:\Project_bulletin\Nvidia8Board

# 수정된 파일 복사
copy app.py templates\board.html templates\view.html templates\edit.html requirements.txt

# Git 커밋
git add .
git commit -m "Add Cloudinary, 대댓글, 썸네일, 파일수정 기능"
git push origin main
```

### 4단계: 데이터베이스 마이그레이션
기존 posts, comments 테이블에 새 컬럼 추가 필요:

```sql
-- PostgreSQL (Render Console)
ALTER TABLE posts ADD COLUMN IF NOT EXISTS cloudinary_url TEXT;
ALTER TABLE posts ADD COLUMN IF NOT EXISTS cloudinary_public_id TEXT;
ALTER TABLE comments ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE;
```

**Render에서 실행:**
```
1. Dashboard → PostgreSQL 서비스 클릭
2. Connect → External 탭
3. psql 명령어 복사해서 로컬 터미널에서 실행
4. 위 SQL 실행
```

---

## ✅ 테스트 체크리스트

배포 후 확인:

- [ ] 게시글 작성 시 파일 업로드 → Cloudinary URL 확인
- [ ] 게시판 목록에서 썸네일 표시 확인
- [ ] 댓글에 답글 버튼 → 대댓글 작성 확인
- [ ] 글 수정 → 파일 수정/삭제 확인
- [ ] 백업 API 호출 → cloudinary_url 포함 확인

```bash
# 백업 API 테스트
curl "https://nvidia8th-board.onrender.com/admin/backup?password=apxkahd12"
```

---

## 📊 데이터베이스 스키마 변경

### posts 테이블
```sql
기존:
- id
- board_type
- title
- author
- password
- content
- filename
- created_at

추가:
- cloudinary_url (TEXT)       -- Cloudinary 파일 URL
- cloudinary_public_id (TEXT)  -- Cloudinary 삭제용 ID
```

### comments 테이블
```sql
기존:
- id
- post_id
- author
- password
- content
- created_at

추가:
- parent_id (INTEGER)  -- 대댓글용 (NULL이면 원댓글)
```

---

## 🔧 Cloudinary 설정 확인

### Dashboard 확인
```
Cloudinary Dashboard → Media Library

업로드된 파일 확인:
nvidia8th_board/
  ├── free/
  │   └── 파일들...
  └── project/
      └── 파일들...
```

### 무료 플랜 제한
- 저장 공간: 25GB
- 대역폭: 25GB/월
- 변환: 25 크레딧/월

충분히 사용 가능! ✅

---

## 🆘 문제 해결

### Cloudinary 업로드 실패
```python
# 에러: "Could not authenticate"
→ 환경변수 확인 (CLOUDINARY_CLOUD_NAME, API_KEY, API_SECRET)

# 에러: "Invalid image file"
→ 파일 형식 확인
```

### 썸네일 안 보임
```
→ cloudinary_url이 NULL인지 확인
→ 이미지 파일만 썸네일 표시됨
```

### 대댓글 안 보임
```sql
-- parent_id 컬럼 확인
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'comments';
```

---

## 💡 추가 개선 아이디어

1. **이미지 리사이징**
   - 썸네일 자동 생성 (Cloudinary transformation)
   - 큰 이미지 자동 압축

2. **파일 타입 아이콘**
   - PDF: 📄
   - ZIP: 📦
   - 이미지: 🖼️

3. **대댓글 알림**
   - 이메일 알림
   - 실시간 알림

---

## 📞 요약

**변경 사항:**
- requirements.txt (cloudinary 추가)
- app.py (전체 로직 수정)
- board.html (썸네일 UI)
- view.html (대댓글 UI)
- edit.html (파일 수정 UI)

**배포 순서:**
1. Cloudinary 가입
2. 환경변수 설정
3. 코드 배포
4. DB 마이그레이션
5. 테스트

**소요 시간:** 약 30분

성공적인 업그레이드를 기원합니다! 🚀
