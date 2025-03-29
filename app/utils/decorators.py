from functools import wraps
from flask import jsonify, request, current_app

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header is None or not auth_header.startswith('Bearer '):
            return jsonify({'status': 'error', 'message': 'Token missing'}), 401
        
        session_token = auth_header.split('Bearer ')[1]
        session_data = current_app.mongo_db.sessions.find_one({'session_token': session_token})
        
        if not session_data:
            return jsonify({'status': 'error', 'message': 'Invalid or expired session'}), 401

        return f(*args, **kwargs)
    return decorated_function