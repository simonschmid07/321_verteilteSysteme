from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep
from air_sensor import AirSensor
from light_sensor import LightSensor
from distance_sensor import DistanceSensor
from touch_sensor import TouchSensor
import threading
import mimetypes
import textwrap
import json
import os

import paho.mqtt.client as mqtt

air_sensor = AirSensor()
light_sensor = LightSensor()
distance_sensor = DistanceSensor()
touch_sensor = TouchSensor(11)

host = "0.0.0.0"
port = 8080

touch_counter = 0


def on_connect(client, userdata, flags, reason_code, properites):
    print(f"Connected to MQTT Broker with result {reason_code}")
    mqtt_client.subscribe("mondaymorning/touch_counter", qos=2)


def on_message(client, userdata, msg: object):
    print(msg.topic + " " + str(msg.payload))
    if msg.topic == "mondaymorning/touch_counter":
        global touch_counter
        touch_counter = int(msg.payload)
        print("got touch_counter state:", touch_counter)


mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("172.17.0.1", 1883, 60)

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

    def serveStatic(self):
        local_file_path = os.path.join(".", self.path[1:], "index.html")
        print(local_file_path)

        if os.path.exists(local_file_path) and os.path.isfile(local_file_path):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Vary", "Origin")

            mime_type, _ = mimetypes.guess_type(local_file_path)
            if mime_type:
                self.send_header("Content-type", mime_type)
            else:
                self.send_header("Content-type", "application/octet-stream")

            self.end_headers()

            with open(local_file_path, "rb") as file:
                self.wfile.write(file.read())

    def do_GET(self):
        if self.path == "/":
            self.serveStatic()

        if self.path == "/metrics":
            air = air_sensor.readAir()
            light = light_sensor.readLight()
            response = textwrap.dedent(f"""
                # HELP sensor_light measured light itensity in lux\n\
                # TYPE sensor_light gauge\n\
                sensor_light {light}\n\
                # HELP sensor_air_temperature measured temperature in celcius\n\
                # TYPE sensor_air_temperature gauge\n\
                sensor_air_temperature {air.temperature}\n\
                # HELP sensor_air_humidity measured humidity in percent\n\
                # TYPE sensor_air_humidity gauge\n\
                sensor_air_humidity {air.humidity}
            """)

            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Vary", "Origin")
            self.send_header("Content-type", "text/plain")
            self.end_headers()

            self.wfile.write(response.encode())

        if self.path == "/api/air":
            air = air_sensor.readAir()
            self.sendJSON(
                {
                    "status": "ok",
                    "data": [
                        {
                            "label": "Temperature",
                            "value": air.temperature,
                            "unit": "°C",
                        },
                        {"label": "Humidity", "value": air.humidity, "unit": "%"},
                    ],
                }
            )

        if self.path == "/api/light":
            self.sendJSON(
                {
                    "status": "ok",
                    "data": {
                        "label": "Illuminance",
                        "value": light_sensor.readLight(),
                        "unit": "lux",
                    },
                }
            )

        if self.path == "/api/touch-counter":
            global touch_counter
            self.sendJSON(
                {
                    "status": "ok",
                    "data": {
                        "touch_counter": touch_counter,
                    },
                }
            )


def read_distance_sensor(delay):
    while True:
        distance = distance_sensor.read()
        mqtt_client.publish("mondaymorning/sensors/distance", distance, qos=2)
        sleep(delay)


def handle_touch(is_touched):
    if is_touched:
        print("touched")
        mqtt_client.publish("mondaymorning/sensors/touch", "touched", qos=2)

        global touch_counter
        touch_counter += 1
        mqtt_client.publish(
            "mondaymorning/touch_counter", touch_counter, qos=2, retain=True
        )


def main():
    web_server = HTTPServer((host, port), Server)
    print(f"Server started and listen to {host}:{port}")

    distanceSensorThread = threading.Thread(
        target=read_distance_sensor, args=(0.3,), daemon=True
    )

    distanceSensorThread.start()

    touch_sensor.start(handle_touch)

    try:
        mqtt_client.loop_start()
        mqtt_client.publish("mondaymorning/up", "true", qos=2)
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

print("Server stopped")
