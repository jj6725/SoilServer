import time
import board
import adafruit_scd4x


class SCD41:
    name = "SCD41"

    def get_temperature(self):
        return self.sensor.temperature
    
    def get_humidity(self):
        return self.sensor.relative_humidity

    def get_co2(self):
        return self.sensor.CO2

    def print(self):
        print("CO2: %d" % (self.get_co2()))
        print("Temperature: %0.1f *C" % self.get_temperature())
        print("Humidity: %0.1f %%" % self.get_humidity())

    def __init__(self):
        try:
            i2c = board.I2C()
            self.sensor = adafruit_scd4x.SCD4X(i2c)
        except:
            raise


if __name__ == "__main__":
    try:
        sensor = SCD41()
    except:
        print(SCD41.name, "Unavailable")
    else:
        print(SCD41.name, "Initialized")
        while True:
            if sensor.data_ready:
              sensor.print()
            time.sleep(1)
