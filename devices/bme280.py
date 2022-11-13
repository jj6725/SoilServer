import time
import board
from adafruit_bme280 import basic as adafruit_bme280


class BME280:
    def get_temperature(self):
        return self.sensor.temperature

    def get_humidity(self):
        return self.sensor.relative_humidity

    def get_pressure(self):
        return self.sensor.pressure

    def get_altitude(self):
        return self.sensor.altitude

    def print(self):
        print()
        print("Temperature: %0.1f C" % self.sensor.get_temperature())
        print("Humidity: %0.1f %%" % self.sensor.get_humidity())
        print("Pressure: %0.1f hPa" % self.sensor.get_pressure())
        print("Altitude = %0.2f meters" % self.sensor.get_altitude())

    def __init__(self):
        try:
            i2c = board.I2C()  # uses board.SCL and board.SDA
            self.sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c)
            self.sensor.sea_level_pressure = 1013.25
        except (RuntimeError):
            raise


if __name__ == "__main__":
    sensor = BME280()

    while True:
        sensor.print()
        time.sleep(2)
