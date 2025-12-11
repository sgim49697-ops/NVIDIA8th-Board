# 🔐 Flask 게시판 - 하이브리드 인증 시스템 (PostgreSQL 전용)

## 📦 제공 파일 목록

### Python 파일
- `app_postgresql.py` - PostgreSQL 전용 메인 앱
- `migrate_postgresql.py` - PostgreSQL 전용 마이그레이션 스크립트
- `requirements_postgresql.txt` - 필요한 Python 패키지 목록

### HTML 템플릿 (templates/ 폴더에 넣기)
- `register.html` - 회원가입 페이지
- `login.html` - 로그인 페이지
- `user_profile.html` - 사용자 프로필 페이지
- `index_hybrid.html` → `index.html` (교체)
- `board_hybrid.html` → `board.html` (교체)
- `write_hybrid.html` → `write.html` (교체)
- `view_hybrid.html` → `view.html` (교체)
- `edit_hybrid.html` → `edit.html` (교체)

### 문서
- `DEPLOYMENT_GUIDE_POSTGRESQL.md` - 상세 배포 가이드
- `README_POSTGRESQL.md` - 이 파일

---

## 🎯 PostgreSQL 전용 버전

### 특징
✅ PostgreSQL만 사용 (SQLite 제거)
✅ 코드가 더 단순하고 명확
✅ 로컬과 프로덕션 환경 일관성
✅ PostgreSQL 전용 기능 활용 가능

### 필수 조건
⚠️ **PostgreSQL이 반드시 필요합니다!**

**로컬 개발:**
- PostgreSQL 설치 필수
- DATABASE_URL 환경변수 설정 필수

**Render 배포:**
- PostgreSQL 서비스 연결 (Render가 DATABASE_URL 자동 제공)

---

## 🚀 빠른 시작 가이드

### 1️⃣ PostgreSQL 준비

#### 로컬 개발용
```bash
# Windows
https://www.postgresql.org/download/windows/

# Mac
brew install postgresql@16
brew services start postgresql@16

# Linux
sudo apt install postgresql postgresql-contrib
```

#### 데이터베이스 생성
```bash
psql -U postgres
CREATE DATABASE flask_board;
\q
```

### 2️⃣ Gmail 앱 비밀번호 생성

1. https://myaccount.google.com/security 접속
2. **2단계 인증** 활성화
3. **앱 비밀번호** 생성 (메일 앱)
4. 16자리 비밀번호 복사 (공백 제거)

### 3️⃣ 환경변수 설정

#### Windows CMD
```cmd
set DATABASE_URL=postgresql://postgres:password@localhost:5432/flask_board
set MAIL_USERNAME=your-email@gmail.com
set MAIL_PASSWORD=abcdefghijklmnop
set SECRET_KEY=your-secret-key
set ADMIN_PASSWORD=your-admin-password
set CLOUDINARY_CLOUD_NAME=your-cloud-name
set CLOUDINARY_API_KEY=your-api-key
set CLOUDINARY_API_SECRET=your-api-secret
```

#### Windows PowerShell
```powershell
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/flask_board"
$env:MAIL_USERNAME="your-email@gmail.com"
$env:MAIL_PASSWORD="abcdefghijklmnop"
$env:SECRET_KEY="your-secret-key"
$env:ADMIN_PASSWORD="your-admin-password"
```

### 4️⃣ 파일 교체

```bash
# 백업
mkdir backup
copy app.py backup\
copy templates\*.html backup\

# Python 파일 교체
copy app_postgresql.py app.py
copy requirements_postgresql.txt requirements.txt

# 템플릿 파일 교체
copy register.html templates\
copy login.html templates\
copy user_profile.html templates\
copy index_hybrid.html templates\index.html
copy board_hybrid.html templates\board.html
copy write_hybrid.html templates\write.html
copy view_hybrid.html templates\view.html
copy edit_hybrid.html templates\edit.html
```

### 5️⃣ 데이터베이스 마이그레이션

```bash
python migrate_postgresql.py
```

### 6️⃣ 패키지 설치 및 실행

```bash
pip install -r requirements.txt
python app.py
```

### 7️⃣ 테스트

1. http://localhost:5000 접속
2. **회원가입** 클릭
3. 이메일 인증 확인
4. 로그인 후 글 작성
5. "✓ 인증됨" 배지 확인

---

## 🌐 Render 배포

### 1. GitHub 푸시
```bash
git add .
git commit -m "PostgreSQL only hybrid authentication"
git push origin main
```

### 2. Render 환경변수 추가

Dashboard → Environment → Add Environment Variable:

```
DATABASE_URL = (Render가 자동 제공)
MAIL_USERNAME = your-email@gmail.com
MAIL_PASSWORD = abcdefghijklmnop
SECRET_KEY = (새로 생성)
ADMIN_PASSWORD = (새로 생성)
CLOUDINARY_CLOUD_NAME = your-cloud-name
CLOUDINARY_API_KEY = your-api-key
CLOUDINARY_API_SECRET = your-api-secret
```

### 3. 재배포
- Manual Deploy 클릭
- 또는 자동 배포 대기

### 4. 확인
```
Dashboard → Logs
✅ PostgreSQL 데이터베이스 초기화 완료
```

---

## ✨ 주요 기능

### 익명 사용자 (기존 방식)
- 아이디/비밀번호만으로 게시 가능
- 수정/삭제 시 비밀번호 필요
- 프로필 링크 없음

### 회원 사용자 (신규)
- ✅ 이메일 인증 회원가입
- ✅ 로그인/로그아웃
- ✅ "✓ 인증됨" 배지 표시
- ✅ 비밀번호 입력 불필요 (자동 인증)
- ✅ 프로필 페이지 (내가 쓴 글/댓글)
- ✅ 활동 추적

### 관리자 기능
```
# 사용자 활동 통계
https://your-app.onrender.com/admin/user-activity?password=ADMIN_PASSWORD

# IP 주소 추적 (보안)
- 모든 게시글/댓글에 IP 저장
- 도배 감지 가능
- 동일인 확인 가능
```

---

## 📊 데이터베이스 스키마

### users 테이블 (신규)
```sql
id                  SERIAL PRIMARY KEY
username            VARCHAR(50) UNIQUE NOT NULL
email               VARCHAR(100) UNIQUE NOT NULL
password            VARCHAR(200) NOT NULL
email_verified      BOOLEAN DEFAULT FALSE
verification_token  VARCHAR(100)
created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### posts 테이블 (컬럼 추가)
```sql
user_id             INTEGER REFERENCES users(id)  -- 신규
ip_address          VARCHAR(45)                   -- 신규
user_agent          TEXT                          -- 신규
```

### comments 테이블 (컬럼 추가)
```sql
user_id             INTEGER REFERENCES users(id)  -- 신규
ip_address          VARCHAR(45)                   -- 신규
user_agent          TEXT                          -- 신규
```

---

## 🔧 트러블슈팅

### DATABASE_URL 오류
```bash
❌ DATABASE_URL 환경변수가 설정되지 않았습니다!

# 해결방법:
set DATABASE_URL=postgresql://user:pass@host:port/database
```

### PostgreSQL 연결 실패
```bash
❌ psycopg2.OperationalError: connection failed

# 해결방법:
# 1. PostgreSQL 서비스 실행 확인
# 2. DATABASE_URL 형식 확인
# 3. 비밀번호 확인
```

### 이메일 발송 실패
```bash
❌ SMTPAuthenticationError

# 해결방법:
# 1. 2단계 인증 활성화 확인
# 2. 앱 비밀번호 (16자리) 사용 확인
# 3. 일반 비밀번호 사용 안됨!
```

### users 테이블 없음
```bash
❌ relation "users" does not exist

# 해결방법:
python migrate_postgresql.py
# 또는
python
>>> from app import init_db
>>> init_db()
```

---

## 📈 하이브리드 vs SQLite 버전 비교

| 기능 | SQLite 버전 | PostgreSQL 전용 |
|------|------------|----------------|
| 로컬 개발 | ✅ 간단 (DB 설치 불필요) | ⚠️ PostgreSQL 설치 필요 |
| 프로덕션 | ✅ PostgreSQL | ✅ PostgreSQL |
| 코드 복잡도 | 높음 (조건문 많음) | 낮음 (단순) |
| 환경 일관성 | 낮음 (로컬≠프로덕션) | 높음 (로컬=프로덕션) |
| 유지보수 | 어려움 | 쉬움 |
| 디버깅 | 어려움 | 쉬움 |

**추천**: 진지한 프로젝트라면 PostgreSQL 전용 사용!

---

## 💡 사용 팁

### 로컬 개발 환경
- Docker 사용 추천:
  ```bash
  docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:16
  ```

### 환경변수 관리
- `.env` 파일 사용 (python-dotenv)
- `.gitignore`에 `.env` 추가

### SECRET_KEY 생성
```python
import secrets
secrets.token_hex(32)
```

### 데이터베이스 백업
```bash
# 로컬
pg_dump flask_board > backup.sql

# Render
Dashboard → PostgreSQL → Backup
```

---

## 🔒 보안 권장사항

1. **환경변수 절대 GitHub에 푸시 금지**
   - `.gitignore`에 `.env` 추가
   - 기존 환경변수 노출 시 즉시 변경

2. **강력한 비밀번호 사용**
   - SECRET_KEY: 64자 이상
   - ADMIN_PASSWORD: 12자 이상, 특수문자 포함

3. **정기적인 업데이트**
   - Flask, psycopg2 등 패키지 업데이트
   - PostgreSQL 버전 업데이트

4. **HTTPS 사용**
   - Render는 자동 제공
   - 로컬 개발 시 ngrok 활용

---

## 📞 추가 도움

자세한 내용은 `DEPLOYMENT_GUIDE_POSTGRESQL.md`를 참고하세요!

- PostgreSQL 설치 가이드
- Gmail 설정 상세 가이드
- Render 배포 단계별 설명
- 트러블슈팅 상세 해결 방법

---

## 🎉 완료!

PostgreSQL 전용 하이브리드 인증 시스템으로 업그레이드 완료! 🚀

**장점:**
- ✅ 코드가 단순하고 명확
- ✅ 로컬과 프로덕션 환경 일관성
- ✅ 유지보수가 쉬움
- ✅ 디버깅이 쉬움

질문이 있으면 언제든지 문의하세요! 😊
