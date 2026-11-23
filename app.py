from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
@app.route("/login")
def login():
    # shortcut: 화면만 렌더링, POST 처리는 2.1/2.2(로그인 DB 연결)에서 추가
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
