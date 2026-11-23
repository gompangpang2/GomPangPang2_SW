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

웹은 5000번, 노드 TCP 수신은 9000번 포트로 함께 뜹니다. 같은 와이파이에 있는 기기에서 `http://<파이 IP>:5000` 으로 접속합니다. 파이 IP는 `hostname -I`로 확인합니다.

### 환경변수

| 이름 | 기본값 | 설명 |
| --- | --- | --- |
| `DB_HOST` | `localhost` | DB 주소 |
| `DB_PORT` | `3306` | DB 포트 |
| `DB_USER` | `gompang` | DB 계정 |
| `DB_PASSWORD` | (없음) | DB 비밀번호 |
| `DB_NAME` | `gompang` | DB 이름 |
| `PORT` | `5000` | 웹 포트 |
| `TCP_PORT` | `9000` | 노드가 접속할 TCP 포트 |
| `SECRET_KEY` | 실행마다 랜덤 | 로그인 세션 암호화 키. 고정하지 않으면 서버를 재시작할 때 로그인이 풀립니다. |

## 노드 ↔ 서버 프로토콜

노드는 서버의 9000번 포트에 TCP로 접속하고, 한 줄에 JSON 하나씩 보냅니다. 줄 끝은 `\n`입니다.

```
{"node": "closet1", "temp": 24.0, "hum": 62.0}
```

| 필드 | 형식 |
| --- | --- |
| `node` | 노드 이름. 영문, 숫자, `_`, `-`로 1~30자 |
| `temp` | 온도(°C). -40~80 |
| `hum` | 습도(%). 0~100 |

서버는 줄마다 한 줄로 답합니다.

| 응답 | 뜻 |
| --- | --- |
| `OK` | 저장됨 |
| `ERR json` | JSON 형식이 아님 |
| `ERR node` | 노드 이름이 틀림 |
| `ERR temp/hum` | 온도나 습도가 숫자가 아님 |
| `ERR range` | 값이 범위를 벗어남 |
| `ERR server` | DB 저장 실패 |

연결은 끊지 않고 계속 보내도 됩니다.

### 노드 예시 (DHT11)

`node/dht_node.py`를 센서가 달린 파이에서 실행합니다. 이 코드는 DHT11 데이터 핀이 GPIO4에 연결되어 있다고 가정합니다.

```bash
pip install adafruit-circuitpython-dht && sudo apt install -y libgpiod2
SERVER_HOST=<서버 파이 IP> NODE_NAME=closet1 python3 node/dht_node.py
```

## 테스트

MySQL 없이 돌아갑니다. `test_auth.py`는 회원가입부터 로그인, 로그아웃까지, `test_sensor.py`는 TCP 수신부터 저장, API까지 확인합니다.

```bash
python3 test_auth.py && python3 test_sensor.py
```
