import time
import board
import busio
import adafruit_sht31d

class SHT31D:
    count = 0
    def getTemperature(self):
        self.count += 1 
        return self.sensor.temperature

    def getHumidity(self):
        self.count += 1
        return self.sensor.relative_humidity

    def heat(self):
        if self.count > 10:
            self.sensor.heater = True
            time.sleep(1)
            self.sensor.heater = False
            self.count = 0

    def __init__(self):
        count = 0 
        self.sensor = adafruit_sht31d.SHT31D(busio.I2C(board.SCL, board.SDA),address=0x44)

if __name__ == "__main__":
    sensor = SHT31D()
    print("\nTemperature: %0.1f C" % sensor.getTemperature())
    print("Humidity: %0.1f %%" % sensor.getHumidity())    
