#include <Arduino_LSM6DS3.h>
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <math.h>

const char* WIFI_SSID = "James Iphone";
const char* WIFI_PASS = "james123";

// your laptop IP on hotspot (from ipconfig)
const char* SERVER_IP = "172.20.10.2";
const int   SERVER_PORT = 8000;
const char* POST_PATH = "/api/data";

WiFiClient wifi;
HttpClient client(wifi, SERVER_IP, SERVER_PORT);

// ---- IMU movement code ----
float ax, ay, az, gx, gy, gz;

const float LIGHT_MOVE_G = 0.08;
const float HEAVY_MOVE_G = 0.25;
const float FREEFALL_G   = 0.30;
const unsigned long WINDOW_MS = 1000;

float baseline = 1.0;
unsigned long windowStart = 0;

int lightEvents = 0;
int heavyEvents = 0;
bool freeFallNow = false;
unsigned long freeFallStart = 0;

float dynSum = 0;
int samples = 0;

bool dropDetectedThisWindow = false;

void connectWiFi() {
  Serial.print("Connecting WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("Arduino IP: ");
  Serial.println(WiFi.localIP());
}

void postMovement(const char* state, float avgDyn, int lightCnt, int heavyCnt, bool drop) {
  // Build JSON
  String json = "{";
  json += "\"device_id\":\"movement_arduino\",";
  json += "\"movement_state\":\"" + String(state) + "\",";
  json += "\"avg_move_g\":" + String(avgDyn, 3) + ",";
  json += "\"light_events\":" + String(lightCnt) + ",";
  json += "\"heavy_events\":" + String(heavyCnt) + ",";
  json += "\"drop\":" + String(drop ? "true" : "false");
  json += "}";

  client.beginRequest();
  client.post(POST_PATH);
  client.sendHeader("Content-Type", "application/json");
  client.sendHeader("Content-Length", json.length());
  client.beginBody();
  client.print(json);
  client.endRequest();

  int statusCode = client.responseStatusCode();
  String resp = client.responseBody();

  Serial.print("POST status=");
  Serial.print(statusCode);
  Serial.print(" body=");
  Serial.println(resp);
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  if (!IMU.begin()) {
    Serial.println("IMU init failed");
    while (true) {}
  }

  connectWiFi();

  windowStart = millis();
  Serial.println("Sleep movement tracker running...");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (IMU.accelerationAvailable()) IMU.readAcceleration(ax, ay, az);
  if (IMU.gyroscopeAvailable())    IMU.readGyroscope(gx, gy, gz);

  float amag = sqrt(ax*ax + ay*ay + az*az);

  baseline = 0.98 * baseline + 0.02 * amag;

  float dyn = fabs(amag - baseline);
  dynSum += dyn;
  samples++;

  if (dyn > HEAVY_MOVE_G) heavyEvents++;
  else if (dyn > LIGHT_MOVE_G) lightEvents++;

  unsigned long now = millis();
  if (amag < FREEFALL_G) {
    if (!freeFallNow) {
      freeFallNow = true;
      freeFallStart = now;
    }
  } else {
    if (freeFallNow && (now - freeFallStart) > 150) {
      dropDetectedThisWindow = true;
      Serial.println("DROP detected (free-fall)!");
    }
    freeFallNow = false;
  }

  if (now - windowStart >= WINDOW_MS) {
    float avgDyn = (samples > 0) ? (dynSum / samples) : 0.0;

    const char* state = "STILL";
    if (avgDyn > HEAVY_MOVE_G) state = "HEAVY";
    else if (avgDyn > LIGHT_MOVE_G) state = "LIGHT";

    Serial.print("state=");
    Serial.print(state);
    Serial.print(" avgMove(g)=");
    Serial.print(avgDyn, 3);
    Serial.print(" lightCounts=");
    Serial.print(lightEvents);
    Serial.print(" heavyCounts=");
    Serial.print(heavyEvents);
    Serial.print(" drop=");
    Serial.println(dropDetectedThisWindow ? "true" : "false");

    // Send to Django
    postMovement(state, avgDyn, lightEvents, heavyEvents, dropDetectedThisWindow);

    // reset window stats
    windowStart = now;
    dynSum = 0;
    samples = 0;
    lightEvents = 0;
    heavyEvents = 0;
    dropDetectedThisWindow = false;
  }

  delay(20);
}
