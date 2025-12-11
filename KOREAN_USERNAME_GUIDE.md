# 한국어 아이디 허용 - app.py 수정 가이드

## 📝 수정 사항

app.py의 register 함수에서 username 유효성 검사를 추가/수정합니다.

---

## 🔧 app.py 수정

### register 함수 찾기:

```python
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
```

### 다음 코드를 추가:

```python
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # 아이디 유효성 검사 (한글, 영문, 숫자, 밑줄 허용)
        import re
        if not re.match(r'^[가-힣a-zA-Z0-9_]{3,50}$', username):
            flash('아이디는 한글, 영문, 숫자, 밑줄(_)만 사용 가능합니다 (3-50자)', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 8:
            flash('비밀번호는 8자 이상이어야 합니다.', 'error')
            return redirect(url_for('register'))
        
        # ... 나머지 코드
```

---

## 📋 전체 수정된 register 함수:

```python
import re  # 파일 맨 위에 추가

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # 아이디 유효성 검사 (한글, 영문, 숫자, 밑줄 허용)
        if not re.match(r'^[가-힣a-zA-Z0-9_]{3,50}$', username):
            flash('아이디는 한글, 영문, 숫자, 밑줄(_)만 사용 가능합니다 (3-50자)', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 8:
            flash('비밀번호는 8자 이상이어야 합니다.', 'error')
            return redirect(url_for('register'))
        
        password_hash = generate_password_hash(password)
        token = serializer.dumps(email, salt='email-confirm')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password, verification_token)
                VALUES (%s, %s, %s, %s)
            ''', (username, email, password_hash, token))
            
            conn.commit()
            
            # 인증 이메일 발송
            confirm_url = url_for('confirm_email', token=token, _external=True)
            msg = Message('NVIDIA 8th 게시판 - 이메일 인증', recipients=[email])
            msg.body = f'''
안녕하세요 {username}님,

NVIDIA 8th 게시판 가입을 환영합니다!

아래 링크를 클릭하여 이메일을 인증해주세요:
{confirm_url}

※ 이 링크는 1시간 동안 유효합니다.

감사합니다.
'''
            mail.send(msg)
            
            flash('인증 이메일이 발송되었습니다. 이메일을 확인해주세요.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 회원가입 오류: {type(e).__name__}: {str(e)}")
            
            # 오류 메시지 개선
            error_msg = str(e)
            if 'users_username_key' in error_msg:
                flash('이미 사용 중인 아이디입니다.', 'error')
            elif 'users_email_key' in error_msg:
                flash('이미 사용 중인 이메일입니다.', 'error')
            else:
                flash(f'회원가입 실패: {error_msg}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('register.html')
```

---

## ✅ 적용 방법

### 1. app.py 수정
```python
# 파일 맨 위에 import 추가
import re

# register 함수에 유효성 검사 추가 (위 코드 참고)
```

### 2. register.html 교체
```bash
copy register_korean.html templates\register.html
```

### 3. Flask 서버 재시작
```bash
python app.py
```

### 4. 테스트
```
http://localhost:5000/register

아이디: 김슬기
이메일: test@gmail.com
비밀번호: 12345678
```

---

## 🎯 허용되는 아이디 예시

✅ **허용됨:**
- `김슬기` (한글)
- `ksg6346` (영문+숫자)
- `슬기Kim` (한글+영문)
- `user_123` (영문+숫자+밑줄)
- `홍길동_2024` (한글+영문+숫자+밑줄)

❌ **허용 안됨:**
- `김 슬기` (공백)
- `kim@naver` (특수문자 @)
- `김!` (특수문자 !)
- `ab` (3자 미만)
- `very_long_username_that_exceeds_fifty_characters_limit` (50자 초과)

---

## 🔍 데이터베이스 확인

PostgreSQL에서 한글 저장 확인:

```sql
-- username 컬럼 확인
\d users

-- 한글 아이디 조회
SELECT * FROM users WHERE username LIKE '%김%';

-- 모든 사용자 조회
SELECT id, username, email FROM users;
```

---

## 💡 주의사항

### PostgreSQL 인코딩 확인

PostgreSQL이 UTF-8 인코딩인지 확인:

```sql
SHOW SERVER_ENCODING;
-- UTF8이어야 함
```

만약 다른 인코딩이면:

```sql
-- 새 데이터베이스 생성 시
CREATE DATABASE flask_board WITH ENCODING 'UTF8';
```

---

## 📊 변경 전후 비교

### 변경 전
```javascript
// 영문, 숫자, 밑줄만
const regex = /^[a-zA-Z0-9_]{3,50}$/;
```

### 변경 후
```javascript
// 한글, 영문, 숫자, 밑줄 허용
const regex = /^[가-힣a-zA-Z0-9_]{3,50}$/;
```

---

## 🚀 완료!

이제 한글 아이디로 회원가입이 가능합니다! 🎉

- ✅ 프론트엔드 유효성 검사 (JavaScript)
- ✅ 백엔드 유효성 검사 (Python)
- ✅ 데이터베이스 저장 (UTF-8)
