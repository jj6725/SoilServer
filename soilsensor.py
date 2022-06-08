import board
import busio
import smbus

from adafruit_seesaw.seesaw import Seesaw

class SoilSensor:
    def getTemperature(self):
        return self.ss.get_temp()

    def getMoisture(self):
        return self.ss.moisture_read()

    def __init__(self, bus, address):
        self.address = hex(address)
        self.ss = Seesaw(bus, addr=address)

class BusManager:
    def getTemperature(self):
        temperatureValues = {}
        for device in self.devices:
            temperatureValues[device.address] = device.getTemperature()
        return temperatureValues

    def getMoisture(self):
        moistureValues = {}
        for device in self.devices:
            moistureValues[device.address] = device.getMoisture()
        return moistureValues

    def __init__(self, busNumber):
        # connect to i2c bus
        deviceAddresses = []
        i2cbus = smbus.SMBus(busNumber)
        for address in range(54,58):
            try:
                i2cbus.read_byte(address)
                deviceAddresses.append(address)
            finally:
                continue

        if busNumber == 3:
            self.busAlias = "B"
            self.bus = busio.I2C(board.D5, board.D6)
        else:
            self.busAlias = "A"
            self.bus = board.I2C()

        self.devices = []
        for device in deviceAddresses:
            self.devices.append(SoilSensor(self.bus, device))

class SensorManager:
    def getMoisture(self):
        moistureValues = {}
        for bus in self.i2cbusses:
            moistureValues[bus.busAlias] = bus.getMoisture()
        return moistureValues

    def getTemperature(self):
        temperatureValues = {}
        for bus in self.i2cbusses:
            temperatureValues[bus.busAlias] = bus.getTemperature()
        return temperatureValues

    def __init__(self):
        self.i2cbusses = [BusManager(1), BusManager(3)]

if __name__ == "__main__":
    manager = SensorManager()
    print("\n == Moisture == \n" + str(manager.getMoisture()))
    print("\n == Temperature == \n" + str(manager.getTemperature()))
