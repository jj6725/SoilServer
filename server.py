#!flask/bin/python
from flask import Flask, jsonify, make_response, abort
from flask_cors import CORS
from sht31d import SHT31D
from soilsensor import SoilSensor

##########################################################################################
# Python Home Soil Server
##########################################################################################

app = Flask(__name__, static_url_path = "")
CORS(app)

sht31d = None
soil = None

try:
    sht31d = SHT31D()
except:
    print("SHT31D not present")
    pass

try:
    soil = SoilSensor()
except:
    print("Soil Sensor not present")
    pass

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify( { 'error': 'Bad request' } ), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

@app.route('/devices', methods = ['GET'])
def getDevices():
    sht31dStatus = "Offline"
    soilStatus = "Offline"

    try:
        sht31d.getStatus()
        sht31dStatus = "OK"
    except:
        sht31dStatus = "Offline"

    try:
        if soil is not None:
            soilStatus = "OK"
    except:
        soilStatus ="Offline"

    return jsonify({'sht31d': sht31dStatus, 'i2cSoil': soilStatus})

@app.route('/data', methods = ['GET'])
def getData():
    try:
        return jsonify({'temperature': sht31d.getTemperature(),'humidity': sht31d.getHumidity()})
    except:
        return offlineError()

@app.route('/temp', methods = ['GET'])
def getTemp():
    try:
        return jsonify( {'temperature': sht31d.getTemperature()} )
    except:
        return offlineError()

@app.route('/humidity', methods = ['GET'])
def getHumidity():
    try:
        return jsonify( {'humidity': sht31d.getHumidity()} )
    except:
        return offlineError()

@app.route('/moisture', methods = ['GET'])
def getMoisture():
    try:
        return jsonify( {'moisture': soil.getMoisture()} )
    except:
        return offlineError()

def offlineError():
    return make_response(jsonify( {'error': 'Devices are offline'} ), 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6725, debug=True)
