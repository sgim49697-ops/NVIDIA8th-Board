# 🚨 Render 포트 바인딩 오류 해결 가이드

## 오류 메시지
```
Port scan timeout reached, no open ports detected on 0.0.0.0.
Detected open ports on localhost -- did you mean to bind one of these to 0.0.0.0?
```

---

## 🔍 원인 분석

### 문제점 1: Procfile에서 개발 서버 사용
```
❌ web: python app.py
```

- `python app.py`는 Flask 개발 서버를 실행
- 프로덕션 환경에 부적합 (성능, 안정성 문제)
- Render에서 제대로 작동하지 않을 수 있음

### 문제점 2: render.yaml에서도 동일한 문제
```yaml
❌ startCommand: python app.py
```

### 문제점 3: runtime.txt 인코딩 오류
- UTF-16 BOM으로 인코딩되어 있음
- UTF-8로 수정 필요

---

## ✅ 해결 방법

### 1️⃣ Procfile 수정

**변경 전:**
```
web: python app.py
```

**변경 후:**
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

**설명:**
- `gunicorn`: 프로덕션용 WSGI 서버
- `app:app`: 첫 번째 `app`은 파일명(app.py), 두 번째 `app`은 Flask 앱 객체
- `--bind 0.0.0.0:$PORT`: Render의 PORT 환경변수 사용

---

### 2️⃣ render.yaml 수정 (선택사항)

**변경 전:**
```yaml
services:
  - type: web
    name: project-board
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

**변경 후:**
```yaml
services:
  - type: web
    name: nvidia8th-board
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

**참고:** Procfile이 있으면 우선 적용되므로, render.yaml 수정은 선택사항입니다.

---

### 3️⃣ runtime.txt 수정

**변경 전:**
```
\xff\xfep y t h o n - 3 . 1 1 . 9      (인코딩 오류)
```

**변경 후:**
```
python-3.11.9
```

---

## 🚀 적용 방법

### 방법 1: GitHub를 통한 배포 (권장)

```bash
# 1. 로컬에서 파일 수정
cd C:\Project_bulletin\Nvidia8Board

# 2. Procfile 수정
echo web: gunicorn app:app --bind 0.0.0.0:$PORT > Procfile

# 3. runtime.txt 수정
echo python-3.11.9 > runtime.txt

# 4. Git에 커밋 및 푸시
git add Procfile runtime.txt
git commit -m "Fix Render port binding issue"
git push origin main

# 5. Render가 자동으로 재배포
```

### 방법 2: Render 대시보드에서 직접 수정

1. Render 대시보드 접속
2. 서비스 선택
3. **Settings** → **Build & Deploy** 섹션
4. **Start Command** 항목 찾기
5. 다음으로 변경:
   ```
   gunicorn app:app --bind 0.0.0.0:$PORT
   ```
6. **Save Changes**
7. **Manual Deploy** → **Deploy latest commit**

---

## 📋 체크리스트

적용 전 확인사항:

- [ ] `requirements.txt`에 `gunicorn==21.2.0` 포함 확인 ✅ (이미 있음)
- [ ] `Procfile` 수정: `web: gunicorn app:app --bind 0.0.0.0:$PORT`
- [ ] `runtime.txt` 수정: `python-3.11.9`
- [ ] Git에 커밋 및 푸시
- [ ] Render에서 자동 배포 확인

---

## 🧪 배포 후 테스트

### 1. Render 로그 확인

배포 후 Render 대시보드의 **Logs** 탭에서:

```
✅ 정상 로그:
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:10000
[INFO] Using worker: sync
[INFO] Booting worker with pid: 123
```

```
❌ 오류 로그:
Port scan timeout reached
No open ports detected on 0.0.0.0
```

### 2. 웹사이트 접속 테스트

```
https://nvidia8th-board.onrender.com/
```

- ✅ 정상: 메인 페이지가 로드됨
- ❌ 오류: 503 Service Unavailable

---

## 🔧 추가 최적화 (선택사항)

### Gunicorn 워커 설정

더 나은 성능을 위해 Procfile을 다음과 같이 수정할 수 있습니다:

```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120
```

**옵션 설명:**
- `--workers 2`: 워커 프로세스 2개 (무료 플랜에서는 1-2개 권장)
- `--threads 2`: 워커당 스레드 2개
- `--timeout 120`: 요청 타임아웃 120초

---

## 🆘 여전히 문제가 있을 때

### 1. 환경변수 확인

Render 대시보드에서 다음 환경변수가 설정되어 있는지 확인:

- `DATABASE_URL` (PostgreSQL 연결 정보)
- `SECRET_KEY`
- `ADMIN_PASSWORD`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

### 2. 로그에서 오류 확인

```bash
# Render 로그에서 에러 검색
# "error", "failed", "exception" 키워드 확인
```

### 3. 데이터베이스 연결 확인

```python
# app.py의 init_db()가 정상 실행되는지 확인
# PostgreSQL 연결 정보가 올바른지 확인
```

---

## 📌 참고 자료

- [Render Port Binding 문서](https://render.com/docs/web-services#port-binding)
- [Gunicorn 공식 문서](https://docs.gunicorn.org/en/stable/configure.html)
- [Flask Deployment 가이드](https://flask.palletsprojects.com/en/3.0.x/deploying/)

---

## 💡 핵심 요약

1. **Procfile 수정**: `web: gunicorn app:app --bind 0.0.0.0:$PORT`
2. **runtime.txt 수정**: `python-3.11.9`
3. **Git 푸시**: 변경사항을 GitHub에 푸시
4. **Render 자동 배포**: Render가 자동으로 재배포
5. **로그 확인**: 배포 성공 여부 확인

이제 Render에 정상적으로 배포될 것입니다! 🎉
