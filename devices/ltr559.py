import time
import board
from ltr559 import LTR559


class LTR559:
    name = "LTR559"

    def get_lux(self):
        return self.sensor.get_lux()

    def print(self):
        print("Lux: {0:0.1f}".format(self.get_lux()))

    def __init__(self) -> None:
        try:
            i2c = board.I2C()
            self.sensor = ltr559(i2c)
        except:
            raise


if __name__ == "__main__":
    try:
        sensor = LTR559()
    except:
        print(LTR559.name, "Unavailable")
    else:
        print(LTR559.name, "Initialized")
        while True:
            sensor.print()
            time.sleep(1)
