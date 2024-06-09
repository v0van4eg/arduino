from flask import Flask, request, jsonify, render_template
import os
import psycopg2
import pandas as pd
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Получение переменных окружения для подключения к базе данных PostgreSQL
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', '10.8.217.1')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'arduino')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'arduino')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'arduinopassword')

# Подключение к PostgreSQL
conn = psycopg2.connect(
    host=POSTGRES_HOST,
    database=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD
)
cur = conn.cursor()

# Создание таблицы, если она еще не существует
cur.execute("""
    CREATE TABLE IF NOT EXISTS pogoda (
        id SERIAL PRIMARY KEY,
        soil_moisture FLOAT,
        temperature FLOAT,
        humidity FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

# Счетчик для общего количества принятых сообщений
messages_received_total = Counter('messages_received_total', 'Total number of messages received')

# Измерение последних значений датчика
soil_moisture_gauge = Gauge('soil_moisture', 'Soil moisture value')
temperature_gauge = Gauge('temperature', 'Temperature value')
humidity_gauge = Gauge('humidity', 'Humidity value')

@app.route('/pogoda', methods=['POST'])
def receive_sensor_data():
    print('Приём сообщения')
    data = request.get_json()
    sm = data['soil_moisture']
    soil_moisture = (sm / 850)*100
    temperature = data['temperature']
    humidity = data['humidity']

    # Сохранение данных в базу данных
    cur.execute("INSERT INTO pogoda (soil_moisture, temperature, humidity) VALUES (%s, %s, %s)", (soil_moisture, temperature, humidity))
    conn.commit()
    print('Данные сохранены в БД')

    # Обновление метрик Prometheus
    messages_received_total.inc()
    soil_moisture_gauge.set(soil_moisture)
    temperature_gauge.set(temperature)
    humidity_gauge.set(humidity)

    return 'Data received and stored in the database', 200


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_data')
def get_data():
    # Получение данных из базы данных
    cur.execute("SELECT * FROM pogoda ORDER BY created_at DESC")
    data = cur.fetchall()

    # Преобразование данных в формат JSON
    df = pd.DataFrame(data, columns=['id', 'soil_moisture', 'temperature', 'humidity', 'created_at'])
    data_json = df.to_json(orient='records')

    return data_json


@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


app.add_url_rule('/metrics', 'metrics', metrics)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
