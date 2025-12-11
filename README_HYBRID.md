# 🔐 Flask 게시판 - 하이브리드 인증 시스템

## 📦 제공 파일 목록

### Python 파일
- `app_hybrid.py` - 하이브리드 인증 시스템이 적용된 메인 앱
- `migrate_to_hybrid.py` - 데이터베이스 마이그레이션 스크립트
- `requirements_hybrid.txt` - 필요한 Python 패키지 목록

### HTML 템플릿 (templates/ 폴더에 넣기)
- `register.html` - 회원가입 페이지
- `login.html` - 로그인 페이지
- `user_profile.html` - 사용자 프로필 페이지
- `index_hybrid.html` - 메인 페이지 (로그인 링크 추가)
- `board_hybrid.html` - 게시판 목록 (인증 배지 표시)
- `write_hybrid.html` - 글쓰기 페이지 (로그인 사용자 편의 기능)
- `view_hybrid.html` - 게시글 보기 (프로필 링크, 인증 배지)
- `edit_hybrid.html` - 게시글 수정 (로그인 사용자 편의 기능)

### 문서
- `DEPLOYMENT_GUIDE_HYBRID.md` - 상세 배포 가이드
- `README_HYBRID.md` - 이 파일

---

## 🚀 빠른 시작 가이드

### 1️⃣ Gmail 앱 비밀번호 생성

1. https://myaccount.google.com/security 접속
2. **2단계 인증** 활성화
3. **앱 비밀번호** 생성 (메일 앱)
4. 16자리 비밀번호 복사 (공백 제거)

### 2️⃣ 파일 교체

```bash
# 백업 (안전을 위해)
mkdir backup
copy app.py backup\
copy templates\*.html backup\

# 신규 파일로 교체
copy app_hybrid.py app.py
copy requirements_hybrid.txt requirements.txt

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

### 3️⃣ 환경변수 설정

#### Windows CMD
```cmd
set MAIL_USERNAME=your-email@gmail.com
set MAIL_PASSWORD=abcdefghijklmnop
set SECRET_KEY=your-secret-key
set ADMIN_PASSWORD=your-admin-password
```

#### Windows PowerShell
```powershell
$env:MAIL_USERNAME="your-email@gmail.com"
$env:MAIL_PASSWORD="abcdefghijklmnop"
$env:SECRET_KEY="your-secret-key"
$env:ADMIN_PASSWORD="your-admin-password"
```

### 4️⃣ 데이터베이스 마이그레이션

```bash
python migrate_to_hybrid.py
```

- 기존 게시글/댓글 유지됨
- users 테이블 자동 생성
- user_id, ip_address, user_agent 컬럼 추가

### 5️⃣ 패키지 설치 및 실행

```bash
pip install -r requirements.txt --break-system-packages
python app.py
```

### 6️⃣ 테스트

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
git commit -m "Add hybrid authentication system"
git push origin main
```

### 2. Render 환경변수 추가

Dashboard → Environment → Add Environment Variable:
```
MAIL_USERNAME = your-email@gmail.com
MAIL_PASSWORD = abcdefghijklmnop
SECRET_KEY = your-secret-key
ADMIN_PASSWORD = your-admin-password
```

### 3. 재배포
- Manual Deploy 클릭
- 또는 자동 배포 대기

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

# IP 주소 확인 (게시글 ID 필요)
https://your-app.onrender.com/admin/check-ip?password=ADMIN_PASSWORD&post_id=1
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

### 이메일이 발송되지 않음
- 2단계 인증 활성화 확인
- 앱 비밀번호 (16자리) 사용 확인
- 스팸함 확인

### 환경변수 오류
```python
# 환경변수 확인
import os
print(os.environ.get('MAIL_USERNAME'))
print(os.environ.get('MAIL_PASSWORD'))
```

### 데이터베이스 오류
```bash
# 마이그레이션 재실행
python migrate_to_hybrid.py
```

---

## 📈 시스템 비교

| 기능 | 기존 시스템 | 하이브리드 시스템 |
|------|------------|-----------------|
| 익명 게시 | ✅ | ✅ |
| 회원 가입 | ❌ | ✅ (선택) |
| 인증 배지 | ❌ | ✅ |
| 프로필 페이지 | ❌ | ✅ |
| 비밀번호 불필요 | ❌ | ✅ (회원) |
| IP 추적 | ❌ | ✅ |
| 활동 통계 | ❌ | ✅ |

---

## 💡 사용 팁

### 회원 vs 익명 선택 기준
- **익명 추천**: 가벼운 질문, 일회성 글
- **회원 추천**: 지속적 활동, 프로필 관리 필요

### 관리자 기능
- IP 추적으로 도배 감지
- 사용자 활동 통계로 커뮤니티 분석
- 동일인 여부 확인 가능

### 보안 권장사항
- 관리자 비밀번호 정기 변경
- SECRET_KEY는 무작위 생성 (최소 32자)
- HTTPS 사용 (Render는 자동 제공)

---

## 📞 추가 도움

자세한 내용은 `DEPLOYMENT_GUIDE_HYBRID.md`를 참고하세요!

- Gmail 설정 상세 가이드
- Render 배포 단계별 설명
- 트러블슈팅 상세 해결 방법

---

## 🎉 완료!

하이브리드 인증 시스템으로 업그레이드 완료! 🚀

질문이 있으면 언제든지 문의하세요! 😊
