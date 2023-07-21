from flask import Flask, jsonify
import Adafruit_DHT
import time
import datetime


app = Flask(__name__)

sensor = Adafruit_DHT.DHT22
gpio_pin = 4

temperature = 0.0
humidity = 0.0
current_time = datetime.datetime.now()

def read_sensor():
    global temperature, humidity, current_time
    while True:
        # Read temperature and humidity data from the sensor
        new_humidity, new_temperature = Adafruit_DHT.read_retry(sensor, gpio_pin)
        
        # Update the global variables only if the data retrieval was successful
        if new_humidity is not None and new_temperature is not None:
            temperature = new_temperature
            humidity = new_humidity
            current_time = datetime.datetime.now()

        # Wait for some time before taking the next reading (e.g., 2 seconds)
        time.sleep(2)

import threading
sensor_thread = threading.Thread(target=read_sensor)
sensor_thread.daemon = True
sensor_thread.start()

@app.route('/data')
def get_data():
    data = {
        'temperature': temperature,
        'humidity': humidity,
        'time' : current_time
    }
    return jsonify(data)

@app.route('/')
def index():
    return f'<h1>Temperature: {temperature:.2f} °C </h1><h1>Humidity: {humidity:.2f}%</h1>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)