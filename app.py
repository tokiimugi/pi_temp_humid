from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO
import Adafruit_DHT
import time
import datetime
import threading
import requests
from config import API_KEY

API_URL = "http://api.weatherapi.com/v1/current.json"

current_city = "Vancouver"

app = Flask(__name__)
socketio = SocketIO(app)

sensor = Adafruit_DHT.DHT22
gpio_pin = 4

temperature = 0.0
humidity = 0.0
current_time = datetime.datetime.now()

sensor_thread_running = True
connected_clients = set()


def read_sensor():
    global temperature, humidity, current_time, sensor_thread_running
    while sensor_thread_running:
        # Read temperature and humidity data from the sensor
        new_humidity, new_temperature = Adafruit_DHT.read_retry(sensor, gpio_pin, delay_seconds=0.1)
        
        # Update the global variables only if the data retrieval was successful
        if new_humidity is not None and new_temperature is not None:
            temperature = new_temperature
            humidity = new_humidity
            current_time = datetime.datetime.now()
        
        # Wait for some time before taking the next reading (e.g., 2 seconds)
        time.sleep(2)

def get_weather_data(city):
    params = {
        "key" : API_KEY,
        "q" : city
    }
    try:
        # Send GET request to the API
        response = requests.get(API_URL, params=params)
        response.raise_for_status()  # Raise an exception for unsuccessful requests
        data = response.json()
        
        # Extract relevant weather information from the response
        temperature = data["current"]["temp_c"]
        humidity = data["current"]["humidity"]

        # Display the weather information
        return {"city_temp" :temperature,
                "city_humid" : humidity}

    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")


def background_task():
    while sensor_thread_running:
        if connected_clients:
            data = {'temperature':temperature, 'humidity': humidity, **get_weather_data(current_city)}
            socketio.emit('update_data', data, namespace='/data')
        socketio.sleep(2)

@socketio.on('connect', namespace='/data')
def handle_connect():
    connected_clients.add(request.sid)

@socketio.on('disconnect', namespace='/data')
def handle_disconnect():
    connected_clients.remove(request.sid)

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

    socketio.start_background_task(target=background_task)
    try:
        socketio.run(app,host='0.0.0.0', port=5000)
    finally:
        sensor_thread_running = False
        sensor_thread.join()