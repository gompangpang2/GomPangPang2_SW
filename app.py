import os
import re
from datetime import timedelta
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import db

app = Flask(__name__)
# SECRET_KEY가 없으면 매 실행마다 새로 만들어져 재시작 시 로그인이 풀린다
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",  # 다른 사이트에서 보낸 POST에 쿠키가 안 붙게 (CSRF 완화)
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    return redirect(url_for("dashboard" if "user_id" in session else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db.find_user(username) if username else None
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session.permanent = bool(request.form.get("remember"))
            return redirect(url_for("dashboard"))
        # 아이디가 없는지 비밀번호가 틀렸는지 구분하지 않는다
        flash("아이디 또는 비밀번호가 맞지 않아요.", "error")
        return render_template("login.html", username=username), 401
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        error = None
        if not USERNAME_RE.match(username):
            error = "아이디는 영문, 숫자, _ 로 3~30자여야 해요."
        elif len(password) < 8:
            error = "비밀번호는 8자 이상이어야 해요."
        elif password != password2:
            error = "비밀번호가 서로 달라요."
        elif not db.create_user(username, generate_password_hash(password)):
            error = "이미 사용 중인 아이디예요."

        if error:
            flash(error, "error")
            return render_template("signup.html", username=username), 400
        flash("가입이 완료됐어요. 로그인해 주세요.", "ok")
        return redirect(url_for("login"))
    return render_template("signup.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session["username"])


@app.route("/api/latest")
@login_required
def api_latest():
    # shortcut: 5초 폴링. 실시간 푸시가 필요해지면 Flask-SocketIO로 교체
    try:
        rows = db.latest_measurements()
    except Exception:
        return jsonify(error="DB에 연결할 수 없어요."), 503
    return jsonify([
        {"node": r["node"], "temp": r["temperature"], "hum": r["humidity"],
         "at": r["measured_at"].strftime("%Y-%m-%d %H:%M:%S")}
        for r in rows
    ])


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    import threading

    import tcp_server

    # 노드 TCP 수신기를 같은 프로세스에서 함께 띄운다
    tcp = tcp_server.make_server()
    threading.Thread(target=tcp.serve_forever, daemon=True).start()
    print(f"[tcp] {tcp.server_address[1]}번 포트에서 노드 기다리는 중")
    app.run(host="0.0.0.0", port=5000)
