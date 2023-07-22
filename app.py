from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO, async_mode
import Adafruit_DHT
import time
import datetime
import threading


app = Flask(__name__)
socketio = SocketIO(app, async_mode=async_mode)


sensor = Adafruit_DHT.DHT22
gpio_pin = 4

temperature = 0.0
humidity = 0.0
current_time = datetime.datetime.now()

sensor_thread_running = True

def read_sensor():
    global temperature, humidity, current_time, sensor_thread_running
    while sensor_thread_running:
        # Read temperature and humidity data from the sensor
        new_humidity, new_temperature = Adafruit_DHT.read_retry(sensor, gpio_pin)
        
        # Update the global variables only if the data retrieval was successful
        if new_humidity is not None and new_temperature is not None:
            temperature = new_temperature
            humidity = new_humidity
            current_time = datetime.datetime.now()
        data = {
        'temperature': temperature,
        'humidity': humidity
        }
        socketio.emit('update_data', data, namespace='/data')
        # Wait for some time before taking the next reading (e.g., 2 seconds)
        time.sleep(2)



@app.route('/api/data')
def get_data():
    data = {
        'temperature': temperature,
        'humidity': humidity,
        'time' : current_time
    }
    return jsonify(data)

@app.route('/')
def index():
    return render_template('index.html', temperature=temperature, humidity=humidity)


if __name__ == '__main__':
    sensor_thread = threading.Thread(target=read_sensor)
    sensor_thread.start()

    try:
        socketio.run(app,host='0.0.0.0', port=5000)
    finally:
        sensor_thread_running = False
        sensor_thread.join()