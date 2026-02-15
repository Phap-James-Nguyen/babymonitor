import machine
import time
import array
import network
import urequests
import gc

# --- CONFIGURATION ---
SSID = "James Iphone"
PASSWORD = "james123"

# Django server (your laptop IP running Django)
SERVER_IP = "172.20.10.3"
SERVER_URL = "http://{}:8000/api/data".format(SERVER_IP)

# Optional: ntfy still
NTFY_TOPIC = "diego_baby_monitor_c3A"

DEVICE_ID = "cry_esp32"

# --- PINS ---
SCK_PIN = 6
WS_PIN = 7
SD_PIN = 5

# --- AUDIO SETTINGS ---
SAMPLE_RATE = 22050
BLOCK_SIZE = 4096
MIN_FREQ = 1500
MAX_FREQ = 3500
MIN_VOLUME = 3000
TRIGGER_COUNT = 5

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)

    wlan.active(False)
    time.sleep(0.5)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to {}...".format(SSID))
        wlan.connect(SSID, PASSWORD)

        timeout = 12
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(".", end="")

    if wlan.isconnected():
        print("\nOnline! IP: {}".format(wlan.ifconfig()[0]))
    else:
        print("\nWifi Failed. Check Password or iPhone Screen.")

def post_to_django(cry_detected, freq_hz=None, volume=None):
    payload = {
        "device_id": DEVICE_ID,
        "cry_detected": bool(cry_detected),
    }
    if freq_hz is not None:
        payload["cry_freq_hz"] = float(freq_hz)
    if volume is not None:
        payload["cry_volume"] = float(volume)

    try:
        r = urequests.post(SERVER_URL, json=payload)
        r.close()
    except Exception as e:
        print("Django POST failed:", e)

def send_ntfy_alert():
    try:
        urequests.post("https://ntfy.sh/{}".format(NTFY_TOPIC), data="Baby Cry Detected!")
        print(">>> NTFY ALERT SENT! <<<")
    except Exception as e:
        print("NTFY Alert Failed:", e)

# --- MAIN SETUP ---
connect_wifi()

print("Starting I2S on IO{}/{}/{}...".format(SCK_PIN, WS_PIN, SD_PIN))
audio_in = machine.I2S(0,
    sck=machine.Pin(SCK_PIN),
    ws=machine.Pin(WS_PIN),
    sd=machine.Pin(SD_PIN),
    mode=machine.I2S.RX,
    bits=32,
    format=machine.I2S.MONO,
    rate=SAMPLE_RATE,
    ibuf=BLOCK_SIZE * 2)

buf = bytearray(BLOCK_SIZE)
cry_counter = 0
last_heartbeat = time.ticks_ms()

print("Listening for crying...")

while True:
    try:
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            connect_wifi()

        num_read = audio_in.readinto(buf)

        if num_read and num_read > 0:
            samples = array.array('i', buf)
            volume = (max(samples) - min(samples)) // 65536

            is_cry = False
            freq = None

            if volume > MIN_VOLUME:
                avg = sum(samples) // len(samples)
                crossings = 0
                for i in range(1, len(samples)):
                    if (samples[i] > avg and samples[i-1] <= avg) or \
                       (samples[i] < avg and samples[i-1] >= avg):
                        crossings += 1

                freq = (crossings / 2) / (len(samples) / SAMPLE_RATE)

                if MIN_FREQ <= freq <= MAX_FREQ:
                    is_cry = True
                    print("Cry Freq: {}Hz | Vol: {}".format(int(freq), volume))

            # Leaky bucket
            if is_cry:
                cry_counter += 1
            elif cry_counter > 0:
                cry_counter -= 1

            # Trigger
            if cry_counter >= TRIGGER_COUNT:
                print("!!! BABY CRYING !!!")

                # POST to Django (triggers web alarm)
                post_to_django(True, freq_hz=freq, volume=volume)

                # optional push
                send_ntfy_alert()

                cry_counter = 0
                time.sleep(5)
                gc.collect()

        # heartbeat every 5s so UI shows device alive even when quiet
        if time.ticks_diff(time.ticks_ms(), last_heartbeat) > 5000:
            post_to_django(False)
            last_heartbeat = time.ticks_ms()

        time.sleep(0.05)

    except Exception as e:
        print("Error in loop:", e)
        time.sleep(1)