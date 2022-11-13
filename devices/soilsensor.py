import board
import busio
import smbus
import time

from adafruit_seesaw.seesaw import Seesaw

# class for fetching a single sensor value from the seesaw moisture sensor
# A single sensor can have a customizeable i2c address between 54 and 58
# (depending on what is soldered between the jumpers on the device)


class SoilSensor:
    def get_temperature(self):
        return self.ss.get_temp()

    def get_moisture(self):
        return self.ss.moisture_read()

    def __init__(self, bus, address):
        self.address = hex(address)
        self.ss = Seesaw(bus, addr=address)

# A single bus manager will return all soil sensor values on a i2c line
# If you have 5 or more sensors, you'll need to define at least two different i2c busses to read all sensor values
# This is why there's an A and B bus here.


class BusManager:
    def get_temperature(self):
        temperatureValues = {}
        for device in self.devices:
            temperatureValues[device.address] = device.get_temperature()
        return temperatureValues

    def get_moisture(self):
        moistureValues = {}
        for device in self.devices:
            moistureValues[device.address] = device.get_moisture()
        return moistureValues

    def __init__(self, busNumber):
        # connect to i2c bus
        deviceAddresses = []
        i2cbus = smbus.SMBus(busNumber)
        for address in range(54, 58):
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


# The overall sensor manager instantiates both busses to support up to 8 soil sensors.
# More could be added by creating more i2c lines as defined in the BusManager
class SensorManager:
    def get_temperature(self):
        temperatureValues = {}
        for bus in self.i2cbusses:
            temperatureValues[bus.busAlias] = bus.get_temperature()
        return temperatureValues

    def get_moisture(self):
        moistureValues = {}
        for bus in self.i2cbusses:
            moistureValues[bus.busAlias] = bus.get_moisture()
        return moistureValues

    def print(self):
        print("\n == Moisture == \n" + str(manager.get_moisture()))
        print("\n == Temperature == \n" + str(manager.get_temperature()))

    def __init__(self):
        self.i2cbusses = [BusManager(1), BusManager(3)]


if __name__ == "__main__":
    manager = SensorManager()
    while True:
        manager.print()
        time.sleep(1)
