from flask import Flask, request, jsonify, render_template
import datetime
from database import Database
import os
from dotenv import load_dotenv

from asgiref.wsgi import WsgiToAsgi
import uvicorn

load_dotenv() # Load environment variables from .env file

app = Flask(__name__)
db = Database('config.yaml')


latest_data = {
    "temperature": None,
    "humidity": None,
    "timestamp": None,
    "error": None
}


API_KEY = os.environ.get('API_KEY')

if not API_KEY:
    print("Warning: API_KEY environment variable not set!")
    # Depending on requirements, you might want to exit or raise an error here.
    # For now, we'll just print a warning and continue, which might lead to auth errors later.

@app.route('/')
def index():
    return render_template('index.html', data=latest_data.copy())



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


#asgi_app = WsgiToAsgi(app)  # Convert Flask WSGI to ASGI

if __name__ == '__main__':
    #if db.connect():
    #    if db.create_tables():
    #        db.disconnect()
    app.run(host='0.0.0.0', port=5011, debug=True)# dev
            #uvicorn.run(asgi_app, host="0.0.0.0", port=50011)# prod
