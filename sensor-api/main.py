from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep

from air_sensor import AirSensor
from touch_sensor import TouchSensor

import json

air_sensor = AirSensor()
touch_sensor = TouchSensor()

host = "0.0.0.0"
port = 8080

sleep(1)


class Server(BaseHTTPRequestHandler):
    def sendJSON(self, object: object, code: int = 200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Vary", "Origin")
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(object).encode())

    def do_GET(self):
        if self.path == "/":
            air = air_sensor.readAir()
            touch = touch_sensor.readTouch()
            self.sendJSON({"status": "ok", "air": air.__dict__, "touch": touch})


def main():
    web_server = HTTPServer((host, port), Server)
    print(f"Server started and listen to {host}:{port}")

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

print("Server stopped")
