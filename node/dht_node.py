"""센서 노드 예시: DHT11을 읽어 서버로 보낸다 (라즈베리파이).

설치: pip install adafruit-circuitpython-dht   (+ sudo apt install libgpiod2)
실행: SERVER_HOST=192.168.0.10 NODE_NAME=closet1 python3 dht_node.py

프로토콜은 tcp_server.py 상단 참고: 한 줄에 JSON 하나 보내고 OK / ERR 응답을 받는다.
"""
import json
import os
import socket
import time

import adafruit_dht
import board

SERVER = (os.environ.get("SERVER_HOST", "127.0.0.1"), int(os.environ.get("SERVER_PORT", 9000)))
NODE = os.environ.get("NODE_NAME", "closet1")
INTERVAL = float(os.environ.get("INTERVAL", 5))
PIN = getattr(board, os.environ.get("DHT_PIN", "D4"))  # GPIO4

sensor = adafruit_dht.DHT11(PIN)


def read_dht():
    # DHT11은 읽기 실패가 잦아서 몇 번 다시 시도한다
    for _ in range(5):
        try:
            t, h = sensor.temperature, sensor.humidity
            if t is not None and h is not None:
                return t, h
        except RuntimeError:
            pass
        time.sleep(2)
    return None


def main():
    while True:
        try:
            with socket.create_connection(SERVER, timeout=10) as sock:
                f = sock.makefile("rwb")
                print(f"서버 연결됨: {SERVER}")
                while True:
                    reading = read_dht()
                    if reading:
                        t, h = reading
                        f.write((json.dumps({"node": NODE, "temp": t, "hum": h}) + "\n").encode())
                        f.flush()
                        reply = f.readline().decode().strip()
                        print(f"{t}°C {h}% -> {reply}")
                        if not reply:
                            raise ConnectionError("서버가 연결을 끊음")
                    time.sleep(INTERVAL)
        except (OSError, ConnectionError) as e:
            print(f"연결 실패: {e} - 5초 뒤 다시 연결")
            time.sleep(5)


if __name__ == "__main__":
    main()
