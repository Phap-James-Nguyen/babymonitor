import json
import time
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .state import state, DEFAULTS


def index(request):
    return render(request, "monitor/index.html")


def api_latest(request):
    devices = state["devices"]

    breathing = devices.get("breathing_esp32", {})
    movement = devices.get("movement_arduino", {})

    out = {
        "breathing": {**DEFAULTS["breathing"], **breathing},
        "movement": {**DEFAULTS["movement"], **movement},
    }
    return JsonResponse(out)


@csrf_exempt
def api_data(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    device_id = body.get("device_id")
    if not device_id:
        return HttpResponseBadRequest(
            "device_id is required (e.g., breathing_esp32 or movement_arduino)"
        )
    device_id = str(device_id)

    # create device bucket if missing
    devices = state["devices"]
    if device_id not in devices:
        devices[device_id] = {}

    dev = devices[device_id]
    dev["device_id"] = device_id
    dev["ts"] = time.time()  # per-device timestamp

    # ---- Breathing fields (optional) ----
    if "wave" in body:
        try:
            dev["wave"] = float(body["wave"])
        except Exception:
            return HttpResponseBadRequest("wave must be a number")

    if "bpm" in body:
        try:
            dev["bpm"] = float(body["bpm"])
        except Exception:
            return HttpResponseBadRequest("bpm must be a number")

    if "status" in body:
        status = str(body["status"])
        if status not in ("OK", "ALERT"):
            return HttpResponseBadRequest("status must be OK or ALERT")
        dev["status"] = status

    # ---- Movement fields (optional) ----
    if "movement_state" in body:
        dev["movement_state"] = str(body["movement_state"]).upper()

    if "avg_move_g" in body:
        try:
            dev["avg_move_g"] = float(body["avg_move_g"])
        except Exception:
            return HttpResponseBadRequest("avg_move_g must be a number")

    if "light_events" in body:
        try:
            dev["light_events"] = int(body["light_events"])
        except Exception:
            return HttpResponseBadRequest("light_events must be an int")

    if "heavy_events" in body:
        try:
            dev["heavy_events"] = int(body["heavy_events"])
        except Exception:
            return HttpResponseBadRequest("heavy_events must be an int")

    if "drop" in body:
        drop_val = body["drop"]
        if isinstance(drop_val, bool):
            dev["drop"] = drop_val
        elif isinstance(drop_val, (int, float)):
            dev["drop"] = (drop_val != 0)
        elif isinstance(drop_val, str):
            dev["drop"] = drop_val.strip().lower() in ("true", "1", "yes", "y")
        else:
            return HttpResponseBadRequest("drop must be boolean-like")

    return JsonResponse({"ok": True})
