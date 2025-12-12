# ⚡ Slack Webhook 빠른 설치 가이드 (10분)

## 🎯 목표
Gmail SMTP (502 에러) → Slack Webhook (안정적) 전환

---

## 📝 1단계: Slack Webhook URL 생성 (5분)

1. **https://api.slack.com/apps** 접속
2. **Create New App** → **From scratch**
3. App Name: `Nvidia8Board`
4. **Incoming Webhooks** → ON
5. **Add New Webhook to Workspace**
6. 채널 선택 (예: `#회원가입-알림`)
7. **Webhook URL 복사**
   ```
   https://hooks.slack.com/services/T.../B.../XXX...
   ```

---

## 🔧 2단계: 파일 교체 (3분)

```powershell
cd C:\Project_bulletin\Nvidia8Board

# 백업
copy app.py app.py.backup
copy requirements.txt requirements.txt.backup

# 새 파일로 교체
# app_slack.py → app.py
# requirements_slack.txt → requirements.txt
```

---

## 🌐 3단계: Render 환경변수 (2분)

**Render → Environment → 추가:**
```
SLACK_WEBHOOK_URL = https://hooks.slack.com/services/...
```

**선택적 제거 (이메일 미사용 시):**
```
MAIL_USERNAME (제거 가능)
MAIL_PASSWORD (제거 가능)
```

---

## 🚀 4단계: 배포 (5분)

```bash
git add app.py requirements.txt
git commit -m "Replace Gmail with Slack - Fix 502"
git push origin main
```

**Render에서 자동 배포 시작!**

---

## ✅ 5단계: 테스트

1. **https://nvidia8th-board.onrender.com/register**
2. 회원가입 시도
3. **결과:**
   - ✅ 502 에러 없음
   - ✅ "회원가입 완료!" 메시지
   - ✅ Slack 알림 도착
   - ✅ 즉시 로그인 가능

---

## 🎉 완료!

**성공 시:**
- 502 에러 완전히 해결
- 사용자는 즉시 로그인 가능
- 관리자는 Slack으로 모니터링

**더 자세한 내용은 SLACK_COMPLETE_GUIDE.md 참고!**
