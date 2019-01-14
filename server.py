#!flask/bin/python
from flask import Flask, jsonify, make_response
from sensor import SoilSensor

##########################################################################################
# Python Home Bulb Server
##########################################################################################

app = Flask(__name__, static_url_path = "")
sensor = SoilSensor()

@app.errorhandler(400)
def bad_request(error):
	return make_response(jsonify( { 'error': 'Bad request' } ), 400)

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify( { 'error': 'Not found' } ), 404)

@app.route('/temp', methods = ['GET'])
def getTemp():
	return jsonify( {'temperature': sensor.getTemp()} )

@app.route('/moisture', methods = ['GET'])
def getMoisture():
	return jsonify( {'moisture': sensor.getMoisture()} )

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=6725, debug=True)