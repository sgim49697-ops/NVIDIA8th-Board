# 🚀 GitHub → Render 배포 완벽 가이드

프로젝트 게시판을 GitHub에 올리고 Render로 무료 배포하는 방법입니다.

---

## 📋 1단계: GitHub 저장소 만들기

### 1-1. GitHub 사이트에서 저장소 생성
1. https://github.com 접속 후 로그인
2. 우측 상단 **"+"** 버튼 클릭 → **"New repository"** 선택
3. 저장소 정보 입력:
   - **Repository name**: `project-board` (원하는 이름)
   - **Description**: "Flask 기반 게시판" (선택사항)
   - **Public** 또는 **Private** 선택
   - ⚠️ **"Initialize this repository with a README"는 체크하지 않기**
4. **"Create repository"** 클릭

### 1-2. 저장소 URL 복사
생성된 페이지에서 저장소 URL을 복사하세요.
예: `https://github.com/your-username/project-board.git`

---

## 💻 2단계: 로컬에서 Git 설정 및 업로드

### 2-1. 프로젝트 폴더로 이동
```bash
cd project_board
```

### 2-2. Git 초기화 및 커밋
```bash
# Git 저장소 초기화
git init

# 모든 파일 추가
git add .

# 첫 커밋
git commit -m "Initial commit: Flask 게시판 프로젝트"
```

### 2-3. GitHub에 업로드
```bash
# GitHub 저장소 연결 (your-username과 your-repo를 실제 값으로 변경)
git remote add origin https://github.com/your-username/project-board.git

# 메인 브랜치로 변경 (필요시)
git branch -M main

# GitHub에 푸시
git push -u origin main
```

**Git 인증 방법:**
- **방법 1 (권장)**: GitHub Personal Access Token 사용
  1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. "Generate new token (classic)" 클릭
  3. repo 권한 선택 후 생성
  4. 생성된 토큰을 비밀번호 대신 사용
  
- **방법 2**: SSH Key 사용
  - https://docs.github.com/ko/authentication/connecting-to-github-with-ssh

---

## 🌐 3단계: Render에서 배포하기

### 3-1. Render 회원가입
1. https://render.com 접속
2. **"Get Started"** 클릭
3. **"Sign in with GitHub"** 선택 (GitHub 계정으로 간편 가입)
4. 권한 승인

### 3-2. 새 웹 서비스 생성
1. Render 대시보드에서 **"New +"** 버튼 클릭
2. **"Web Service"** 선택
3. 오른쪽에서 **"Connect a repository"** 또는 GitHub 저장소 목록 확인
4. `project-board` 저장소 찾아서 **"Connect"** 클릭
   - 저장소가 안 보이면 **"Configure account"** 클릭해서 Render에 권한 추가

### 3-3. 배포 설정 입력

**기본 설정:**
- **Name**: `project-board` (또는 원하는 이름)
- **Region**: `Singapore` (한국과 가까움) 
- **Branch**: `main`
- **Root Directory**: (비워두기)

**빌드 설정:**
- **Runtime**: `Python 3` (자동 선택됨)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

**플랜 선택:**
- **Instance Type**: `Free` ✅ (무료 플랜)

**환경변수 설정 (선택사항):**
"Advanced" → "Add Environment Variable" 클릭
- `SECRET_KEY`: `your-secret-key-here-change-this` (랜덤 문자열로 변경 권장)
- `ADMIN_PASSWORD`: `admin1234` (관리자 비밀번호, 변경 권장)

### 3-4. 배포 시작
1. **"Create Web Service"** 클릭
2. 자동으로 빌드 시작 (5-10분 소요)
3. 로그 창에서 진행 상황 확인:
   ```
   ==> Downloading Python dependencies
   ==> Building...
   ==> Starting service...
   Your service is live 🎉
   ```

### 3-5. 접속 확인
- 상단에 표시된 URL로 접속
- 예: `https://project-board-xxxx.onrender.com`
- 첫 접속은 30초~1분 정도 걸릴 수 있음 (Cold Start)

---

## ⚠️ 중요: 무료 플랜 제한사항

### 데이터 손실 주의
현재 프로젝트는 **SQLite**를 사용하므로:
- ⚠️ **재배포 시 모든 게시글/댓글 삭제됨**
- ⚠️ **업로드된 파일도 모두 삭제됨**
- 코드 업데이트 후 GitHub에 푸시하면 자동 재배포되면서 데이터 초기화

### 자동 슬립 (Sleep)
- 15분간 요청이 없으면 서버가 자동으로 잠듦
- 다음 접속 시 30초~1분 대기 필요 (Cold Start)
- 24/7 운영 가능하지만 방문자가 없으면 잠듦

### 해결 방법
**PostgreSQL 사용 (권장):**
- Render에서 PostgreSQL 무료 제공 (90일, 갱신 가능)
- 데이터 영구 보존 가능
- 설정 방법은 아래 "PostgreSQL 연결하기" 참고

---

## 🔄 4단계: 코드 수정 후 업데이트

코드를 수정했다면:

```bash
# 변경사항 확인
git status

# 변경된 파일 추가
git add .

# 커밋
git commit -m "기능 추가: 댓글 수정 기능"

# GitHub에 푸시
git push
```

Render가 자동으로 GitHub를 감시하고 있다가 새로운 커밋을 감지하면 자동으로 재배포합니다! 🎉

---

## 🗃️ (선택) PostgreSQL 연결하기

### 5-1. PostgreSQL 생성
1. Render 대시보드 → **"New +"** → **"PostgreSQL"**
2. 이름 입력 (예: `project-board-db`)
3. **"Free"** 플랜 선택
4. **"Create Database"** 클릭

### 5-2. 환경변수 자동 연결
1. Web Service 페이지로 이동
2. 좌측 메뉴 **"Environment"** 클릭
3. **"Add Environment Variable"** → **"Add from Database"** 선택
4. 생성한 PostgreSQL 선택
5. `DATABASE_URL` 자동 추가됨

### 5-3. 코드 수정 (app.py)
SQLite 대신 PostgreSQL 사용하도록 코드 수정 필요
- 별도 요청 시 수정된 코드 제공 가능

---

## 🛠️ 문제 해결

### 빌드 실패
**증상**: "Build failed" 메시지
**해결**:
1. Render 로그에서 에러 메시지 확인
2. `requirements.txt`에 모든 패키지가 있는지 확인
3. Python 버전 문제일 경우 `render.yaml`에서 버전 지정

### 서버 시작 실패
**증상**: 빌드는 성공했지만 서버가 시작 안 됨
**해결**:
1. "Logs" 탭에서 에러 확인
2. Start Command가 `python app.py`인지 확인
3. `app.py`에서 `PORT` 환경변수를 제대로 사용하는지 확인

### GitHub 푸시 안됨
**증상**: `git push` 시 인증 오류
**해결**:
1. Personal Access Token 재생성
2. 또는 SSH Key 설정

### 게시판이 너무 느려요
**무료 플랜 특성**:
- Cold Start: 15분 미사용 시 슬립, 재접속 시 30초 대기
- 해결: UptimeRobot 같은 서비스로 주기적 핑
- 또는 유료 플랜 ($7/월) 사용

---

## 📊 배포 상태 확인

### Render 대시보드에서:
- **Logs**: 실시간 서버 로그
- **Events**: 배포 이력
- **Metrics**: CPU/메모리 사용량
- **Settings**: 각종 설정 변경

### GitHub에서:
- **Commits**: 코드 변경 이력
- **Actions** (선택사항): CI/CD 설정 가능

---

## 🎯 추천 설정

### 1. 환경변수 설정
```
SECRET_KEY=랜덤-긴-문자열-여기에
ADMIN_PASSWORD=강력한-비밀번호
```

### 2. Cold Start 방지
UptimeRobot (무료) 사용:
1. https://uptimerobot.com 가입
2. Monitor 추가
3. URL: Render에서 받은 URL
4. Interval: 5분
5. Monitor Type: HTTP(s)

### 3. 커스텀 도메인 (선택)
- Render Settings → Custom Domain
- 무료 플랜에서도 사용 가능

---

## 💡 유용한 팁

### Git 기본 명령어
```bash
git status          # 변경사항 확인
git add .           # 모든 변경사항 추가
git add 파일명       # 특정 파일만 추가
git commit -m "메시지"  # 커밋
git push            # GitHub에 업로드
git pull            # GitHub에서 다운로드
git log             # 커밋 이력 확인
```

### Render CLI (선택사항)
```bash
# Render CLI 설치
npm install -g @render/cli

# 로그인
render login

# 서비스 확인
render services list

# 로그 실시간 확인
render logs -f
```

---

## 📚 참고 자료

- **Render 공식 문서**: https://render.com/docs
- **GitHub 가이드**: https://docs.github.com/ko
- **Flask 문서**: https://flask.palletsprojects.com/
- **Render 커뮤니티**: https://community.render.com

---

## 🎉 완료!

이제 여러분의 게시판이 인터넷에 배포되었습니다!

**접속 URL**: `https://project-board-xxxx.onrender.com`

친구들에게 공유해보세요! 🚀

---

### 다음 단계 제안:
1. ✅ PostgreSQL로 데이터베이스 전환 (데이터 보존)
2. ✅ 파일 업로드를 AWS S3나 Cloudinary로 변경
3. ✅ 커스텀 도메인 연결
4. ✅ HTTPS 자동 적용됨 (Render가 제공)
5. ✅ Google Analytics 추가 (방문자 통계)

궁금한 점이 있으면 언제든 물어보세요! 😊
