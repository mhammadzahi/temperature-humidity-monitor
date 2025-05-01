from flask import Flask, request, jsonify, render_template_string
import datetime

app = Flask(__name__)

# Simple in-memory storage for the latest data
latest_data = {
    "temperature": None,
    "humidity": None,
    "timestamp": None,
    "error": None
}

# HTML Template for displaying data
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Sensor Data</title>
    <meta http-equiv="refresh" content="10"> <!-- Auto refresh page every 10 seconds -->
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f4f4f4; }
        .data-container { background-color: #fff; padding: 30px; display: inline-block; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        p { font-size: 1.2em; color: #555; }
        span { font-weight: bold; color: #007bff; }
        .timestamp { font-size: 0.8em; color: #888; margin-top: 20px; }
        .error { color: red; font-style: italic; }
    </style>
</head>
<body>
    <div class="data-container">
        <h1>Live Sensor Readings</h1>
        {% if data['error'] %}
            <p class="error">Error receiving data: {{ data['error'] }}</p>
        {% elif data['temperature'] is not none and data['humidity'] is not none %}
            <p>Temperature: <span>{{ "%.1f"|format(data['temperature']) }} °C</span></p>
            <p>Humidity: <span>{{ "%.1f"|format(data['humidity']) }} %</span></p>
            <p class="timestamp">Last updated: {{ data['timestamp'] }}</p>
        {% else %}
            <p>Waiting for data from ESP32...</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, data=latest_data.copy())

@app.route('/data', methods=['POST'])
def receive_data():
    """ Endpoint to receive data from the ESP32. """
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
        latest_data['error'] = str(e) # Store error message
        # Respond with error status
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5011, debug=False)

