import time
import board
import busio
import adafruit_sht31d


class SHT31D:
    count = 0

    def get_temperature(self):
        self.count += 1
        return self.sensor.temperature

    def get_humidity(self):
        self.count += 1
        return self.sensor.relative_humidity

    def get_status(self):
        return self.sensor.status

    # The sensor needs to heat itself to reduce humidity bias in reading the surrounding temperature
    # Count helps approximates this process
    def heat(self):
        if self.count > 10:
            self.sensor.heater = True
            time.sleep(1)
            self.sensor.heater = False
            self.count = 0

    def print(self):
        print("Status: {0:b}".format(sensor.get_status()))
        print("Temperature: {0:0.1f} C".format(sensor.get_temperature()))
        print("Humidity: {0:0.1f} %%".format(sensor.get_humidity()))

    def __init__(self):
        self.count = 0
        self.sensor = adafruit_sht31d.SHT31D(
            busio.I2C(board.SCL, board.SDA), address=0x44)


if __name__ == "__main__":
    sensor = SHT31D()
    while True:
        sensor.print()
        time.sleep(1)
