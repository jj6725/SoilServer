import time
from ltr559 import LTR559


class LTR:
    name = "LTR559"

    def get_lux(self):
        self.sensor.update_sensor()
        return self.sensor.get_lux()

    def print(self):
        print("Lux: {0:0.1f}".format(self.get_lux()))

    def __init__(self) -> None:
        try:
            self.sensor = LTR559()
        except:
            raise


if __name__ == "__main__":
    try:
        sensor = LTR()
    except:
        print(LTR.name, "Unavailable")
    else:
        print(LTR.name, "Initialized")
        while True:
            sensor.print()
            time.sleep(1)
