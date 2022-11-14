import time
import board
from pimoroni_circuitpython_ltr559 import Pimoroni_LTR559


class LTR559:
    name = "LTR559"

    def get_lux(self):
        return self.sensor.get_lux()

    def print(self):
        print("Lux: {0:0.1f}".format(self.sensor.get_lux()))

    def __init__(self) -> None:
        try:
            i2c = board.I2C()
            self.sensor = Pimoroni_LTR559(i2c)
        except:
            raise


if __name__ == "__main__":
    try:
        sensor = LTR559()
    except:
        print("%s Unavailable", LTR559.name)
    else:
        print("%s Initialized", LTR559.name)
        while True:
            sensor.print()
            time.sleep(1)
