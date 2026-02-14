import time

latest = {
    "ts": time.time(),
    "wave": 0.0,       # breathing waveform
    "bpm": 0.0,        # breaths/min
    "status": "OK",    # OK or ALERT

    "pulse": None,     # heart rate bpm (int/float)
    "temp_c": None,    # body temperature in C
    "cry_level": 0.0,  # 0..1
    "crying": False,   # bool
}


# This file is used to store the latest data from the monitor app. 
# # It is used to display the data on the dashboard.

# Our device sends data via POST request to the /api/data endpoint. 
# #The data is stored in the latest variable.
#  The dashboard retrieves the data from the latest variable and displays it to the user via GET /api/latest/ endpoint.




#Summary: we store the most recent data here so both endpoints can access it. The device updates it, and the dashboard reads from it.
#NOTE: This is not permanent storage. If the server restarts, the data will be lost. 
# In a production environment, we would use a database to store this data.