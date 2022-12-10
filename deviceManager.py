import time
from devices.bme280 import BME280
from devices.ltr import LTR
from devices.pm25 import PM25
from devices.sgp40 import SGP40
from devices.sht31d import SHT31D
from devices.shtc3 import SHTC3


class DeviceManager:

    def get_data(self):
        # update values only every 5 seconds
        # send last set data if request is within 5 seconds of previous request
        now = time.time_ns()
        if now - self.last_fetch < 5 * 1000 * 1000:
            return self.data

        data = {}
        if self.th_sensor is not None:
            try:
                data["temp"] = self.th_sensor.get_temperature()
                data["humidity"] = self.th_sensor.get_humidity()
            except:
                pass

        if self.pressure_sensor is not None:
            try:
                data["pressure"] = self.pressure_sensor.get_pressure()
            except:
                pass

        if self.light_sensor is not None:
            try:
                data["lux"] = self.light_sensor.get_lux()
            except:
                pass

        if self.gas_sensor is not None:
            try:
                temp = data["temp"]
                humidity = data["humidity"]
            except:
                pass
            else:
                try:
                    data["voc_index"] = self.gas_sensor.get_voc_index(
                        temperature=temp, humidity=humidity)
                    data["gas"] = self.gas_sensor.get_compensated_gas(
                        temperature=temp, humidity=humidity)
                except:
                    pass

        if self.pm_sensor is not None:
            try:
                aqdata = self.pm_sensor.get_data()
                data["air_quality"] = {
                    "pm03": aqdata["particles 03um"],
                    "pm05": aqdata["particles 05um"],
                    "pm10": aqdata["particles 10um"],
                    "pm25": aqdata["particles 25um"],
                    "pm50": aqdata["particles 50um"],
                    "pm100": aqdata["particles 100um"]
                }
            except:
                pass

        # don't update data or last fetch time if nothing was written
        if data == {}:
            return data

        self.last_fetch = time.time_ns()
        self.data = data
        return data

    def find_devices(self):
        self.devices = []
        # temp & humidity (need to find a better way to do this)
        try:
            bme280 = BME280()
            self.devices.append(BME280.name)
            self.th_sensor = bme280
            self.pressure_sensor = bme280
        except:
            pass

        try:
            sht31d = SHT31D()
            self.devices.append(SHT31D.name)
            self.th_sensor = sht31d
        except:
            pass

        try:
            shtc3 = SHTC3()
            self.devices.append(SHTC3.name)
            self.th_sensor = shtc3
        except:
            pass

        # lux
        try:
            ltr559 = LTR()
            self.light_sensor = ltr559
            self.devices.append(LTR.name)
        except:
            pass

        # VOC & Gas
        try:
            sgp40 = SGP40()
            self.gas_sensor = sgp40
            self.devices.append(SGP40.name)
        except:
            pass

        # Particulate Matter
        try:
            pm25 = PM25()
            self.pm_sensor = pm25
            self.devices.append(PM25.name)
        except:
            pass

    def __init__(self):
        self.data = {}
        self.last_fetch = 0
        self.th_sensor = None
        self.pressure_sensor = None
        self.light_sensor = None
        self.gas_sensor = None
        self.pm_sensor = None
        self.find_devices()


if __name__ == "__main__":
    manager = DeviceManager()
    print(manager.devices)
    count = 0
    while True:
        count += 1
        if (count > 30):
            count = 0
            manager.find_devices()
            print("Refinding devices")
            print(manager.devices)

        print(manager.get_data())
        time.sleep(1)
