import time
from devices import BME280, SHT31D, LTR559, PM25, SGP40


class DeviceManager:

    def get_data(self):
        # update values only every 5 seconds
        # send last set data if request is within 5 seconds of previous request
        now = time.time_ns()
        if now - self.last_fetch < 5 * 1000 * 1000:
            return self.data

        data = {}
        if self.th_sensor is not None:
            data["temp"] = self.th_sensor.get_temperature()
            data["humidity"] = self.th_sensor.get_humidity()

        if self.pressure_sensor is not None:
            data["pressure"] = self.pressure_sensor.get_pressure()

        if self.light_sensor is not None:
            data["lux"] = self.light_sensor.get_lux()

        if self.gas_sensor is not None:
            temp = data["temp"]
            humidity = data["humidity"]
            if temp is not None and humidity is not None:
                data["voc_index"] = self.gas_sensor.get_voc_index(
                    temp=temp, humidity=humidity)
                data["gas"] = self.gas_sensor.get_compensated_gas(
                    temp=temp, humidity=humidity)

        if self.pm_sensor is not None:
            aqdata = self.pm_sensor.get_data()
            data["air_quality"] = {
                "pm03": aqdata["particles 03um"],
                "pm05": aqdata["particles 05um"],
                "pm10": aqdata["particles 10um"],
                "pm25": aqdata["particles 25um"],
                "pm50": aqdata["particles 50um"],
                "pm100": aqdata["particles 100um"]
            }

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
            try:
                sht31d = SHT31D()
                self.devices.append(SHT31D.name)
                self.th_sensor = sht31d
            except:
                pass
        # lux
        try:
            ltr559 = LTR559()
            self.light_sensor = ltr559
            self.devices.append(LTR559.name)
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
