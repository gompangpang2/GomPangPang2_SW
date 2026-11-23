import os

import pymysql


def connect():
    # 접속 정보는 환경변수로 받는다 (비밀번호를 코드에 넣지 않기 위해)
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "gompang"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "gompang"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def find_user(username):
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
        return cur.fetchone()


def create_user(username, password_hash):
    """새 사용자 저장. 아이디가 이미 있으면 False."""
    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash),
            )
        return True
    except pymysql.err.IntegrityError:
        return False
