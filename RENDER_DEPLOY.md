# Render.com 배포 가이드 (무료)

## 📋 준비사항
1. GitHub 계정
2. 이 프로젝트를 GitHub에 업로드

## 🚀 배포 단계

### 1단계: GitHub에 프로젝트 올리기

```bash
# 프로젝트 폴더에서
git init
git add .
git commit -m "Initial commit"

# GitHub에 새 저장소 만든 후
git remote add origin https://github.com/your-username/your-repo.git
git push -u origin main
```

### 2단계: Render 회원가입
1. https://render.com 접속
2. **"Get Started"** 또는 **"Sign Up"** 클릭
3. **"Sign in with GitHub"** 선택
4. GitHub 계정으로 로그인 및 권한 승인

### 3단계: 새 웹 서비스 생성
1. Render 대시보드에서 **"New +"** 버튼 클릭
2. **"Web Service"** 선택
3. GitHub 저장소 목록에서 프로젝트 선택
   - 저장소가 안 보이면 "Configure account" 클릭해서 권한 추가
4. **"Connect"** 클릭

### 4단계: 배포 설정
다음 설정을 확인/입력하세요:

**기본 정보:**
- **Name**: `project-board` (원하는 이름)
- **Region**: `Singapore` (한국과 가까운 지역)
- **Branch**: `main` (또는 `master`)
- **Root Directory**: 비워두기

**빌드 설정:**
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

**플랜:**
- **Instance Type**: `Free` (무료 플랜 선택)

### 5단계: 배포
1. 모든 설정 확인 후 **"Create Web Service"** 클릭
2. 자동으로 빌드 시작 (5-10분 소요)
3. 빌드 로그에서 진행 상황 확인
4. "Your service is live 🎉" 메시지 확인

### 6단계: 접속
- 생성된 URL 확인 (예: `https://project-board-xxxx.onrender.com`)
- 브라우저에서 접속하여 테스트

## ⚠️ 무료 플랜 제한사항

### 제한 사항
- **자동 슬립**: 15분간 요청 없으면 서버 중지
  - 첫 접속 시 30초-1분 정도 로딩 시간 필요
- **750시간/월**: 매월 750시간까지 무료 (한 달 내내 켜놓기 가능)
- **대역폭**: 월 100GB
- **빌드 시간**: 월 500분

### 데이터 보존
- ⚠️ **SQLite 데이터베이스**: 재배포 시 초기화됨
- ⚠️ **업로드 파일**: 재배포 시 초기화됨
- 💡 **해결책**: 
  - PostgreSQL 사용 (Render에서 무료 제공)
  - 파일은 Cloudinary나 AWS S3 사용

## 🔄 코드 업데이트 방법

코드 수정 후 GitHub에 푸시하면 자동 재배포:

```bash
git add .
git commit -m "Update message"
git push
```

Render가 자동으로 감지하고 재배포합니다!

## 🛠️ 문제 해결

### 빌드 실패
- **로그 확인**: 빌드 로그에서 에러 메시지 확인
- **Python 버전**: render.yaml에서 Python 버전 명시됨
- **의존성**: requirements.txt 파일 확인

### 서버 시작 실패
- **포트 설정**: app.py에서 PORT 환경변수 사용하는지 확인
- **로그 확인**: "Logs" 탭에서 에러 확인

### 느린 첫 로딩
- 무료 플랜은 15분 동안 요청이 없으면 슬립 모드
- 첫 접속 시 30초~1분 대기 정상

### 파일 업로드 안됨
- 무료 플랜은 ephemeral storage (임시 저장)
- 재배포 시 파일 모두 삭제됨
- 영구 저장 필요하면 외부 스토리지 사용 (Cloudinary, S3 등)

## 💰 무료 vs 유료

### 무료 플랜
- ✅ 750시간/월
- ✅ 100GB 대역폭
- ⚠️ 자동 슬립
- ⚠️ 공유 CPU/메모리

### 유료 플랜 ($7/월~)
- ✅ 항상 켜짐 (슬립 없음)
- ✅ 더 빠른 성능
- ✅ 영구 디스크
- ✅ PostgreSQL 포함

## 🎯 추천 설정

### PostgreSQL 사용하기 (무료)
1. Render 대시보드에서 **"New +"** → **"PostgreSQL"** 선택
2. 무료 플랜 선택
3. Web Service의 Environment에 DATABASE_URL 연결
4. app.py에서 SQLite 대신 PostgreSQL 사용하도록 수정

### 환경변수 설정
Render 대시보드 → Web Service → Environment:
- `SECRET_KEY`: Flask 시크릿 키
- `DATABASE_URL`: PostgreSQL URL (자동 연결 가능)

## 📚 유용한 링크
- Render 문서: https://render.com/docs
- Render 상태: https://status.render.com
- 커뮤니티: https://community.render.com

---

궁금한 점이 있으면 언제든 물어보세요! 🚀
