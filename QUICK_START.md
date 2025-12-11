# ⚡ PostgreSQL 전용 버전 빠른 설정 가이드

## 🎯 목표
기존 Flask 게시판에 PostgreSQL 전용 하이브리드 인증 시스템 적용

## ⏱️ 예상 소요 시간
- 로컬 설정: 30분
- Render 배포: 10분

---

## 📋 1단계: 사전 준비 (10분)

### ✅ PostgreSQL 설치 (로컬 개발용)
```bash
# Windows
https://www.postgresql.org/download/windows/
→ PostgreSQL 16 설치 (비밀번호 기억!)

# Mac
brew install postgresql@16
brew services start postgresql@16

# Linux
sudo apt install postgresql
```

### ✅ 데이터베이스 생성
```bash
psql -U postgres
CREATE DATABASE flask_board;
\q
```

### ✅ Gmail 앱 비밀번호 생성
1. https://myaccount.google.com/security
2. 2단계 인증 활성화
3. 앱 비밀번호 생성 → 16자리 복사 (공백 제거)

### ✅ SECRET_KEY 생성
```python
python
>>> import secrets
>>> secrets.token_hex(32)
'복사할 64자리 문자열'
```

---

## 📂 2단계: 파일 교체 (5분)

### ✅ 백업 생성
```bash
mkdir backup
copy app.py backup\
copy requirements.txt backup\
copy templates\*.html backup\
```

### ✅ Python 파일 교체
```bash
copy app_postgresql.py app.py
copy requirements_postgresql.txt requirements.txt
copy .gitignore .gitignore
copy .env.example .env
```

### ✅ 템플릿 파일 교체
```bash
# 신규 파일 추가
copy register.html templates\
copy login.html templates\
copy user_profile.html templates\

# 기존 파일 교체
copy index_hybrid.html templates\index.html
copy board_hybrid.html templates\board.html
copy write_hybrid.html templates\write.html
copy view_hybrid.html templates\view.html
copy edit_hybrid.html templates\edit.html
```

---

## ⚙️ 3단계: 환경변수 설정 (5분)

### ✅ .env 파일 편집
```bash
notepad .env
```

### ✅ 다음 값 입력:
```bash
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/flask_board
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=abcdefghijklmnop  # 앱 비밀번호 16자리
SECRET_KEY=생성한_64자리_키
ADMIN_PASSWORD=새로_만든_강력한_비밀번호
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

**⚠️ 중요:**
- MAIL_PASSWORD = Gmail **앱 비밀번호** (일반 비밀번호 아님!)
- SECRET_KEY = 새로 생성 (기존 값 사용 금지)
- ADMIN_PASSWORD = 새로 생성 (apxkahd12 사용 금지)

---

## 🔧 4단계: 로컬 테스트 (10분)

### ✅ 패키지 설치
```bash
pip install -r requirements.txt
```

### ✅ 마이그레이션 실행
```bash
python migrate_postgresql.py
# "y" 입력
```

**확인사항:**
- ✅ PostgreSQL 데이터베이스 초기화 완료
- ✅ 기존 게시글 N개 유지됨

### ✅ 앱 실행
```bash
python app.py
```

**확인사항:**
- ✅ PostgreSQL 연결 성공
- ✅ 서버 시작 성공
- ✅ http://localhost:5000 접속 가능

### ✅ 기능 테스트
1. **회원가입** 클릭
2. 아이디, 이메일, 비밀번호 입력
3. 이메일 수신 확인 (스팸함도 확인!)
4. 인증 링크 클릭
5. 로그인
6. 글 작성 → "✓ 인증됨" 배지 확인

**문제 발생 시:**
```bash
# 로그 확인
콘솔에 오류 메시지 확인

# 일반적인 오류:
❌ DATABASE_URL 오류 → .env 파일 확인
❌ SMTP 오류 → Gmail 설정 확인
❌ users 테이블 없음 → migrate_postgresql.py 재실행
```

---

## 🚀 5단계: Render 배포 (10분)

### ✅ GitHub 푸시
```bash
git add .
git commit -m "PostgreSQL only hybrid authentication"
git push origin main
```

### ✅ Render 환경변수 설정

**Dashboard → Environment → Add:**

```
MAIL_USERNAME = your-email@gmail.com
MAIL_PASSWORD = abcdefghijklmnop
SECRET_KEY = (로컬과 동일한 값)
ADMIN_PASSWORD = (로컬과 동일한 값)
CLOUDINARY_CLOUD_NAME = your-cloud-name
CLOUDINARY_API_KEY = your-api-key
CLOUDINARY_API_SECRET = your-api-secret
```

**⚠️ DATABASE_URL은 추가하지 마세요!**
→ Render가 PostgreSQL 연결 시 자동 제공

### ✅ 재배포
- **Manual Deploy** 클릭
- 또는 자동 배포 대기 (5-10분)

### ✅ 배포 확인
```bash
# 1. 로그 확인
Dashboard → Logs

# 확인사항:
✅ PostgreSQL 데이터베이스 초기화 완료
✅ Starting gunicorn

# 2. 웹사이트 접속
https://your-app.onrender.com

# 3. 회원가입 테스트
회원가입 → 이메일 수신 → 인증 → 로그인
```

---

## ✅ 최종 체크리스트

### 로컬
- [ ] PostgreSQL 설치 완료
- [ ] 데이터베이스 생성 완료
- [ ] 파일 교체 완료
- [ ] .env 파일 설정 완료
- [ ] 마이그레이션 완료
- [ ] 로컬 테스트 성공
- [ ] 회원가입/로그인 성공
- [ ] 이메일 수신 확인

### Render
- [ ] GitHub 푸시 완료
- [ ] 환경변수 8개 설정 완료
- [ ] 재배포 완료
- [ ] 로그 확인 (오류 없음)
- [ ] 웹사이트 접속 가능
- [ ] 회원가입 테스트 성공
- [ ] 이메일 수신 확인

### 보안
- [ ] .gitignore 적용됨
- [ ] .env 파일 Git에 없음
- [ ] SECRET_KEY 새로 생성
- [ ] ADMIN_PASSWORD 새로 생성
- [ ] GitHub에 비밀번호 노출 안됨

---

## 🎉 완료!

모든 단계를 완료했다면 성공입니다! 🚀

**이제 사용 가능:**
- ✅ 익명 게시 (기존)
- ✅ 회원 가입/로그인 (신규)
- ✅ 이메일 인증 (신규)
- ✅ "✓ 인증됨" 배지 (신규)
- ✅ 프로필 페이지 (신규)
- ✅ IP 추적 (관리자)

---

## 🆘 문제 해결

### 로컬에서 오류 발생
```bash
# 1. 환경변수 확인
type .env  (Windows)
cat .env   (Mac/Linux)

# 2. PostgreSQL 실행 확인
# Windows: 작업 관리자 → 서비스 → postgresql
# Mac: brew services list

# 3. 마이그레이션 재실행
python migrate_postgresql.py

# 4. 로그 확인
콘솔 출력 확인
```

### Render에서 오류 발생
```bash
# 1. 로그 확인
Dashboard → Logs

# 2. 환경변수 확인
Dashboard → Environment
(8개 모두 설정됐는지 확인)

# 3. 재배포
Manual Deploy 클릭
```

### 이메일 안옴
```bash
# 1. 스팸함 확인
# 2. 앱 비밀번호 재확인 (16자리)
# 3. 2단계 인증 확인
# 4. Render 로그에서 SMTP 오류 확인
```

---

## 📚 추가 문서

더 자세한 정보는 다음 문서를 참고하세요:

- `README_POSTGRESQL.md` - 전체 개요
- `DEPLOYMENT_GUIDE_POSTGRESQL.md` - 상세 가이드
- `.env.example` - 환경변수 예시

---

**소요 시간:**
- ✅ 1단계: 10분
- ✅ 2단계: 5분
- ✅ 3단계: 5분
- ✅ 4단계: 10분
- ✅ 5단계: 10분
**총합: 40분**

수고하셨습니다! 🎊
