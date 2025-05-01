#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// --- Configuration ---
const char* ssid = "your_network_name";
const char* password = "your_network_password";

const char* serverIP = "server_IP";
const int serverPort = 5000; //flask default port
const char* serverPath = "/data";


#define DHTPIN 4
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);


unsigned long lastSendTime = 0;
const long sendInterval = 5000; // Send data every 5 seconds

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nESP32 DHT11 Data Sender");

  dht.begin();
  Serial.println("DHT11 sensor initialized.");

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(1000);
  
  Serial.print("Connecting to ");
  Serial.println(ssid);0
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(2000);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Sending data to server: http://");
    Serial.print(serverIP);
    Serial.print(":");
    Serial.print(serverPort);
    Serial.println(serverPath);
  } else {
    Serial.println("\nFailed to connect to WiFi. Check credentials/network. Restarting...");
    delay(5000);
    ESP.restart();
  }
}

void loop() {
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();

    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();

    // Check if reads failed
    if (isnan(humidity) || isnan(temperature)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    Serial.printf("Readings: Temp=%.1f C, Hum=%.1f %%\n", temperature, humidity);

    
    if (WiFi.status() == WL_CONNECTED) { // Send data to server if WiFi is connected
      sendDataToServer(temperature, humidity);
    }
    else {
      Serial.println("WiFi Disconnected. Cannot send data.");
    }
  }

}

void sendDataToServer(float temp, float hum) {
  HTTPClient http;
  WiFiClient client;

  String serverUrl = "http://";
  serverUrl += serverIP;
  serverUrl += ":";
  serverUrl += serverPort;
  serverUrl += serverPath;

  Serial.print("Sending POST request to: ");
  Serial.println(serverUrl);

  // Prepare JSON payload using ArduinoJson
  StaticJsonDocument<200> jsonDoc; // Adjust size as needed
  jsonDoc["temperature"] = temp;
  jsonDoc["humidity"] = hum;
  // jsonDoc["deviceId"] = "ESP32_LivingRoom"; // Optionally add device ID

  String jsonPayload;
  serializeJson(jsonDoc, jsonPayload);

  // Start HTTP POST request
  if (http.begin(client, serverUrl)) { // Use client instance
      http.addHeader("Content-Type", "application/json");

      // Send the request with the payload
      int httpResponseCode = http.POST(jsonPayload);

      // Check the response
      if (httpResponseCode > 0) {
          Serial.printf("HTTP Response code: %d\n", httpResponseCode);
          // String responsePayload = http.getString(); // Get response payload from server (if any)
          // Serial.println("Response payload: " + responsePayload);
          if (httpResponseCode != 200) {
             Serial.println("Warning: Server returned non-OK status.");
          }
      }
      else {
          Serial.printf("HTTP POST failed, error: %s\n", http.errorToString(httpResponseCode).c_str());
      }

      http.end();// Disconnect
  }
  else {
      Serial.println("HTTP Client failed to connect.");
  }
}
