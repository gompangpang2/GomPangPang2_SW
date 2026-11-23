# GomPangPang2_SW

곰팡이 방지 시스템 웹 서버입니다. Flask와 MySQL(라즈베리파이에서는 MariaDB)을 씁니다.

## 라즈베리파이에서 실행하기

### 1. 코드와 패키지

```bash
git clone https://github.com/gompangpang2/GomPangPang2_SW.git
cd GomPangPang2_SW
sudo apt install -y mariadb-server python3-flask python3-pymysql
```

### 2. DB 만들기

먼저 테이블을 만듭니다.

```bash
sudo mysql < schema.sql
```

그다음 앱이 쓸 DB 계정을 만듭니다. 비밀번호는 원하는 값으로 바꾸세요.

```bash
sudo mysql -e "CREATE USER IF NOT EXISTS 'gompang'@'localhost' IDENTIFIED BY '비밀번호'; GRANT ALL ON gompang.* TO 'gompang'@'localhost';"
```

### 3. 서버 실행

```bash
export DB_PASSWORD='비밀번호'
export SECRET_KEY="$(python3 -c 'import secrets;print(secrets.token_hex(32))')"
python3 app.py
```

같은 와이파이에 있는 기기에서 `http://<파이 IP>:5000` 으로 접속합니다. 파이 IP는 `hostname -I`로 확인합니다.

### 환경변수

| 이름 | 기본값 | 설명 |
| --- | --- | --- |
| `DB_HOST` | `localhost` | DB 주소 |
| `DB_PORT` | `3306` | DB 포트 |
| `DB_USER` | `gompang` | DB 계정 |
| `DB_PASSWORD` | (없음) | DB 비밀번호 |
| `DB_NAME` | `gompang` | DB 이름 |
| `SECRET_KEY` | 실행마다 랜덤 | 로그인 세션 암호화 키. 고정하지 않으면 서버를 재시작할 때 로그인이 풀립니다. |

## 테스트

MySQL 없이 회원가입부터 로그인, 로그아웃까지의 흐름을 확인합니다.

```bash
python3 test_auth.py
```
