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

@csrf_exempt
def api_data(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    # Optional: device id (recommended when multiple devices post)
    device_id = body.get("device_id", None)
    if device_id is not None:
        latest["device_id"] = str(device_id)

    latest["ts"] = time.time()  # mark update time

    # ---- Breathing fields (optional) ----
    if "wave" in body:
        try:
            latest["wave"] = float(body["wave"])
        except Exception:
            return HttpResponseBadRequest("wave must be a number")

    if "bpm" in body:
        try:
            latest["bpm"] = float(body["bpm"])
        except Exception:
            return HttpResponseBadRequest("bpm must be a number")

    if "status" in body:
        status = str(body["status"])
        if status not in ("OK", "ALERT"):
            return HttpResponseBadRequest("status must be OK or ALERT")
        latest["status"] = status

    # ---- Movement fields (NEW, optional) ----
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
        # body["drop"] could be true/false, 0/1, "true"/"false"
        drop_val = body["drop"]
        if isinstance(drop_val, bool):
            latest["drop"] = drop_val
        elif isinstance(drop_val, (int, float)):
            latest["drop"] = (drop_val != 0)
        elif isinstance(drop_val, str):
            latest["drop"] = drop_val.strip().lower() in ("true", "1", "yes", "y")
        else:
            return HttpResponseBadRequest("drop must be boolean-like")

    return JsonResponse({"ok": True})
