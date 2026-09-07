from time import sleep
import RPi.GPIO as GPIO
import threading

GPIO.setmode(GPIO.BOARD)


class TouchSensor:

    def update(self):
        while True:
            if GPIO.input(self.pin) == GPIO.LOW:
                self.result = True
                print("Touch wurde erkannt")
            else:
                self.result = False

            sleep(0.1)

    def __init__(self):
        self.pin = 11

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.result = False

        threading.Thread(target=self.update, daemon=True).start()

    def readTouch(self):
        return self.result
