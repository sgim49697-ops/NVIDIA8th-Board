# Render.com PostgreSQL 배포 가이드

## 🎯 왜 PostgreSQL?

```
SQLite (기본):
❌ 재배포 시 데이터 삭제
❌ 업로드 파일도 삭제
❌ 프로덕션 부적합

PostgreSQL (Render):
✅ 데이터 영구 보존
✅ 무료 1GB 저장소
✅ 프로덕션 준비 완료
```

## 📋 배포 단계

### 1. GitHub 업로드
```bash
git init
git add .
git commit -m "Initial commit"
git push -u origin main
```

### 2. PostgreSQL 생성 (Render)
1. https://render.com → "New +" → "PostgreSQL"
2. 설정:
   - Name: `project-board-db`
   - Region: `Singapore`
   - Plan: `Free`
3. "Create Database"
4. **Internal Database URL** 복사

### 3. Web Service 생성
1. "New +" → "Web Service"
2. GitHub 저장소 연결
3. 설정:
   - Build: `pip install -r requirements.txt`
   - Start: `python app.py`
   - Instance: `Free`

### 4. 환경변수 설정
Environment 탭에서 추가:
```
DATABASE_URL = (PostgreSQL의 Internal Database URL)
ADMIN_PASSWORD = your-admin-password
SECRET_KEY = random-secret-key
```

### 5. 배포
"Create Web Service" 클릭!

## 🔄 자동 전환

코드가 자동으로 DB를 선택합니다:

```python
# DATABASE_URL 환경변수 있음? → PostgreSQL
# DATABASE_URL 환경변수 없음? → SQLite
```

로컬: SQLite (board.db)
Render: PostgreSQL (자동)

## 💾 백업 방법

### Render 대시보드
1. PostgreSQL 서비스 페이지
2. "Backups" 탭
3. "Create Backup"

### pg_dump (추천)
```bash
# URL 설정
export DATABASE_URL="postgresql://..."

# 백업
pg_dump $DATABASE_URL > backup_2025_12_09.sql

# 복원
psql $DATABASE_URL < backup_2025_12_09.sql
```

## 🔧 문제 해결

### "relation does not exist" 에러
```bash
# 테이블이 생성되지 않음
# 해결: 웹 서비스 재시작 또는 로그 확인
```

### DATABASE_URL 연결 실패
```bash
# Internal Database URL 사용했는지 확인
# External URL은 외부 접속용
```

### 한글 깨짐
```bash
# PostgreSQL은 UTF-8 기본 설정됨
# 문제 없음
```

## 💰 무료 vs 유료

| 항목 | Free | Starter ($7/월) |
|------|------|-----------------|
| DB 크기 | 1GB | 10GB |
| 자동 백업 | ❌ | ✅ (매일) |
| 연결 수 | 제한 | 더 많음 |
| 슬립 | 15분 | ❌ 없음 |

## 📊 데이터 관리

### 데이터 확인
```bash
# psql 접속
psql $DATABASE_URL

# 테이블 목록
\dt

# 게시글 수 확인
SELECT COUNT(*) FROM posts;

# 게시판별 게시글 수
SELECT board_type, COUNT(*) FROM posts GROUP BY board_type;
```

### 데이터 정리
```bash
# 모든 댓글 삭제
DELETE FROM comments;

# 특정 게시판 글 삭제
DELETE FROM posts WHERE board_type = 'test';
```

## 🎯 추천 백업 일정

```
주 1회: 수동 백업
월 1회: 로컬에 다운로드
중요 작업 전: 즉시 백업
```

## 📝 참고사항

- 무료 플랜: 1GB 충분 (게시글 수만 개)
- 재배포해도 데이터 유지됨
- 파일 업로드는 여전히 삭제됨 (Cloudinary 권장)
- PostgreSQL 무료 플랜: 영구 제공

---

궁금한 점이 있으면 Issues에 남겨주세요!
