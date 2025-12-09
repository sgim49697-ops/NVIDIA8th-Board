# 프로젝트 게시판 (Quill 에디터 + PostgreSQL 지원)

Flask로 만든 풀 기능 게시판입니다. 이미지 복사-붙여넣기, 리치 텍스트 에디터, PostgreSQL 지원을 제공합니다.

## ✨ 주요 기능

### 게시판
- ✅ 자유게시판 & 프로젝트게시판 분리
- ✅ 프로젝트 게시판 최신글 메인 페이지 미리보기
- ✅ 파일 업로드/다운로드 (최대 100MB)
- ✅ 작성자 본인 게시글 수정/삭제
- ✅ 관리자 모든 게시글 수정/삭제

### 에디터 (Quill.js)
- ✅ **이미지 복사-붙여넣기** (Ctrl+V)
- ✅ 리치 텍스트 편집 (볼드, 이탤릭, 색상 등)
- ✅ 코드 블록, 인용문, 리스트
- ✅ 링크 삽입
- ✅ 이미지 업로드 (URL 또는 복사-붙여넣기)

### 댓글
- ✅ 댓글 작성/삭제
- ✅ 작성자 본인 댓글 삭제
- ✅ 관리자 모든 댓글 삭제

### 데이터베이스
- ✅ 자동 감지: 로컬은 SQLite, Render는 PostgreSQL
- ✅ 데이터 영구 보존 (PostgreSQL 사용 시)
- ✅ 백업/복원 스크립트 포함

## 🚀 로컬에서 실행

```bash
pip install -r requirements.txt
python app.py
```

브라우저에서 `http://localhost:5000` 접속

## 🎨 이미지 사용 방법

### 방법 1: 복사-붙여넣기 (추천)
1. 이미지 복사 (Ctrl+C)
2. 에디터에서 Ctrl+V
3. 자동으로 삽입됨!

### 방법 2: 툴바 버튼
1. 에디터 툴바의 🖼️ 이미지 버튼 클릭
2. 이미지 URL 입력
3. 삽입

### 방법 3: 파일 첨부
- 별도 파일 첨부 필드 사용

## 🌐 Render 배포 (PostgreSQL)

### 1. PostgreSQL 생성
1. https://render.com → "New +" → "PostgreSQL"
2. Region: Singapore, Plan: Free
3. **Internal Database URL** 복사

### 2. Web Service 생성
1. "New +" → "Web Service"
2. GitHub 저장소 연결
3. 환경변수 설정:
   - `DATABASE_URL`: (PostgreSQL URL)
   - `ADMIN_PASSWORD`: 관리자 비밀번호
   - `SECRET_KEY`: Flask 시크릿 키

**자세한 내용**: `RENDER_POSTGRESQL.md` 참조

## 💾 백업

### Python 스크립트 (추천)

```bash
# 백업
python backup_db.py backup

# 백업 목록
python backup_db.py list

# 복원
python backup_db.py restore backup_20251209_120000.json
```

## 🔐 관리자 설정

**기본 관리자 비밀번호**: `admin1234`

환경변수로 변경:
```bash
export ADMIN_PASSWORD="your-secure-password"
```

## 📊 데이터베이스 선택

코드가 **자동으로 감지**합니다:

```
DATABASE_URL 환경변수 있음? → PostgreSQL
DATABASE_URL 환경변수 없음? → SQLite
```

## 🔧 문제 해결

### SQLite: "no such column: board_type"
```bash
# 기존 DB 삭제
del board.db  # Windows
rm board.db   # Mac/Linux

# 또는 마이그레이션
python migrate_db.py
```

### 이미지가 DB에 저장됨
- 이미지는 base64로 인코딩되어 DB에 저장됩니다
- 큰 이미지를 많이 올리면 DB 용량 증가
- 프로덕션: Cloudinary 같은 이미지 호스팅 권장

## ⚠️ 주의사항

### 이미지 저장 방식
- 현재: base64로 DB에 저장
- 장점: 간편함, 추가 설정 불필요
- 단점: DB 용량 증가
- 권장: 큰 이미지는 파일 첨부 사용

### 파일 업로드 (Render)
- 업로드 파일은 재배포 시 삭제됨
- 해결: Cloudinary (무료) 사용 권장

## 📁 파일 구조

```
project_board/
├── app.py              # 메인 앱 (SQLite/PostgreSQL 자동 감지)
├── backup_db.py        # 백업/복원 스크립트
├── migrate_db.py       # SQLite 마이그레이션
├── requirements.txt    # 패키지 (psycopg2-binary 포함)
└── templates/          # HTML 템플릿 (Quill 에디터 포함)
    ├── index.html      # 메인 (카드 요소 제거됨)
    ├── write.html      # 글쓰기 (Quill)
    ├── edit.html       # 수정 (Quill)
    ├── view.html       # 상세보기 (이미지 스타일 적용)
    └── board.html      # 목록
```

## 🎯 새로운 기능

### v2.0 업데이트
- ✅ Quill.js 에디터 통합
- ✅ 이미지 복사-붙여넣기
- ✅ 리치 텍스트 포맷팅
- ✅ 메인 페이지 카드 요소 제거 (깔끔한 디자인)
- ✅ 이미지 자동 반응형 처리

## 💡 추천 설정

**로컬 개발**: SQLite (간편)
**프로덕션**: PostgreSQL (데이터 보존)

## 📖 추가 문서

- `RENDER_POSTGRESQL.md`: Render + PostgreSQL 완벽 가이드
- `RENDER_DEPLOY.md`: 일반 Render 배포 가이드

---

궁금한 점이 있으면 Issues에 남겨주세요!
