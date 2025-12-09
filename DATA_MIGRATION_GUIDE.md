# 데이터 보존 완벽 가이드

## 🎉 좋은 소식!

app.py에 백업/복원 API가 이미 포함되어 있습니다!

## 📥 1단계: 현재 데이터 백업 (PostgreSQL 추가 전)

### 브라우저에서 백업 다운로드

```
https://your-app.onrender.com/admin/backup?password=admin1234
```

1. 위 URL을 브라우저에 입력 (your-app을 실제 앱 이름으로 변경)
2. `password=` 뒤에 관리자 비밀번호 입력
3. JSON 데이터가 표시됨
4. 우클릭 → "다른 이름으로 저장" → `backup.json`

또는 **curl 사용:**

```bash
curl "https://your-app.onrender.com/admin/backup?password=admin1234" > backup.json
```

## 🔄 2단계: PostgreSQL 환경변수 추가

Render Web Service:
1. Environment 탭
2. 환경변수 추가:
   - DATABASE_URL
   - ADMIN_PASSWORD (변경했다면)
   - SECRET_KEY
3. Save Changes → 자동 재배포

## 📤 3단계: 데이터 복원 (PostgreSQL로 전환 후)

재배포 완료 후:

### curl 사용 (추천):

```bash
curl -X POST \
  -F "password=admin1234" \
  -F "backup_file=@backup.json" \
  https://your-app.onrender.com/admin/restore
```

### Python 스크립트 사용:

```python
import requests

url = "https://your-app.onrender.com/admin/restore"
files = {'backup_file': open('backup.json', 'rb')}
data = {'password': 'admin1234'}

response = requests.post(url, files=files, data=data)
print(response.text)
```

## ✅ 완료 확인

1. 사이트 접속
2. 게시판 확인
3. 모든 게시글과 댓글이 복원되었는지 확인

## 🎯 전체 프로세스 요약

```
1. 백업 다운로드
   ↓
   https://your-app.onrender.com/admin/backup?password=admin1234
   ↓
   backup.json 저장

2. PostgreSQL 설정
   ↓
   DATABASE_URL 환경변수 추가
   ↓
   자동 재배포 (2-3분)

3. 데이터 복원
   ↓
   curl -X POST -F "password=admin1234" -F "backup_file=@backup.json" \
   https://your-app.onrender.com/admin/restore
   ↓
   완료! ✅
```

## ⚠️ 주의사항

### 관리자 비밀번호
- 기본값: `admin1234`
- 변경했다면 환경변수 `ADMIN_PASSWORD` 확인

### 타이밍
1. **먼저** 백업 다운로드
2. **그 다음** PostgreSQL 설정
3. **마지막** 복원

### 백업 파일 보관
- 안전한 곳에 백업 파일 보관
- 혹시 모를 상황에 대비

## 🆘 문제 해결

### "Unauthorized" 에러
→ 관리자 비밀번호 확인

### 복원 후 게시글 없음
→ backup.json 내용 확인 (비어있지 않은지)

### API 접근 불가
→ 앱이 정상 실행 중인지 확인

## 💡 팁

### 로컬에서 테스트
로컬에서도 동일하게 작동합니다:

```bash
# 백업
curl "http://localhost:5000/admin/backup?password=admin1234" > backup.json

# 복원
curl -X POST \
  -F "password=admin1234" \
  -F "backup_file=@backup.json" \
  http://localhost:5000/admin/restore
```
