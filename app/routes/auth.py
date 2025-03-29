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
    user_id = session.get('user_id')
    if user_id:
        # MongoDB에서 세션 데이터 삭제
        current_app.mongo_db.sessions.delete_one({'_id': ObjectId(user_id)})
    session.clear()
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
        current_time = datetime.now(timezone.utc) 
        user_id = str(user['_id'])
        
        session_data = {
            'user_id': user_id,
            'session_token': session_token,
            'created_at': current_time  # 현재 시간 사용
        }

        # MongoDB sessions 컬렉션에 저장
        current_app.mongo_db.sessions.update_one(
            {'user_id': user_id},
            {'$set': {'session_token': session_token, 'created_at': current_time}},
            upsert=True
        )

        session['user_id'] = session_data['user_id']

        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'session': session_data
        })

    return jsonify({'status': 'error', 'message': 'Invalid password'}), 401
