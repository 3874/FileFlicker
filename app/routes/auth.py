from flask import Blueprint, request, jsonify, session
from flask import current_app
import bcrypt
import os
import base64
from datetime import datetime, timezone
from bson import ObjectId

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/signout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'status': 'success', 'message': 'Logged out'})


@bp.route('/authenticateUser', methods=['POST'])
def authenticate_user():
    data = request.json
    if not data or 'ID' not in data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid request'}), 400

    users_collection = current_app.mongo_db.users
    user = users_collection.find_one({'ID': data['ID']})
    
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    # Password verification
    stored_password = user['password']
    if isinstance(stored_password, bytes):
        hashed_bytes = stored_password
    else:
        hashed_bytes = stored_password.encode('utf-8')

    if bcrypt.checkpw(data['password'].encode('utf-8'), hashed_bytes):
        if not user.get('role'):
            return jsonify({'status': 'pending', 'message': 'User role is not assigned. Contact Admin.'}), 403

        session_token = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
        session_data = {
            'user_id': str(user['_id']),
            'session_token': session_token,
            'created_at': datetime.now(timezone.utc)
        }

        current_app.mongo_db.sessions.update_one(
            {'_id': ObjectId(session_data['user_id'])},
            {'$set': session_data},
            upsert=True
        )

        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'session': session_data
        })

    return jsonify({'status': 'error', 'message': 'Invalid password'}), 401
