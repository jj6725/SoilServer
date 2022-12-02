import time
import board
import adafruit_shtc3


class SHTC3:
    name = "SHTC3"

    def get_temperature(self):
        return self.sensor.temperature

    def get_humidity(self):
        return self.sensor.relative_humidity

    def print(self):
        print("Temperature: {0:0.1f} C".format(self.get_temperature()))
        print("Humidity: {0:0.1f} %%".format(self.get_humidity()))

    def __init__(self):
        self.count = 0
        try:
            i2c = board.I2C()
            self.sensor = adafruit_shtc3.SHTC3(i2c)
        except:
            raise


if __name__ == "__main__":
    try:
        sensor = SHTC3()
    except:
        print(SHTC3.name, "Unavailable")
    else:
        print(SHTC3.name, "Initialized")
        while True:
            sensor.print()
            time.sleep(1)
