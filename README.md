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

### 3. 서버 한 번에 켜기 (추천)

```bash
./start.sh
```

이 명령 하나로 DB 컨테이너(`my-db-server`), 웹 서버(5001번), DHT 센서 노드가 모두 켜집니다. tmux 안에서 실행되므로 SSH가 끊겨도 계속 동작합니다.

- 화면 보기: `tmux attach -t gompang` (빠져나오기: `Ctrl+B`를 누른 뒤 `D`)
- 끄기: `./start.sh stop`
- 센서 없이 웹만 켜기: `NODE=0 ./start.sh`
- 처음 한 번 설치: `sudo apt install -y tmux`

DB 비밀번호는 실행할 때 물어봅니다. 매번 입력하기 번거로우면 프로젝트 폴더에 `.env` 파일을 만들어 두면 됩니다. 이 파일은 `.gitignore`에 들어 있어 GitHub에 올라가지 않습니다.

```
DB_PASSWORD=실제비밀번호
SECRET_KEY=아무_긴_문자열
```

`.env`에는 `DB_USER`, `DB_NAME`, `PORT`, `DB_CONTAINER`, `VENV`, `NODE_NAME`도 넣을 수 있습니다. 기본값은 각각 `root`, `gompang`, `5001`, `my-db-server`, `../.venv`, `closet1`입니다.

### 3-1. 직접 실행하기

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
