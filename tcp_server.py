"""노드 → 서버 TCP 수신기.

프로토콜: 한 줄(\n)에 JSON 하나
  보냄: {"node": "closet1", "temp": 24.0, "hum": 62.0}
  응답: OK            저장됨
        ERR <이유>    형식이 틀려 버림
연결은 계속 유지하고 여러 줄을 보내도 된다. 노드마다 스레드 하나.
"""
import json
import os
import re
import socketserver

import db

NODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,30}$")


def parse_line(line):
    """한 줄을 (node, temp, hum)으로. 틀리면 ValueError."""
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        raise ValueError("json")
    if not isinstance(msg, dict):
        raise ValueError("json")

    node = msg.get("node")
    if not isinstance(node, str) or not NODE_RE.match(node):
        raise ValueError("node")

    try:
        temp, hum = float(msg["temp"]), float(msg["hum"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("temp/hum")
    # DHT11 측정 범위 밖이면 센서 오류로 보고 버린다 (NaN도 여기서 걸림)
    if not (-40 <= temp <= 80) or not (0 <= hum <= 100):
        raise ValueError("range")
    return node, temp, hum


class NodeHandler(socketserver.StreamRequestHandler):
    def handle(self):
        peer = self.client_address[0]
        print(f"[tcp] 연결: {peer}")
        for raw in self.rfile:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                node, temp, hum = parse_line(line)
                db.save_measurement(node, temp, hum)
                self.wfile.write(b"OK\n")
            except ValueError as e:
                self.wfile.write(f"ERR {e}\n".encode())
            except Exception as e:  # DB 장애 등: 노드에 알리고 연결은 유지
                print(f"[tcp] 저장 실패: {e}")
                self.wfile.write(b"ERR server\n")
        print(f"[tcp] 연결 끊김: {peer}")


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(port=None):
    return Server(("0.0.0.0", port if port is not None else int(os.environ.get("TCP_PORT", 9000))), NodeHandler)


if __name__ == "__main__":
    with make_server() as srv:
        print(f"[tcp] {srv.server_address[1]}번 포트에서 노드 기다리는 중")
        srv.serve_forever()
