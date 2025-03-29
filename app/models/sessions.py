from flask import current_app

def get_sessions_collection():
    return current_app.mongo_db.sessions

sessions_collection = get_sessions_collection()