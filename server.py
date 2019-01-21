#!flask/bin/python
from flask import Flask, jsonify, make_response, abort
from sht31d import SHT31D
from soilsensor import SoilSensor

##########################################################################################
# Python Home Bulb Server
##########################################################################################

app = Flask(__name__, static_url_path = "")

sht31d = Object()
soils = Object()

try:
    sht31d = SHT31D()
except:
    print("SHT31D not present")
    pass
else:
    sht31d = None

try:
    soil = SoilSensor()
except:
    print("Soil Sensor not present")
    pass
else:
    soil = None

@app.errorhandler(400)
def bad_request(error):
	abort(400)

@app.errorhandler(404)
def not_found(error):
    abort(404)

@app.route('/temp', methods = ['GET'])
def getTemp():
    temp = 0

    if sht31d is not None:
        temp = sht31d.getTemperature()
    else if soil is not None:
        temp = soil.getTemperature()
    else:
        abort(404)

    return jsonify( {'temperature': temp})

@app.route('/humidity', methods = ['GET'])
def getHumidity():
    if sht31d is not None:
        return jsonify( {'humidity': sht31d.getHumidity()} )
    else:
        abort(404)

@app.route('/moisture', methods = ['GET'])
def getMoisture():
    if soil is not None:
        return jsonify( {'humidity': soil.getMoisture()} )
    else:
        abort(404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6725, debug=False)
