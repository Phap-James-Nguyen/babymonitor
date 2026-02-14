#include <WiFi.h>
#include <HTTPClient.h>
#include <math.h>
#include <string.h>


const char* WIFI_SSID = "James Iphone";
const char* WIFI_PASS = "james123";

// PUT YOUR LAPTOP IPv4 HERE (from ipconfig)
const char* SERVER_URL = "http://172.20.10.2:8000/api/data";

unsigned long lastPost = 0;
double t = 0.0;

void setup() {
  Serial.begin(115200);
  delay(300);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void postData(float wave, float bpm, const char* status) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  String payload = "{";
  payload += "\"wave\":" + String(wave, 1) + ",";
  payload += "\"bpm\":" + String(bpm, 1) + ",";
  payload += "\"status\":\"" + String(status) + "\"";
  payload += "}";

  int code = http.POST(payload);
  Serial.print("POST code=");
  Serial.print(code);
  Serial.print(" payload=");
  Serial.println(payload);

  http.end();
}

void loop() {
  // Send every 200ms (5 Hz)
  if (millis() - lastPost >= 200) {
    lastPost = millis();

    // Fake breathing wave around 520 with amplitude 80
    float wave = 520.0f + 80.0f * sin(t);

    // Fake BPM around 18
    float bpm = 18.0f + 2.0f * sin(t / 6.0);

    // Every ~20 seconds, simulate "no breathing" for 10 seconds (ALERT)
    int cycle = (millis() / 1000) % 30; // 0..29
    const char* status = (cycle >= 20 && cycle < 30) ? "ALERT" : "OK";

    // If alert, flatten the wave + bpm 0 (looks realistic)
    if (strcmp(status, "ALERT") == 0) {
      wave = 520.0f;
      bpm = 0.0f;
    }

    postData(wave, bpm, status);

    t += 0.25; // controls wave speed
  }
}
