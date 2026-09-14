from time import sleep

import RPi.GPIO as GPIO
import threading

GPIO.setmode(GPIO.BOARD)


class LightSensor:

    def update(self):
        while True:
            self.result = GPIO.input(self.pin)

            sleep(0.1)

    def __init__(self):
        self.pin = 12
        GPIO.setup(self.pin, GPIO.IN)

        self.result = 0

        threading.Thread(target=self.update, daemon=True).start()

    def readLight(self):
        return self.result
