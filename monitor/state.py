# monitor/state.py

latest = {
    "ts": None,

    # movement
    "device_id": "movement_arduino",
    "movement_state": "UNKNOWN",
    "avg_move_g": 0.0,
    "light_events": 0,
    "heavy_events": 0,
    "drop": False,
    "face_down": False,

    # environment
    "temp_c": None,
    "temp_f": None,
    "humidity": None,
    "env_status": "OK",   # OK / ALERT
}
