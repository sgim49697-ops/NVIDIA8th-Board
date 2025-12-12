# ⚡ SendGrid API + Slack 빠른 가이드 (20분)

## 🎯 목표
Render 호환 이메일 발송 (SMTP 포트 차단 해결)

---

## 📝 1단계: SendGrid 설정 (10분)

### A. 회원가입
1. https://signup.sendgrid.com/
2. 계정 생성 + 이메일 인증

### B. Sender 인증 (중요!)
1. Settings → Sender Authentication
2. **Verify a Single Sender**
3. 이메일 입력: your-email@gmail.com
4. 인증 이메일 확인

### C. API Key 생성
1. Settings → API Keys
2. Create API Key
3. Name: `Nvidia8Board`
4. **API Key 복사** (한 번만 보임!)
   ```
   SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## 🎨 2단계: Slack Webhook (5분)

1. https://api.slack.com/apps
2. Create New App → From scratch
3. Incoming Webhooks → ON
4. Add New Webhook
5. **Webhook URL 복사**

---

## 💻 3단계: 파일 교체 (2분)

```powershell
cd C:\Project_bulletin\Nvidia8Board

# 백업
copy app.py app.py.backup
copy requirements.txt requirements.txt.backup

# 교체
# app_sendgrid_slack.py → app.py
# requirements_sendgrid.txt → requirements.txt
```

---

## 🌐 4단계: Render 환경변수 (3분)

**추가/수정:**
```
SENDGRID_API_KEY = SG.xxxxxx...
SENDGRID_FROM_EMAIL = your-verified-email@gmail.com
SLACK_WEBHOOK_URL = https://hooks.slack.com/...
DATABASE_URL = postgres://... (Internal!)
```

**제거 (선택):**
```
MAIL_USERNAME ❌
MAIL_PASSWORD ❌
```

---

## 🚀 5단계: 배포 (2분)

```bash
git add app.py requirements.txt
git commit -m "SendGrid API - Render compatible"
git push origin main
```

---

## ✅ 6단계: 테스트

1. https://nvidia8th-board.onrender.com/register
2. **실제 이메일** 입력
3. 회원가입

**결과:**
- ✅ 502 에러 없음!
- ✅ Gmail 수신함에 예쁜 HTML 이메일
- ✅ Slack 알림
- ✅ 이메일 인증 → 로그인 성공

---

## 🎉 완료!

**Render Free Plan에서 이메일 발송 성공!**
- SendGrid API (HTTP) 사용
- SMTP 포트 차단 우회
- 완벽한 이메일 인증 시스템

**더 자세한 내용: SENDGRID_COMPLETE_GUIDE.md**
