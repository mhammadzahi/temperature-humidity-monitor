from flask import Flask, request, jsonify, render_template_string
import datetime
from database import Database

app = Flask(__name__)
db = Database('config.yaml')



# Simple in-memory storage for the latest data
latest_data = {
    "temperature": None,
    "humidity": None,
    "timestamp": None,
    "error": None
}

HTML_TEMPLATE = """ """

API_KEY = "6vQr78Y07JHKGmGiBG24NF8nZaZDkPBpeGcQAi8AvzyY"

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, data=latest_data.copy())



@app.route('/data', methods=['POST'])
def receive_data():
    submitted_key = request.headers.get('X-API-Key')
    print(f"Submitted key: {submitted_key}")
    if submitted_key != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    global latest_data
    try:
        data = request.get_json()
        if not data or 'temperature' not in data or 'humidity' not in data:
            raise ValueError("Missing 'temperature' or 'humidity' in JSON payload")

        temp = data['temperature']
        hum = data['humidity']

        # Basic validation (optional)
        if not isinstance(temp, (int, float)) or not isinstance(hum, (int, float)):
             raise ValueError("Temperature and humidity must be numbers")

        # Update latest data
        latest_data['temperature'] = float(temp)
        latest_data['humidity'] = float(hum)
        latest_data['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        latest_data['error'] = None # Clear previous error on success

        print(f"Received data: Temp={temp:.1f} C, Hum={hum:.1f} % at {latest_data['timestamp']}")

        # Respond to ESP32 to acknowledge receipt
        return jsonify({"status": "success", "message": "Data received"}), 200

    except Exception as e:
        print(f"Error processing request: {e}")
        latest_data['error'] = str(e)
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == '__main__':
    if db.connect():
        if db.create_tables():
            db.disconnect()
            app.run(host='0.0.0.0', port=5011, debug=True)

