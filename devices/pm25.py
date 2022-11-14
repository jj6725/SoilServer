import time
import board
import busio
from adafruit_pm25.i2c import PM25_I2C


class PM25:
    name = "PM25"

    def get_data(self):
        return self.sensor.read()

    def print(self):
        aqdata = self.get_data()
        print()
        print("Concentration Units (standard)")
        print("---------------------------------------")
        print(
            "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
            % (aqdata["pm10 standard"], aqdata["pm25 standard"], aqdata["pm100 standard"])
        )
        print("Concentration Units (environmental)")
        print("---------------------------------------")
        print(
            "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
            % (aqdata["pm10 env"], aqdata["pm25 env"], aqdata["pm100 env"])
        )
        print("---------------------------------------")
        print("Particles > 0.3um / 0.1L air:", aqdata["particles 03um"])
        print("Particles > 0.5um / 0.1L air:", aqdata["particles 05um"])
        print("Particles > 1.0um / 0.1L air:", aqdata["particles 10um"])
        print("Particles > 2.5um / 0.1L air:", aqdata["particles 25um"])
        print("Particles > 5.0um / 0.1L air:", aqdata["particles 50um"])
        print("Particles > 10 um / 0.1L air:", aqdata["particles 100um"])
        print("---------------------------------------")

    def __init__(self):
        try:
            i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
            self.sensor = PM25_I2C(i2c)
        except:
            raise


if __name__ == "__main__":
    try:
        sensor = PM25()
    except:
        print(PM25.name, "Unavailable")
    else:
        print(PM25.name, "Initialized")
        while True:
            sensor.print()
            time.sleep(1)
