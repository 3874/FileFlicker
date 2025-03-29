import bcrypt
from flask import current_app
from flask import Blueprint, request, jsonify, render_template, session
from bson import ObjectId
from datetime import datetime
from .. import users_collection
from ..utils.decorators import login_required

bp = Blueprint('user', __name__, url_prefix='/users')

@bp.route('/', methods=['GET'])
@login_required
def get_users():
    if not check_admin_role():
        return jsonify({'success': False, 'message': 'Access denied. Admins only.'}), 403
    
    try:
        users = list(users_collection.find())

        user_data = []
        for user in users:
            user_data.append({
                '_id': str(user['_id']),
                'ID': user.get('ID', ''),  # ID 필드
                'name': user.get('name', ''),  # 이름 필드
                'role': user.get('role', ''),  # 역할 필드
                'hire_date': user.get('hire_date', ''), 
                'createdAt': user.get('createdAt', '').isoformat(),  # 생성 날짜
                'updatedAt': user.get('updatedAt', '').isoformat(),  # 업데이트 날짜
            })

        return jsonify({'status': 'success', 'data': user_data})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/addUser', methods=['POST'])
def add_user():
    data = request.json

    if not data or 'ID' not in data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid request'}), 400

    # 비밀번호 해싱
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

    # 사용자 정보를 데이터베이스에 저장
    user_data = {
        'ID': data['ID'],
        'password': hashed_password,  # 해시된 비밀번호 저장
        'role': 'pending',
        'createdAt': datetime.now(),
        'updatedAt': datetime.now(),
    }

    # 사용자 추가
    users_collection.insert_one(user_data)

    return jsonify({'status': 'success', 'message': 'User added successfully'}), 201

@bp.route('/updateUser/<user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    try:
        data = request.json
        
        # 비밀번호가 없을 경우 비밀번호 업데이트를 생략
        update_fields = {
            'ID': data.get('ID'),
            'name': data.get('name', ''),
            'role': data.get('role', ''),
            'hire_date': data.get('hire_date', ''),
            'updatedAt': datetime.now()
        }

        # 비밀번호가 제공된 경우 해시 처리
        if 'password' in data:
            hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            update_fields['password'] = Binary(hashed)

        result = users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_fields}
        )

        if result.modified_count == 0:
            return jsonify({'status': 'error', 'message': 'User not found or no changes made'}), 404
        
        return jsonify({'status': 'success', 'message': 'User updated'})
    
    except errors.InvalidId:
        return jsonify({'status': 'error', 'message': 'Invalid ID format'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/getUser/<user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    print(user_id)
    try:
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        user['_id'] = str(user['_id'])
        user_data = {
            '_id': user['_id'],
            'ID': user.get('ID', ''),
            'name': user.get('name', ''),
            'role': user.get('role', ''),
            'hire_date': user.get('hire_date', ''), 
            'createdAt': user.get('createdAt').isoformat() if isinstance(user.get('createdAt'), datetime) else '',
            'updatedAt': user.get('updatedAt').isoformat() if isinstance(user.get('updatedAt'), datetime) else '',
        }

        return jsonify({'status': 'success', 'data': user_data}), 200  # 성공 시 200 상태 코드 반환
    
    except errors.InvalidId:  # InvalidId 예외 처리
        return jsonify({'status': 'error', 'message': 'Invalid ID format'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/deleteUser/<user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    try:
        result = users_collection.delete_one({'_id': ObjectId(user_id)})
        if result.deleted_count == 0:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        return jsonify({'status': 'success', 'message': 'User deleted'})
    except errors.InvalidId:
        return jsonify({'status': 'error', 'message': 'Invalid ID format'}), 400

@bp.route('/searchUser', methods=['GET'])
@login_required
def search_user():
    search_query = request.args.get('query', '').strip()
    if not search_query:
        return jsonify({'status': 'error', 'message': 'Query parameter is required'}), 400

    users = list(users_collection.find({
        '$or': [
            {'ID': {'$regex': search_query, '$options': 'i'}},  # 사용자 ID 검색
            {'name': {'$regex': search_query, '$options': 'i'}}  # 사용자 이름 검색
        ]
    }, {'_id': 1, 'ID': 1, 'name': 1}))  # 필요한 필드만 반환

    for user in users:
        user['_id'] = str(user['_id'])  # ObjectId를 문자열로 변환

    return jsonify({'status': 'success', 'data': users})

def check_admin_role():
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    
    # 사용자 역할 확인
    if user is None or user.get('role') != 'admin':
        return False
    return True
