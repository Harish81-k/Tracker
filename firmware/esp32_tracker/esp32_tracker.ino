#include <Arduino.h>
#include <WiFi.h> // Mocking LTE with WiFi for the stub
#include <HTTPClient.h>

// Configuration
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
const char* backendUrl = "https://your-backend.com/api/v1/devices/1/upload_telemetry/";
const char* deviceToken = "Bearer YOUR_JWT_TOKEN";

// Deep Sleep settings
#define uS_TO_S_FACTOR 1000000ULL
#define TIME_TO_SLEEP  300        // Sleep for 5 minutes

RTC_DATA_ATTR int bootCount = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  ++bootCount;
  Serial.println("Boot number: " + String(bootCount));

  // Connect to Network
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to network.");

  // Get GPS Data (Stubbed)
  float lat = 37.7749 + (random(-100, 100) / 10000.0);
  float lng = -122.4194 + (random(-100, 100) / 10000.0);
  
  // Get Battery Data (Stubbed)
  int batteryLevel = 85;

  // Send Telemetry
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(backendUrl);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", deviceToken);

    String payload = "{\"location\": {\"latitude\": " + String(lat, 6) + 
                     ", \"longitude\": " + String(lng, 6) + 
                     ", \"timestamp\": \"2024-05-18T12:00:00Z\"}, " +
                     "\"battery\": {\"level\": " + String(batteryLevel) + "}}";

    int httpResponseCode = http.POST(payload);
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    
    http.end();
  }

  // Go back to Deep Sleep
  Serial.println("Going to sleep now");
  esp_sleep_enable_timer_wakeup(TIME_TO_SLEEP * uS_TO_S_FACTOR);
  Serial.flush(); 
  esp_deep_sleep_start();
}

void loop() {
  // This is not going to be called because the ESP goes to sleep in setup()
}
