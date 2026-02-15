import time

# monitor/state.py

state = {
    "devices": {
        # device_id -> latest payload + server timestamp
        # "breathing_esp32": {"ts": 0, ...},
        # "movement_arduino": {"ts": 0, ...},
    }
}

DEFAULTS = {
    "breathing": {"device_id": None, "bpm": None, "wave": None, "status": "OK", "ts": None},
    "movement": {
        "device_id": None,
        "movement_state": "UNKNOWN",
        "avg_move_g": 0.0,
        "light_events": 0,
        "heavy_events": 0,
        "drop": False,
        "ts": None,
    },
}



# This file is used to store the latest data from the monitor app. 
# # It is used to display the data on the dashboard.

# Our device sends data via POST request to the /api/data endpoint. 
# #The data is stored in the latest variable.
#  The dashboard retrieves the data from the latest variable and displays it to the user via GET /api/latest/ endpoint.

# Right now an issue is that there will be overlap between the two endpoints: POST /api/data updates the latest variable, 
# and GET /api/latest/ reads from the latest variable to display the most recent data on the dashboard.


#Summary: we store the most recent data here so both endpoints can access it. The device updates it, and the dashboard reads from it.
#NOTE: This is not permanent storage. If the server restarts, the data will be lost. 
# In a production environment, we would use a database to store this data.