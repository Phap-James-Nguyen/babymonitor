import json
import time
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .state import latest


def index(request):
    return render(request, "monitor/index.html")


def api_latest(request):
    return JsonResponse(latest)


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

    latest["ts"] = time.time()

    if "device_id" in body:
        latest["device_id"] = str(body["device_id"])

    # movement
    if "movement_state" in body:
        latest["movement_state"] = str(body["movement_state"]).upper()

    if "avg_move_g" in body:
        try:
            latest["avg_move_g"] = float(body["avg_move_g"])
        except Exception:
            return HttpResponseBadRequest("avg_move_g must be a number")

    if "light_events" in body:
        try:
            latest["light_events"] = int(body["light_events"])
        except Exception:
            return HttpResponseBadRequest("light_events must be an int")

    if "heavy_events" in body:
        try:
            latest["heavy_events"] = int(body["heavy_events"])
        except Exception:
            return HttpResponseBadRequest("heavy_events must be an int")

    if "drop" in body:
        try:
            latest["drop"] = _parse_boolish(body["drop"], "drop")
        except Exception as e:
            return HttpResponseBadRequest(str(e))

    if "face_down" in body:
        try:
            latest["face_down"] = _parse_boolish(body["face_down"], "face_down")
        except Exception as e:
            return HttpResponseBadRequest(str(e))

    # environment
    if "temp_c" in body:
        try:
            latest["temp_c"] = float(body["temp_c"])
        except Exception:
            return HttpResponseBadRequest("temp_c must be a number")

    if "temp_f" in body:
        try:
            latest["temp_f"] = float(body["temp_f"])
        except Exception:
            return HttpResponseBadRequest("temp_f must be a number")

    if "humidity" in body:
        try:
            latest["humidity"] = float(body["humidity"])
        except Exception:
            return HttpResponseBadRequest("humidity must be a number")

    if "env_status" in body:
        s = str(body["env_status"]).upper()
        if s not in ("OK", "ALERT"):
            return HttpResponseBadRequest("env_status must be OK or ALERT")
        latest["env_status"] = s

    return JsonResponse({"ok": True})
