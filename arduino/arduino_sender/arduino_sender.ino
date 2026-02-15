#include <Arduino_LSM6DS3.h>
#include <SimpleDHT.h>

#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <math.h>

// -------------------- WIFI --------------------
const char* WIFI_SSID = "James Iphone";
const char* WIFI_PASS = "james123";

// PUT YOUR LAPTOP IP HERE (from ipconfig on hotspot)
const char* SERVER_IP = "172.20.10.3";
const int   SERVER_PORT = 8000;
const char* POST_PATH = "/api/data";

WiFiClient wifi;
HttpClient client(wifi, SERVER_IP, SERVER_PORT);

// -------------------- DHT22 --------------------
const int pinDHT22 = 5;
SimpleDHT22 dht22(pinDHT22);

float temperatureC = NAN;
float temperatureF = NAN;
float humidity = NAN;

unsigned long prevDhtMillis = 0;
const unsigned long DHT_INTERVAL_MS = 1000;

// Abnormal thresholds
const float TEMP_HIGH_C = 26.0;
const float TEMP_LOW_C  = 18.0;
const float HUM_HIGH    = 70.0;
const float HUM_LOW     = 30.0;

// -------------------- IMU --------------------
float ax, ay, az, gx, gy, gz;

const float LIGHT_MOVE_G = 0.08;
const float HEAVY_MOVE_G = 0.25;
const float FREEFALL_G   = 0.30;

const unsigned long WINDOW_MS = 1000;

float baseline = 1.0;
unsigned long windowStart = 0;

int lightEvents = 0;
int heavyEvents = 0;

float dynSum = 0;
int samples = 0;

// drop detection
bool freeFallNow = false;
unsigned long freeFallStart = 0;
bool dropDetectedThisWindow = false;

// -------------------- FACE-DOWN (AZ BASED) --------------------
// Board is "facing up" when pins touch the table.
// That means az is ~ +1g when safe, ~ -1g when flipped face-down.
const float FACE_DOWN_AZ_THRESH = -0.75;     // tune: -0.6 to -0.85
const unsigned long FACE_DOWN_HOLD_MS = 2000; // 2s hold for quick alert

bool faceDownNow = false;
unsigned long faceDownStart = 0;
bool faceDownDetectedThisWindow = false;

// -------------------- WIFI HELPERS --------------------
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

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

String boolToJson(bool b) { return b ? "true" : "false"; }

// -------------------- POST TO DJANGO --------------------
void postToServer(const char* moveState, float avgDyn, int lightCnt, int heavyCnt,
                  bool drop, bool faceDown,
                  float tc, float tf, float hum, const char* envStatus) {

  String json = "{";
  json += "\"device_id\":\"movement_arduino\",";

  json += "\"movement_state\":\"" + String(moveState) + "\",";
  json += "\"avg_move_g\":" + String(avgDyn, 3) + ",";
  json += "\"light_events\":" + String(lightCnt) + ",";
  json += "\"heavy_events\":" + String(heavyCnt) + ",";
  json += "\"drop\":" + boolToJson(drop) + ",";
  json += "\"face_down\":" + boolToJson(faceDown) + ",";

  if (!isnan(tc)) json += "\"temp_c\":" + String(tc, 2) + ",";
  if (!isnan(tf)) json += "\"temp_f\":" + String(tf, 2) + ",";
  if (!isnan(hum)) json += "\"humidity\":" + String(hum, 2) + ",";
  json += "\"env_status\":\"" + String(envStatus) + "\"";
  json += "}";

  client.beginRequest();
  client.post(POST_PATH);
  client.sendHeader("Content-Type", "application/json");
  client.sendHeader("Connection", "close");            // helps avoid stalls
  client.sendHeader("Content-Length", json.length());
  client.beginBody();
  client.print(json);
  client.endRequest();

  int statusCode = client.responseStatusCode();
  client.skipResponseHeaders(); // do NOT read body (faster)

  Serial.print("POST status=");
  Serial.println(statusCode);
}

// -------------------- SETUP --------------------
void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  if (!IMU.begin()) {
    Serial.println("IMU init failed");
    while (true) {}
  }

  connectWiFi();

  windowStart = millis();
  Serial.println("Movement + Temp/Humidity tracker running...");
}

// -------------------- LOOP --------------------
void loop() {
  connectWiFi();

  unsigned long now = millis();

  // ---- Read DHT every 1s ----
  if (now - prevDhtMillis >= DHT_INTERVAL_MS) {
    prevDhtMillis = now;

    int err = dht22.read2(&temperatureC, &humidity, NULL);
    if (err != SimpleDHTErrSuccess) {
      Serial.print("DHT22 read failed, err=");
      Serial.println(err);
      temperatureC = NAN;
      temperatureF = NAN;
      humidity = NAN;
    } else {
      temperatureF = temperatureC * 1.8 + 32.0;
    }
  }

  // ---- Read IMU ----
  if (IMU.accelerationAvailable()) IMU.readAcceleration(ax, ay, az);
  if (IMU.gyroscopeAvailable())    IMU.readGyroscope(gx, gy, gz);

  float amag = sqrt(ax*ax + ay*ay + az*az);

  baseline = 0.98 * baseline + 0.02 * amag;
  float dyn = fabs(amag - baseline);
  dynSum += dyn;
  samples++;

  if (dyn > HEAVY_MOVE_G) heavyEvents++;
  else if (dyn > LIGHT_MOVE_G) lightEvents++;

  // ---- Drop detection ----
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

  // ---- Face-down detection (AZ sign + HOLD) ----
  // safe/up: az ~ +1.0, face-down: az ~ -1.0
  bool faceDownInstant = (az < FACE_DOWN_AZ_THRESH);

  if (faceDownInstant) {
    if (!faceDownNow) {
      faceDownNow = true;
      faceDownStart = now;
    } else if (now - faceDownStart >= FACE_DOWN_HOLD_MS) {
      faceDownDetectedThisWindow = true;
      Serial.println("ALERT: FACE-DOWN detected!");
      faceDownStart = now; // cooldown so it doesn't spam every loop
    }
  } else {
    faceDownNow = false;
  }

  // ---- Report once per WINDOW_MS ----
  if (now - windowStart >= WINDOW_MS) {
    float avgDyn = (samples > 0) ? (dynSum / samples) : 0.0;

    const char* state = "STILL";
    if (avgDyn > HEAVY_MOVE_G) state = "HEAVY";
    else if (avgDyn > LIGHT_MOVE_G) state = "LIGHT";

    // Environment status
    const char* envStatus = "OK";
    if (!isnan(temperatureC) && (temperatureC > TEMP_HIGH_C || temperatureC < TEMP_LOW_C)) envStatus = "ALERT";
    if (!isnan(humidity) && (humidity > HUM_HIGH || humidity < HUM_LOW)) envStatus = "ALERT";

    Serial.print("state=");
    Serial.print(state);
    Serial.print(" avgMove=");
    Serial.print(avgDyn, 3);
    Serial.print(" light=");
    Serial.print(lightEvents);
    Serial.print(" heavy=");
    Serial.print(heavyEvents);
    Serial.print(" drop=");
    Serial.print(dropDetectedThisWindow ? "true" : "false");
    Serial.print(" faceDown=");
    Serial.println(faceDownDetectedThisWindow ? "true" : "false");

    // POST to Django
    postToServer(
      state, avgDyn, lightEvents, heavyEvents,
      dropDetectedThisWindow, faceDownDetectedThisWindow,
      temperatureC, temperatureF, humidity, envStatus
    );

    // reset window stats
    windowStart = now;
    dynSum = 0;
    samples = 0;
    lightEvents = 0;
    heavyEvents = 0;
    dropDetectedThisWindow = false;
    faceDownDetectedThisWindow = false;
  }

  delay(20);
}
