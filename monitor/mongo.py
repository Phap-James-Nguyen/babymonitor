import os
from pymongo import MongoClient

_client = None

def get_collection():
    global _client
    uri = os.getenv("MONGO_URI")
    if not uri:
        return None

    db_name = os.getenv("MONGO_DB", "baby_monitor")
    coll_name = os.getenv("MONGO_COLL", "events")

    if _client is None:
        _client = MongoClient(uri)

    return _client[db_name][coll_name]
