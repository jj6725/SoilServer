import busio

from board import SCL, SDA
from adafruit_seesaw.seesaw import Seesaw


class SoilSensor:
    def getTemp(self):
        return self.ss.get_temp()

    def getMoisture(self):
        return self.ss.moisture_read()

    def __init__(self):
        self.ss = Seesaw(busio.I2C(SCL, SDA), addr=0x36)

if __name__ == "__main__":
    sensor = SoilSensor()
    print("temp: " + str(sensor.getTemp()) + "  moisture: " + str(sensor.getMoisture()))