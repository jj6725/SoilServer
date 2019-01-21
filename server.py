#!flask/bin/python
from flask import Flask, jsonify, make_response, abort
from sht31d import SHT31D
from soilsensor import SoilSensor

##########################################################################################
# Python Home Soil Server
##########################################################################################

app = Flask(__name__, static_url_path = "")

sht31d = None
soils = None

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

@app.route('/temp', methods = ['GET'])
def getTemp():
    temp = 0

    if sht31d is not None:
        temp = sht31d.getTemperature()
    elif soil is not None:
        temp = soil.getTemperature()
    else:
        abort(404)

    return jsonify( {'temperature': temp})

@app.route('/humidity', methods = ['GET'])
def getHumidity():
    if sht31d is not None:
        return jsonify( {'humidity': sht31d.getHumidity()} )
    else:
        return make_response(jsonify( { 'error': 'Not found' } ), 404)

@app.route('/moisture', methods = ['GET'])
def getMoisture():
    if soil is not None:
        return jsonify( {'humidity': soil.getMoisture()} )
    else:
        return make_response(jsonify( { 'error': 'Not found' } ), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6725, debug=False)
