# SQLite → PostgreSQL 데이터 마이그레이션 가이드

현재 Render에서 SQLite로 실행 중이고 게시글이 이미 있는 상태에서 PostgreSQL로 전환하는 방법입니다.

## 🎯 개요

현재: SQLite + 게시글 있음
목표: PostgreSQL + 데이터 보존

⚠️ 단순 재배포하면 데이터 삭제됨!

## ⭐ 추천: 백업 API 사용 (3단계)

### 1️⃣ 백업 다운로드

브라우저에서:
```
https://your-app.onrender.com/admin/backup?password=admin1234
```

→ backup.json 다운로드됨

### 2️⃣ PostgreSQL 연결

1. Render: New + → PostgreSQL (Singapore, Free)
2. Internal Database URL 복사
3. Web Service → Environment 추가:
   - DATABASE_URL = (복사한 URL)
   - ADMIN_PASSWORD = admin1234  
   - SECRET_KEY = random-string
4. Save → 재배포 대기 (2-3분)

### 3️⃣ 데이터 복원

Windows PowerShell:
```powershell
curl.exe -X POST https://your-app.onrender.com/admin/restore `
  -F "password=admin1234" `
  -F "backup_file=@backup.json"
```

Mac/Linux:
```bash
curl -X POST https://your-app.onrender.com/admin/restore \
  -F "password=admin1234" \
  -F "backup_file=@backup.json"
```

✅ 완료! 사이트에서 게시글 확인

---

## 방법 2: Render Shell 사용

### 1️⃣ 백업
Web Service → Shell 버튼:
```bash
python backup_db.py backup
cat backup_*.json
```
→ 내용 복사하여 로컬 저장

### 2️⃣ PostgreSQL 연결 (위와 동일)

### 3️⃣ 복원
Shell에서:
```bash
cat > backup.json << 'EOF'
(복사한 내용 붙여넣기)
EOF

python backup_db.py restore backup.json
```

---

## 체크리스트

- [ ] 백업 다운로드 (/admin/backup?password=...)
- [ ] PostgreSQL 생성
- [ ] DATABASE_URL 환경변수 추가
- [ ] 재배포 완료
- [ ] 복원 실행
- [ ] 게시글 확인 ✅
