import time
import board
import busio
import adafruit_sht31d

class SHT31D:
    count = 0
    def getTemperature(self):
        self.count += 1 
        temperature = 0
        try:
            temperature = self.sensor.temperature
        except:
            raise("Device error")
        else:
            return temperature

    def getHumidity(self):
        self.count += 1
        humidity = 0
        try:
            humidity = self.sensor.relative_humidity
        except:
            raise("Device error")
        else:
            return humidity

    def heat(self):
        if self.count > 10:
            self.sensor.heater = True
            time.sleep(1)
            self.sensor.heater = False
            self.count = 0
    
    def getStatus(self):
        status = 0 
        try:
            status = self.sensor.status
        except:
            raise("Device error")
        else:
            return status

    def __init__(self):
        count = 0 
        self.sensor = adafruit_sht31d.SHT31D(busio.I2C(board.SCL, board.SDA),address=0x44)

if __name__ == "__main__":
    sensor = SHT31D()
    print("Status: {0:b}".format(sensor.getStatus()))
    print("Temperature: {0:0.1f} C".format(sensor.getTemperature()))
    print("Humidity: {0:0.1f} %%".format(sensor.getHumidity()))
