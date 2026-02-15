# monitor/state.py

latest_movement = {
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

latest_audio = {
    "ts": None,

    # audio (cry)
    "device_id": "cry_esp32",
    "cry_detected": False,
    "cry_freq_hz": None,
    "cry_volume": None,
}
