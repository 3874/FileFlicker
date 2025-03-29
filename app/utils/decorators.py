from functools import wraps
from flask import session, jsonify, current_app
from bson import ObjectId
from datetime import datetime, timezone

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({'error': 'No session found'}), 401

        try:
            session_data = current_app.mongo_db.sessions.find_one({
                'user_id': user_id 
            })

            if not session_data:
                return jsonify({'error': 'Invalid session'}), 401

            created_at = session_data.get('created_at')
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            current_time = datetime.now(timezone.utc) 
            time_diff = current_time - created_at

            time_diff_seconds = time_diff.total_seconds()
            
            if not created_at or time_diff_seconds > 3600:
                current_app.mongo_db.sessions.delete_one({'user_id': user_id})
                return jsonify({'error': 'Session expired'}), 401

            return f(*args, **kwargs)

        except Exception as e:
            return jsonify({'error': f'Session validation error: {str(e)}'}), 401

    return decorated_function