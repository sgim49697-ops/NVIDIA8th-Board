# 🔄 Cloudinary 파일 마이그레이션 가이드

## 📋 개요

기존 `uploads` 폴더에 있는 파일을 Cloudinary로 이전하는 스크립트입니다.

**실행 시점:** 
- 코드 배포 후
- DB 마이그레이션 후
- 재배포 전

---

## 🚀 사용 방법 (Windows)

### 1단계: 파일 준비

```bash
# 프로젝트 폴더로 이동
cd C:\Project_bulletin\Nvidia8Board

# 스크립트 복사
# migrate_to_cloudinary.py 파일을 프로젝트 폴더에 복사
```

### 2단계: 환경변수 설정

**방법 1: 명령 프롬프트 (CMD)**
```bash
set CLOUDINARY_CLOUD_NAME=your_cloud_name
set CLOUDINARY_API_KEY=your_api_key
set CLOUDINARY_API_SECRET=your_api_secret
set DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

**방법 2: PowerShell**
```powershell
$env:CLOUDINARY_CLOUD_NAME="your_cloud_name"
$env:CLOUDINARY_API_KEY="your_api_key"
$env:CLOUDINARY_API_SECRET="your_api_secret"
$env:DATABASE_URL="postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"
```

**Cloudinary 정보 확인:**
```
1. https://cloudinary.com 로그인
2. Dashboard 페이지에서 확인:
   - Cloud name: dxxxxx
   - API Key: 123456789012345
   - API Secret: abcdefghijklmnopqr
```

**DATABASE_URL 확인:**
```
Render: Environment 탭에서 DATABASE_URL 복사
또는
Supabase: Settings → Database → Connection String 복사
```

### 3단계: 스크립트 실행

```bash
python migrate_to_cloudinary.py
```

---

## 📺 실행 예시

```
============================================================
📦 Cloudinary 파일 마이그레이션 시작
============================================================
📝 마이그레이션할 게시글: 5개

[1/5] 20251209_113141_image.png... ✅ 업로드 완료
[2/5] project_file.pdf... ✅ 업로드 완료
[3/5] deleted_file.jpg... ❌ 파일 없음
[4/5] screenshot.png... ✅ 업로드 완료
[5/5] data.zip... ✅ 업로드 완료

============================================================
📊 마이그레이션 완료
============================================================
✅ 성공: 4개
❌ 실패: 0개
⏭️  스킵: 1개 (파일 없음)
📁 총합: 5개
============================================================

✨ 마이그레이션이 성공적으로 완료되었습니다!
이제 안전하게 재배포할 수 있습니다.
```

---

## ✅ 확인 방법

### 1. Cloudinary 확인
```
1. https://cloudinary.com 로그인
2. Media Library 클릭
3. nvidia8th_board 폴더 확인
   ├── free/
   │   └── 파일들...
   └── project/
       └── 파일들...
```

### 2. 데이터베이스 확인
```sql
-- PostgreSQL
SELECT id, title, filename, cloudinary_url 
FROM posts 
WHERE filename IS NOT NULL;

-- cloudinary_url이 채워져 있으면 성공!
```

### 3. 웹사이트 확인
```
게시글 접속 → 첨부파일 클릭
→ Cloudinary URL로 열리면 성공
(https://res.cloudinary.com/...)
```

---

## 🔧 트러블슈팅

### 에러 1: 환경변수 없음
```
❌ 에러: Cloudinary 환경변수가 설정되지 않았습니다.

해결:
환경변수 다시 설정 (대소문자 정확히!)
```

### 에러 2: uploads 폴더 없음
```
❌ uploads 폴더가 없습니다.

해결:
1. 프로젝트 폴더 확인
2. uploads 폴더 있는지 확인
3. 없으면 마이그레이션 불필요
```

### 에러 3: DB 연결 실패
```
❌ could not connect to server

해결:
DATABASE_URL 확인
- Render: Internal URL 사용
- 비밀번호 정확한지 확인
```

### 에러 4: Cloudinary 인증 실패
```
❌ Could not authenticate

해결:
Cloudinary 정보 다시 확인
- Cloud name
- API Key  
- API Secret
```

---

## 📊 전체 배포 체크리스트

### Phase 1: 준비 (5분)
- [ ] Cloudinary 가입
- [ ] Cloud name, API Key, API Secret 복사
- [ ] 수정된 코드 파일 5개 준비

### Phase 2: 코드 배포 (5분)
- [ ] 파일 교체 (app.py, board.html, view.html, edit.html, requirements.txt)
- [ ] Render 환경변수 추가 (CLOUDINARY_CLOUD_NAME, API_KEY, API_SECRET)
- [ ] Git push
- [ ] Render 재배포

### Phase 3: DB 마이그레이션 (5분)
```sql
ALTER TABLE posts ADD COLUMN cloudinary_url TEXT;
ALTER TABLE posts ADD COLUMN cloudinary_public_id TEXT;
ALTER TABLE comments ADD COLUMN parent_id INTEGER REFERENCES comments(id);
```

### Phase 4: 파일 마이그레이션 (5분) ← 여기!
- [ ] migrate_to_cloudinary.py 다운로드
- [ ] 환경변수 설정
- [ ] 스크립트 실행
- [ ] Cloudinary에서 파일 확인

### Phase 5: 최종 확인 (5분)
- [ ] 새 게시글 작성 → 파일 업로드 → 썸네일 확인
- [ ] 댓글 작성 → 답글 작성 확인
- [ ] 글 수정 → 파일 수정 확인
- [ ] 재배포 → 파일 유지 확인

---

## ⚡ 빠른 실행 (복사-붙여넣기)

### Windows CMD
```bash
cd C:\Project_bulletin\Nvidia8Board
set CLOUDINARY_CLOUD_NAME=your_cloud_name
set CLOUDINARY_API_KEY=your_api_key
set CLOUDINARY_API_SECRET=your_api_secret
set DATABASE_URL=your_database_url
python migrate_to_cloudinary.py
```

### Windows PowerShell
```powershell
cd C:\Project_bulletin\Nvidia8Board
$env:CLOUDINARY_CLOUD_NAME="your_cloud_name"
$env:CLOUDINARY_API_KEY="your_api_key"
$env:CLOUDINARY_API_SECRET="your_api_secret"
$env:DATABASE_URL="your_database_url"
python migrate_to_cloudinary.py
```

---

## 💡 팁

### 1. 테스트 실행
```python
# 스크립트 수정: 실제 업로드 안 하고 확인만
# migrate_to_cloudinary.py 에서

# 이 부분을 주석 처리:
# result = cloudinary.uploader.upload(...)

# 대신 이렇게:
print(f"테스트: {file_path} 업로드 예정")
```

### 2. 부분 마이그레이션
```sql
-- 특정 게시판만
SELECT id, filename 
FROM posts 
WHERE board_type = 'project' AND filename IS NOT NULL;
```

### 3. 재실행 안전
```
스크립트는 여러 번 실행해도 안전합니다.
이미 cloudinary_url이 있으면 덮어씁니다.
```

---

## 🎯 성공 기준

마이그레이션 성공 후:
- ✅ Cloudinary Media Library에 파일 보임
- ✅ posts 테이블에 cloudinary_url 채워짐
- ✅ 게시글에서 파일 다운로드 가능
- ✅ 썸네일 표시됨
- ✅ 재배포해도 파일 유지

---

## 📞 요약

**목적:** uploads 폴더 → Cloudinary 이전

**타이밍:** 코드 배포 후, 재배포 전

**실행:**
1. migrate_to_cloudinary.py 다운로드
2. 환경변수 4개 설정
3. python migrate_to_cloudinary.py
4. 확인

**소요 시간:** 5분

**결과:** 안전한 재배포 가능! 🎉
