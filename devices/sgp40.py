import time
import board
import adafruit_sgp40


class SGP40:
    name = "SGP40"

    def get_voc_index(temp, humidity, self):
        return self.sensor.measure_index(temperature=temp, relative_humidity=humidity)

    def get_compensated_gas(temp, humidity, self):
        return self.sensor.measure_raw(temperature=temp, relative_humidity=humidity)

    def get_raw_gas(self):
        return self.sensor.raw

    def print(self):
        print("Gas: %d" % (self.sensor.get_raw_gas()))

    def __init__(self):
        try:
            i2c = board.I2C()
            self.sensor = adafruit_sgp40.SGP40(i2c)
        except:
            raise


if __name__ == "__main__":
    try:
        sensor = SGP40()
    except:
        print(SGP40.name, " Unavailable")
    else:
        print(SGP40.name, " Initialized")
        while True:
            sensor.print()
            time.sleep(1)
