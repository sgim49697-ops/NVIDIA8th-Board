# 🔐 하이브리드 인증 시스템 배포 가이드

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [필요한 환경변수](#필요한-환경변수)
3. [Gmail 앱 비밀번호 설정](#gmail-앱-비밀번호-설정)
4. [로컬 테스트](#로컬-테스트)
5. [Render 배포](#render-배포)
6. [데이터베이스 마이그레이션](#데이터베이스-마이그레이션)
7. [트러블슈팅](#트러블슈팅)

---

## 🎯 시스템 개요

### 하이브리드 인증 시스템이란?
- **익명 게시 가능**: 기존처럼 아이디/비밀번호만으로 게시 가능
- **선택적 회원 인증**: 원하는 사용자만 이메일 인증 후 회원 가입
- **인증 사용자 혜택**:
  - ✓ 인증 배지 표시
  - 비밀번호 입력 불필요 (자동 로그인)
  - 활동 추적 및 프로필 페이지
  - 내가 쓴 글/댓글 모아보기

### 주요 기능
✅ 이메일 인증 회원가입
✅ 로그인/로그아웃
✅ 익명 + 회원 혼합 게시
✅ 사용자 프로필 페이지
✅ IP 주소 추적 (관리자 전용)
✅ 관리자 활동 통계

---

## 🔧 필요한 환경변수

### 기존 환경변수 (유지)
```bash
SECRET_KEY=your-secret-key-here
ADMIN_PASSWORD=your-admin-password
DATABASE_URL=postgresql://...
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### 신규 환경변수 (추가 필요) ⭐
```bash
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-digit-app-password
```

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

## 💻 로컬 테스트

### 1. 파일 교체
```bash
# 기존 파일 백업
mkdir backup
copy app.py backup\app.py
copy templates\*.html backup\

# 신규 파일로 교체
copy app_hybrid.py app.py
copy requirements_hybrid.txt requirements.txt
copy register.html templates\register.html
copy login.html templates\login.html
copy user_profile.html templates\user_profile.html
copy index_hybrid.html templates\index.html
copy board_hybrid.html templates\board.html
copy write_hybrid.html templates\write.html
copy view_hybrid.html templates\view.html
copy edit_hybrid.html templates\edit.html
```

### 2. 환경변수 설정 (Windows)
```cmd
# CMD
set MAIL_USERNAME=your-email@gmail.com
set MAIL_PASSWORD=abcdefghijklmnop
set SECRET_KEY=your-secret-key
set ADMIN_PASSWORD=your-admin-password
```

```powershell
# PowerShell
$env:MAIL_USERNAME="your-email@gmail.com"
$env:MAIL_PASSWORD="abcdefghijklmnop"
$env:SECRET_KEY="your-secret-key"
$env:ADMIN_PASSWORD="your-admin-password"
```

### 3. 패키지 설치 및 실행
```bash
pip install -r requirements.txt --break-system-packages
python app.py
```

### 4. 테스트
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
git commit -m "Add hybrid authentication system"
git push origin main
```

### 2. Render Dashboard 환경변수 추가
1. https://dashboard.render.com 접속
2. 프로젝트 선택 → **Environment** 탭
3. 환경변수 추가:

```
MAIL_USERNAME = your-email@gmail.com
MAIL_PASSWORD = abcdefghijklmnop
```

### 3. 재배포
- **Manual Deploy** 클릭
- 또는 자동 배포 대기 (5-10분)

### 4. 배포 확인
```bash
# 로그 확인
curl https://your-app.onrender.com

# 회원가입 테스트
https://your-app.onrender.com/register
```

---

## 🗄️ 데이터베이스 마이그레이션

### PostgreSQL (Render)
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

### SQLite (로컬)
- app.py 실행 시 자동으로 테이블 생성됨
- 기존 데이터 유지됨 (user_id는 NULL로 설정)

---

## 🔍 트러블슈팅

### 1. 이메일이 발송되지 않음
**증상**: 회원가입 후 이메일이 오지 않음

**해결방법**:
```python
# 1. 환경변수 확인
import os
print(os.environ.get('MAIL_USERNAME'))  # None이면 설정 안됨
print(os.environ.get('MAIL_PASSWORD'))

# 2. Gmail "보안 수준이 낮은 앱" 허용 (옛날 방식, 권장하지 않음)
# → 대신 앱 비밀번호 사용!

# 3. Render 로그 확인
# Dashboard → Logs → "SMTPAuthenticationError" 검색
```

**자주 발생하는 오류**:
- `SMTPAuthenticationError: (535, b'Username and Password not accepted')` 
  → 앱 비밀번호가 아닌 일반 비밀번호 사용
- `SMTPServerDisconnected: Connection unexpectedly closed`
  → 2단계 인증 미활성화

### 2. "SECRET_KEY 환경변수가 설정되지 않았습니다" 오류
**증상**: 앱 시작 시 ValueError 발생

**해결방법**:
```bash
# Render Dashboard → Environment
SECRET_KEY = your-secret-key-here
ADMIN_PASSWORD = your-admin-password
```

### 3. 데이터베이스 에러
**증상**: `relation "users" does not exist`

**해결방법**:
```bash
# app.py에서 init_db() 자동 실행됨
# 수동 실행 필요 시:
python
>>> from app import init_db
>>> init_db()
```

### 4. 기존 게시글이 사라짐
**해결방법**: 
- 기존 게시글은 user_id가 NULL로 설정되어 익명 게시글로 유지됨
- 삭제되지 않음! 안심하세요 ✅

### 5. 인증 이메일 스팸함 확인
- Gmail 스팸함 확인
- 발신자: MAIL_USERNAME에 설정한 이메일

---

## ✅ 체크리스트

### 배포 전
- [ ] Gmail 2단계 인증 활성화
- [ ] 앱 비밀번호 16자리 생성 및 복사
- [ ] 모든 파일 교체 완료
- [ ] 로컬 테스트 성공 (이메일 수신 확인)

### Render 배포
- [ ] MAIL_USERNAME 환경변수 추가
- [ ] MAIL_PASSWORD 환경변수 추가
- [ ] GitHub 푸시 완료
- [ ] Render 재배포 완료
- [ ] 배포 후 회원가입 테스트

### 추가 작업
- [ ] 기존 관리자 비밀번호 GitHub에서 삭제
- [ ] .gitignore에 .env 추가
- [ ] 개인정보처리방침 페이지 작성 (선택)

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
1. Render 로그 확인
2. 환경변수 재확인
3. 로컬에서 먼저 테스트

---

## 🎉 완료!

하이브리드 인증 시스템이 성공적으로 배포되었습니다!

**익명 사용자**: 기존처럼 자유롭게 게시 가능
**회원 사용자**: 이메일 인증 후 편리하게 활동

질문이 있으면 언제든지 문의하세요! 😊
