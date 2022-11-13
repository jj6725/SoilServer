import time
from ltr559 import LTR559


class LTR559:
    def get_lux(self):
        return self.sensor.get_lux()

    def print(self):
        print("Lux: {0:0.1f}".format(self.sensor.get_lux()))

    def __init__(self) -> None:
        self.sensor = LTR559()


if __name__ == "__main__":
    sensor = LTR559()
    while True:
        sensor.print()
        time.sleep(1)
