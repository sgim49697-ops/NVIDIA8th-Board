# 🔐 하이브리드 인증 시스템 배포 가이드 (PostgreSQL 전용)

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [필요한 환경변수](#필요한-환경변수)
3. [Gmail 앱 비밀번호 설정](#gmail-앱-비밀번호-설정)
4. [로컬 개발 환경 설정](#로컬-개발-환경-설정)
5. [Render 배포](#render-배포)
6. [데이터베이스 마이그레이션](#데이터베이스-마이그레이션)
7. [트러블슈팅](#트러블슈팅)

---

## 🎯 시스템 개요

### PostgreSQL 전용
이 버전은 **PostgreSQL만 사용**합니다. SQLite는 지원하지 않습니다.

**장점:**
- 코드가 더 단순하고 명확함
- 로컬과 프로덕션이 동일한 DB 사용 (일관성)
- PostgreSQL 전용 기능 활용 가능

### 하이브리드 인증 시스템
- **익명 게시 가능**: 아이디/비밀번호만으로 게시 가능
- **선택적 회원 인증**: 원하는 사용자만 이메일 인증
- **인증 사용자 혜택**: ✓ 인증 배지, 비밀번호 입력 불필요, 활동 추적

---

## 🔧 필요한 환경변수

### 필수 환경변수
```bash
DATABASE_URL=postgresql://user:pass@host:port/dbname
SECRET_KEY=your-secret-key-here
ADMIN_PASSWORD=your-admin-password
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-digit-app-password
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

⚠️ **중요**: DATABASE_URL이 없으면 앱이 시작되지 않습니다!

---

## 📧 Gmail 앱 비밀번호 설정

### 1단계: Google 계정 보안 설정
1. https://myaccount.google.com/security 접속
2. **2단계 인증 활성화** (필수!)
   - 보안 → 2단계 인증
   - 전화번호로 인증 설정

### 2단계: 앱 비밀번호 생성
1. 보안 → 앱 비밀번호 (2단계 인증 활성화 후 나타남)
2. 앱 선택: **메일**
3. 기기 선택: **기타 (맞춤 이름)** → "Flask Board" 입력
4. **생성** 클릭
5. ⚠️ **16자리 비밀번호 복사** (공백 제거)
   - 예시: `abcd efgh ijkl mnop` → `abcdefghijklmnop`

### 3단계: 환경변수 설정
```bash
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=abcdefghijklmnop  # 앱 비밀번호 (공백 없이)
```

---

## 💻 로컬 개발 환경 설정

### 1. PostgreSQL 설치 (로컬)

**Windows:**
```
https://www.postgresql.org/download/windows/
→ PostgreSQL 16 다운로드 및 설치
→ 설치 시 비밀번호 설정 (기억할 것!)
```

**Mac:**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. 로컬 데이터베이스 생성

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE flask_board;

# 사용자 생성 (선택)
CREATE USER flask_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE flask_board TO flask_user;

# 종료
\q
```

### 3. 환경변수 설정 (Windows)

```cmd
# CMD
set DATABASE_URL=postgresql://postgres:your_password@localhost:5432/flask_board
set MAIL_USERNAME=your-email@gmail.com
set MAIL_PASSWORD=abcdefghijklmnop
set SECRET_KEY=your-secret-key
set ADMIN_PASSWORD=your-admin-password
set CLOUDINARY_CLOUD_NAME=your-cloud-name
set CLOUDINARY_API_KEY=your-api-key
set CLOUDINARY_API_SECRET=your-api-secret
```

```powershell
# PowerShell
$env:DATABASE_URL="postgresql://postgres:your_password@localhost:5432/flask_board"
$env:MAIL_USERNAME="your-email@gmail.com"
$env:MAIL_PASSWORD="abcdefghijklmnop"
$env:SECRET_KEY="your-secret-key"
$env:ADMIN_PASSWORD="your-admin-password"
```

### 4. 파일 교체
```bash
# 기존 파일 백업
mkdir backup
copy app.py backup\app.py
copy templates\*.html backup\

# 신규 파일로 교체
copy app_postgresql.py app.py
copy requirements_postgresql.txt requirements.txt
```

### 5. 템플릿 파일 교체
```bash
copy register.html templates\register.html
copy login.html templates\login.html
copy user_profile.html templates\user_profile.html
copy index_hybrid.html templates\index.html
copy board_hybrid.html templates\board.html
copy write_hybrid.html templates\write.html
copy view_hybrid.html templates\view.html
copy edit_hybrid.html templates\edit.html
```

### 6. 패키지 설치 및 실행
```bash
pip install -r requirements.txt
python app.py
```

### 7. 테스트
1. http://localhost:5000 접속
2. **회원가입** 클릭
3. 이메일 주소 입력 → 인증 이메일 수신 확인
4. 인증 링크 클릭 → 로그인
5. 글 작성 → "✓ 인증됨" 배지 확인

---

## 🚀 Render 배포

### 1. GitHub에 푸시
```bash
git add .
git commit -m "PostgreSQL only hybrid authentication system"
git push origin main
```

### 2. Render Dashboard 환경변수 추가
1. https://dashboard.render.com 접속
2. 프로젝트 선택 → **Environment** 탭
3. 환경변수 추가:

```
DATABASE_URL = (Render가 자동으로 제공)
MAIL_USERNAME = your-email@gmail.com
MAIL_PASSWORD = abcdefghijklmnop
SECRET_KEY = (새로 생성한 64자리)
ADMIN_PASSWORD = (새로 생성한 강력한 비밀번호)
CLOUDINARY_CLOUD_NAME = your-cloud-name
CLOUDINARY_API_KEY = your-api-key
CLOUDINARY_API_SECRET = your-api-secret
```

⚠️ **DATABASE_URL은 Render가 PostgreSQL 서비스 연결 시 자동 제공합니다!**

### 3. 재배포
- **Manual Deploy** 클릭
- 또는 자동 배포 대기 (5-10분)

### 4. 배포 확인
```bash
# 로그 확인
Dashboard → Logs

# 성공 메시지 확인
✅ PostgreSQL 데이터베이스 초기화 완료
```

---

## 🗄️ 데이터베이스 마이그레이션

### 로컬에서 마이그레이션

```bash
# 환경변수 설정 (위에서 설정한 값 사용)
python migrate_postgresql.py
```

### Render에서 마이그레이션

**방법 1: 자동 마이그레이션 (권장)**
- app.py 배포 시 `init_db()` 자동 실행
- 별도 작업 불필요

**방법 2: 수동 마이그레이션**
```bash
# Render Shell 접속
Dashboard → Shell 탭

# 마이그레이션 실행
python migrate_postgresql.py
```

### 마이그레이션 SQL
```sql
-- users 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- posts 테이블에 컬럼 추가
ALTER TABLE posts ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE posts ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);
ALTER TABLE posts ADD COLUMN IF NOT EXISTS user_agent TEXT;

-- comments 테이블에 컬럼 추가
ALTER TABLE comments ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE comments ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);
ALTER TABLE comments ADD COLUMN IF NOT EXISTS user_agent TEXT;
```

---

## 🔍 트러블슈팅

### 1. "DATABASE_URL 환경변수가 설정되지 않았습니다" 오류

**로컬:**
```bash
# 환경변수 설정 확인
echo %DATABASE_URL%  (Windows CMD)
echo $env:DATABASE_URL  (PowerShell)

# 형식 확인
postgresql://user:password@host:port/database
```

**Render:**
```
Dashboard → Environment → DATABASE_URL 확인
```

### 2. PostgreSQL 연결 실패

**오류 메시지:**
```
psycopg2.OperationalError: connection to server failed
```

**해결방법:**
```bash
# 1. PostgreSQL 서비스 실행 확인 (로컬)
# Windows: 작업 관리자 → 서비스 → postgresql 확인
# Mac: brew services list
# Linux: sudo systemctl status postgresql

# 2. DATABASE_URL 형식 확인
postgresql://user:password@localhost:5432/database

# 3. 비밀번호에 특수문자 있으면 URL 인코딩
# @ → %40
# : → %3A
```

### 3. 이메일이 발송되지 않음

**증상**: 회원가입 후 이메일이 오지 않음

**Render 로그 확인:**
```
Dashboard → Logs → "SMTP" 검색
```

**자주 발생하는 오류:**
- `SMTPAuthenticationError` → 앱 비밀번호 재확인
- `SMTPServerDisconnected` → 2단계 인증 활성화 확인

### 4. "이미 사용 중인 아이디 또는 이메일입니다" 오류

**Render 로그 확인:**
```
Dashboard → Logs

# 찾을 오류들:
relation "users" does not exist  → users 테이블 없음
SMTPAuthenticationError  → 이메일 설정 오류
```

**해결방법:**
```bash
# Render Shell에서
python
>>> from app import init_db
>>> init_db()
```

### 5. 로컬 PostgreSQL 접속 문제

**비밀번호 잊어버림:**
```bash
# PostgreSQL 재설치 또는
# pg_hba.conf 파일 수정 (trust 모드)
```

---

## ✅ 체크리스트

### 로컬 개발 전
- [ ] PostgreSQL 설치 완료
- [ ] 로컬 데이터베이스 생성 완료
- [ ] DATABASE_URL 환경변수 설정
- [ ] Gmail 앱 비밀번호 생성
- [ ] 모든 환경변수 설정 완료
- [ ] 파일 교체 완료

### Render 배포 전
- [ ] MAIL_USERNAME 환경변수 추가
- [ ] MAIL_PASSWORD 환경변수 추가
- [ ] SECRET_KEY 새로 생성 (기존 값 금지)
- [ ] ADMIN_PASSWORD 새로 생성 (apxkahd12 금지)
- [ ] DATABASE_URL 자동 설정 확인
- [ ] GitHub 푸시 완료

### 배포 후
- [ ] Render 로그 확인 (오류 없는지)
- [ ] 회원가입 테스트
- [ ] 이메일 수신 확인
- [ ] 로그인 테스트
- [ ] 게시글 작성 테스트

---

## 📞 도움이 필요하면

### 관리자 기능
```
# 사용자 활동 통계
https://your-app.onrender.com/admin/user-activity?password=your-admin-password

# 데이터 백업
https://your-app.onrender.com/admin/backup?password=your-admin-password
```

### 문제 발생 시
1. Render 로그 먼저 확인
2. 환경변수 재확인
3. 로컬에서 먼저 테스트

---

## 🎉 완료!

PostgreSQL 전용 하이브리드 인증 시스템이 성공적으로 배포되었습니다!

**로컬 개발**: PostgreSQL 사용
**프로덕션**: PostgreSQL 사용 (Render 제공)
**일관성**: 동일한 데이터베이스, 동일한 코드

질문이 있으면 언제든지 문의하세요! 😊
