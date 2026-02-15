import json
import time
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .state import latest_movement, latest_audio

CRY_STALE_SEC = 6.0


def index(request):
    return render(request, "monitor/index.html")


def api_latest(request):
    now = time.time()
    m = dict(latest_movement)
    a = dict(latest_audio)

    ts_a = a.get("ts")
    if isinstance(ts_a, (int, float)) and (now - ts_a) > CRY_STALE_SEC:
        a["cry_detected"] = False
    elif not isinstance(ts_a, (int, float)):
        a["cry_detected"] = False

    return JsonResponse({"movement": m, "audio": a, "server_ts": now})


def _parse_boolish(val, field_name="field"):
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes", "y", "on")
    raise ValueError(f"{field_name} must be boolean-like")


@csrf_exempt
def api_data(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    device_id = str(body.get("device_id", "")).strip() or "unknown"
    now_ts = time.time()

    # ----------------------------
    # MOVEMENT DEVICE (Arduino)
    # ----------------------------
    if device_id == "movement_arduino":
        latest_movement["ts"] = now_ts
        latest_movement["device_id"] = device_id

        if "movement_state" in body:
            latest_movement["movement_state"] = str(body["movement_state"]).upper()

        if "avg_move_g" in body:
            try:
                latest_movement["avg_move_g"] = float(body["avg_move_g"])
            except Exception:
                return HttpResponseBadRequest("avg_move_g must be a number")

        if "light_events" in body:
            try:
                latest_movement["light_events"] = int(body["light_events"])
            except Exception:
                return HttpResponseBadRequest("light_events must be an int")

        if "heavy_events" in body:
            try:
                latest_movement["heavy_events"] = int(body["heavy_events"])
            except Exception:
                return HttpResponseBadRequest("heavy_events must be an int")

        if "drop" in body:
            try:
                latest_movement["drop"] = _parse_boolish(body["drop"], "drop")
            except Exception as e:
                return HttpResponseBadRequest(str(e))

        if "face_down" in body:
            try:
                latest_movement["face_down"] = _parse_boolish(body["face_down"], "face_down")
            except Exception as e:
                return HttpResponseBadRequest(str(e))

        if "temp_c" in body:
            try:
                latest_movement["temp_c"] = float(body["temp_c"])
            except Exception:
                return HttpResponseBadRequest("temp_c must be a number")

        if "temp_f" in body:
            try:
                latest_movement["temp_f"] = float(body["temp_f"])
            except Exception:
                return HttpResponseBadRequest("temp_f must be a number")

        if "humidity" in body:
            try:
                latest_movement["humidity"] = float(body["humidity"])
            except Exception:
                return HttpResponseBadRequest("humidity must be a number")

        if "env_status" in body:
            s = str(body["env_status"]).upper()
            if s not in ("OK", "ALERT"):
                return HttpResponseBadRequest("env_status must be OK or ALERT")
            latest_movement["env_status"] = s

        return JsonResponse({"ok": True, "device": "movement"})

    # ----------------------------
    # AUDIO DEVICE (ESP32)
    # ----------------------------
    if device_id == "cry_esp32":
        latest_audio["ts"] = now_ts
        latest_audio["device_id"] = device_id

        if "cry_detected" in body:
            try:
                latest_audio["cry_detected"] = _parse_boolish(body["cry_detected"], "cry_detected")
            except Exception as e:
                return HttpResponseBadRequest(str(e))

        if "cry_freq_hz" in body:
            try:
                latest_audio["cry_freq_hz"] = float(body["cry_freq_hz"])
            except Exception:
                return HttpResponseBadRequest("cry_freq_hz must be a number")

        if "cry_volume" in body:
            try:
                latest_audio["cry_volume"] = float(body["cry_volume"])
            except Exception:
                return HttpResponseBadRequest("cry_volume must be a number")

        # ✅ Accept env fields from ESP32 (preferred)
        if "temp_c" in body:
            try:
                latest_audio["temp_c"] = float(body["temp_c"])
            except Exception:
                return HttpResponseBadRequest("temp_c must be a number")

        if "temp_f" in body:
            try:
                latest_audio["temp_f"] = float(body["temp_f"])
            except Exception:
                return HttpResponseBadRequest("temp_f must be a number")

        if "humidity" in body:
            try:
                latest_audio["humidity"] = float(body["humidity"])
            except Exception:
                return HttpResponseBadRequest("humidity must be a number")

        if "env_status" in body:
            s = str(body["env_status"]).upper()
            if s not in ("OK", "ALERT"):
                return HttpResponseBadRequest("env_status must be OK or ALERT")
            latest_audio["env_status"] = s

        # ✅ Backward-compat: if ESP sends "temperature" instead of temp_c
        if "temperature" in body and "temp_c" not in body:
            try:
                tc = float(body["temperature"])
                latest_audio["temp_c"] = tc
                latest_audio["temp_f"] = tc * 1.8 + 32.0
            except Exception:
                return HttpResponseBadRequest("temperature must be a number")

        return JsonResponse({"ok": True, "device": "audio"})

    return HttpResponseBadRequest("Unknown device_id")
