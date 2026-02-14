import json
import time
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .state import latest

def index(request):
    return render(request, "monitor/index.html") #rendering the index.html page. Home page

def api_latest(request):
    return JsonResponse(latest) #return latest sensor reading. polls every 0.5 sec


# This api_latest function will responds with a JSON format something like this
# { "ts": 1690000000.0, "wave": 0.5, "bpm": 120.0, "status": "OK" }







# THis method will receive new sensor data from the device(ESP32)

@csrf_exempt
def api_data(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    # This endpoint exists so ESP32 can send readings POST /api/data. 
    # ^ we only allow POST method. If it's not POST, we return 400 Bad Request.

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")


    try:
        body = json.loads(request.body.decode("utf-8"))
        wave = float(body.get("wave"))
        bpm = float(body.get("bpm"))
        status = str(body.get("status"))
        if status not in ("OK", "ALERT"):
            return HttpResponseBadRequest("status must be OK or ALERT")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON payload. Expected {wave,bpm,status}")

    # ^ We expect the device to send a JSON payload with wave, bpm, and status.
    # # We parse it and validate it. If it's invalid, we return 400 Bad Request.


     # Optional extras
    pulse = body.get("pulse", None)
    temp_c = body.get("temp_c", None)
    cry_level = body.get("cry_level", None)
    crying = body.get("crying", None)

    # Validate optional fields if provided
    try:
        if pulse is not None:
            pulse = float(pulse)
        if temp_c is not None:
            temp_c = float(temp_c)
        if cry_level is not None:
            cry_level = float(cry_level)
            if cry_level < 0: cry_level = 0.0
            if cry_level > 1: cry_level = 1.0
        if crying is not None:
            crying = bool(crying)
    except Exception:
        return HttpResponseBadRequest("Optional fields invalid types")








    #Replaces last readings with new ones


    latest["ts"] = time.time()
    latest["wave"] = wave
    latest["bpm"] = bpm
    latest["status"] = status




    latest["pulse"] = pulse
    latest["temp_c"] = temp_c
    latest["cry_level"] = cry_level if cry_level is not None else latest.get("cry_level", 0.0)
    latest["crying"] = crying if crying is not None else latest.get("crying", False)



    return JsonResponse({"ok": True})
