#!flask/bin/python
from flask import Flask, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__, static_url_path="")
CORS(app)


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/devices', methods=['GET'])
def getDevices():
    pass


@app.route('/data', methods=['GET'])
def getData():
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6725, debug=False)
