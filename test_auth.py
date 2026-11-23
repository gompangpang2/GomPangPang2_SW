"""회원가입 → 로그인 → 로그아웃 흐름 확인. DB는 메모리 가짜로 바꿔서 MySQL 없이 돈다.
실행: python3 test_auth.py
"""
import app as appmod

users = {}


def fake_find(username):
    return users.get(username)


def fake_create(username, password_hash):
    if username in users:
        return False
    users[username] = {"id": len(users) + 1, "username": username, "password_hash": password_hash}
    return True


appmod.db.find_user = fake_find
appmod.db.create_user = fake_create
c = appmod.app.test_client()


def post(url, **data):
    return c.post(url, data=data)


# 로그인 안 하면 대시보드 막힘
assert c.get("/dashboard").headers["Location"].endswith("/login")

# 회원가입 검증
assert "영문" in post("/signup", username="a", password="12345678", password2="12345678").get_data(as_text=True)
assert "8자" in post("/signup", username="mold", password="123", password2="123").get_data(as_text=True)
assert "서로 달라요" in post("/signup", username="mold", password="12345678", password2="12345679").get_data(as_text=True)

r = post("/signup", username="mold", password="12345678", password2="12345678")
assert r.status_code == 302 and r.headers["Location"].endswith("/login")
assert users["mold"]["password_hash"] != "12345678"  # 평문 저장 안 함
assert "이미 사용 중" in post("/signup", username="mold", password="abcdefgh", password2="abcdefgh").get_data(as_text=True)

# 로그인 실패
r = post("/login", username="mold", password="wrongpass")
assert r.status_code == 401 and "맞지 않아요" in r.get_data(as_text=True)
assert post("/login", username="nobody", password="12345678").status_code == 401

# 로그인 성공 → 대시보드
r = post("/login", username="mold", password="12345678")
assert r.headers["Location"].endswith("/dashboard")
assert "mold님" in c.get("/dashboard").get_data(as_text=True)

# 로그아웃
post("/logout")
assert c.get("/dashboard").status_code == 302

# DB 장애: 500 대신 안내 문구와 함께 원래 화면으로
import pymysql
def down(*a):
    raise pymysql.err.OperationalError(2003, "Can't connect")
appmod.db.create_user = down
appmod.db.find_user = down
r = post("/signup", username="newbie", password="12345678", password2="12345678")
assert r.status_code == 302 and r.headers["Location"].endswith("/signup")
assert "DB에 연결할 수 없어요" in c.get("/signup").get_data(as_text=True)
assert post("/login", username="mold", password="12345678").status_code == 302

print("all auth tests passed")
