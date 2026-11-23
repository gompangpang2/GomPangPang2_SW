"""TCP 수신 → 저장 → /api/latest 흐름 확인. DB는 메모리 가짜.
실행: python3 test_sensor.py
"""
import socket
import threading
from datetime import datetime

import app as appmod
import tcp_server

rows = []


def fake_save(node, temperature, humidity):
    rows.append({"node": node, "temperature": temperature, "humidity": humidity, "measured_at": datetime(2026, 11, 23, 12, 0, 0)})


def fake_latest():
    last = {}
    for r in rows:
        last[r["node"]] = r
    return [last[k] for k in sorted(last)]


tcp_server.db.save_measurement = fake_save
appmod.db.latest_measurements = fake_latest

# parse_line
assert tcp_server.parse_line('{"node":"closet1","temp":24,"hum":62}') == ("closet1", 24.0, 62.0)
for bad, why in [("hello", "json"), ("[1]", "json"), ('{"temp":1,"hum":1}', "node"),
                 ('{"node":"a b","temp":1,"hum":1}', "node"), ('{"node":"a","temp":"x","hum":1}', "temp/hum"),
                 ('{"node":"a","temp":20,"hum":150}', "range"), ('{"node":"a","temp":NaN,"hum":50}', "range")]:
    try:
        tcp_server.parse_line(bad)
        raise AssertionError(f"통과하면 안 됨: {bad}")
    except ValueError as e:
        assert str(e) == why, (bad, e)

# 진짜 TCP 서버에 붙어서 보내기
srv = tcp_server.make_server(port=0)
threading.Thread(target=srv.serve_forever, daemon=True).start()
with socket.create_connection(srv.server_address) as s:
    f = s.makefile("rwb")
    for line in [b'{"node":"closet1","temp":24.5,"hum":61}\n', b'oops\n', b'{"node":"shoe","temp":20,"hum":70}\n',
                 b'{"node":"closet1","temp":25,"hum":63}\n']:
        f.write(line); f.flush()
    replies = [f.readline().strip() for _ in range(4)]
assert replies == [b"OK", b"ERR json", b"OK", b"OK"], replies
srv.shutdown()
assert len(rows) == 3

# API: 로그인 전엔 막힘, 로그인 후 노드별 최신값
c = appmod.app.test_client()
assert c.get("/api/latest").status_code == 302
with c.session_transaction() as sess:
    sess["user_id"], sess["username"] = 1, "mold"
data = c.get("/api/latest").get_json()
assert data == [
    {"node": "closet1", "temp": 25.0, "hum": 63.0, "at": "2026-11-23 12:00:00"},
    {"node": "shoe", "temp": 20.0, "hum": 70.0, "at": "2026-11-23 12:00:00"},
], data

# DB 장애면 503
def boom():
    raise RuntimeError("db down")
appmod.db.latest_measurements = boom
assert c.get("/api/latest").status_code == 503

print("all sensor tests passed")
