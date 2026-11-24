#!/usr/bin/env bash
# 서버 한 번에 켜기:  ./start.sh        끄기: ./start.sh stop
# DB 컨테이너 → 웹 서버(app.py) → 센서 노드(dht_node.py)를 tmux 안에서 켠다 (SSH가 끊겨도 계속 동작)
set -e
cd "$(dirname "$0")"
SESSION=gompang

if [ "$1" = stop ]; then
  tmux kill-session -t "$SESSION" 2>/dev/null && echo "꺼졌어요." || echo "켜져 있지 않아요."
  exit 0
fi

command -v tmux >/dev/null || { echo "tmux가 없어요. 먼저: sudo apt install -y tmux"; exit 1; }
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "이미 켜져 있어요.  화면 보기: tmux attach -t $SESSION   끄기: ./start.sh stop"
  exit 0
fi

# 설정: .env 파일이 있으면 읽고(비밀번호 등), 없으면 기본값
[ -f .env ] && { set -a; . ./.env; set +a; }
DB_HOST=${DB_HOST:-127.0.0.1}
DB_PORT=${DB_PORT:-3306}
DB_USER=${DB_USER:-root}
DB_NAME=${DB_NAME:-gompang}
PORT=${PORT:-5001}
DB_CONTAINER=${DB_CONTAINER:-my-db-server}
VENV=${VENV:-../.venv}
NODE_NAME=${NODE_NAME:-closet1}
SECRET_KEY=${SECRET_KEY:-$(python3 -c 'import secrets;print(secrets.token_hex(32))')}
if [ -z "$DB_PASSWORD" ]; then
  read -r -s -p "DB 비밀번호: " DB_PASSWORD; echo
fi

sudo docker start "$DB_CONTAINER" >/dev/null
sleep 3  # MySQL이 접속을 받을 준비가 될 때까지

# tmux 서버가 이미 떠 있으면 현재 환경변수를 물려받지 않으므로 -e로 직접 넘긴다
ENVS=(-e DB_HOST="$DB_HOST" -e DB_PORT="$DB_PORT" -e DB_USER="$DB_USER" -e DB_NAME="$DB_NAME"
      -e DB_PASSWORD="$DB_PASSWORD" -e PORT="$PORT" -e SECRET_KEY="$SECRET_KEY")
tmux new-session -d -s "$SESSION" -n web "${ENVS[@]}" \
  "source $VENV/bin/activate && python3 app.py; echo; echo '서버가 멈췄어요. Enter를 누르면 창이 닫혀요.'; read"
if [ "${NODE:-1}" = 1 ]; then
  tmux new-window -t "$SESSION" -n node \
    "source $VENV/bin/activate && sleep 3 && SERVER_HOST=127.0.0.1 NODE_NAME=$NODE_NAME python3 node/dht_node.py; echo; echo '노드가 멈췄어요. Enter를 누르면 창이 닫혀요.'; read"
fi

echo "켜졌어요 → http://$(hostname -I 2>/dev/null | awk '{print $1}'):$PORT"
echo "화면 보기: tmux attach -t $SESSION  (빠져나오기: Ctrl+B 누르고 D)   끄기: ./start.sh stop"
