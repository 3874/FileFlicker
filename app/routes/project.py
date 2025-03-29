import bcrypt
from flask import current_app
from flask import Blueprint, request, jsonify, render_template, session
from bson import ObjectId
from datetime import datetime
from .. import users_collection, projects_collection 
from ..utils.decorators import login_required

bp = Blueprint('project', __name__, url_prefix='/projects')

@bp.route('/', methods=['GET'])
@login_required
def get_projects():

    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 100))
    search_value = request.args.get('search[value]', '').lower()

    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    query = {}

    if user and user.get('role') == 'admin':
        if search_value:
            query["$or"] = [
                {"title": {"$regex": search_value, "$options": "i"}},
                {"summary": {"$regex": search_value, "$options": "i"}},
                {"contents": {"$regex": search_value, "$options": "i"}}
            ]
    else:
        query = {"owner": session['user_id']}
        if search_value:
            query["$or"] = [
                {"title": {"$regex": search_value, "$options": "i"}},
                {"summary": {"$regex": search_value, "$options": "i"}},
                {"contents": {"$regex": search_value, "$options": "i"}}
            ]

    total = projects_collection.count_documents(query)
    cursor = projects_collection.find(query).sort("createdAt", -1).skip(start).limit(length)
    paginated_projects = list(cursor)
    for p in paginated_projects:
        p['_id'] = str(p['_id'])

    response = {
        "draw": int(request.args.get('draw', 1)),
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": paginated_projects
    }
    return jsonify(response)

@bp.route('/newProject', methods=['POST'])
@login_required
def new_project():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data.'}), 400

    title = data.get('title')
    summary = data.get('summary')
    contents = data.get('contents')
    related_files = data.get('related_files', [])
    related_companies = data.get('related_companies', [])
    shared_users = data.get('shared', [])

    current_time = datetime.now().isoformat()
    new_entry = {
        'title': title,
        'summary': summary,
        'contents': contents,
        'related_files': related_files,
        'related_companies': related_companies,
        'owner': session['user_id'],
        'shared': shared_users,
        'createdAt': current_time,
        'updatedAt': current_time
    }

    result = projects_collection.insert_one(new_entry)
    new_entry['_id'] = str(result.inserted_id)
    return jsonify({'success': True, 'data': new_entry}), 201

@bp.route('/updateProject/<string:projectId>', methods=['PUT'])
@login_required
def update_project(projectId):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data.'}), 400

    try:
        obj_id = ObjectId(projectId)
    except Exception:
        return jsonify({'error': 'Invalid project ID format.'}), 400

    update_data = {key: value for key, value in data.items() if value is not None}
    update_data['updatedAt'] = datetime.now().isoformat()

    result = projects_collection.update_one({'_id': obj_id}, {'$set': update_data})
    if result.matched_count == 0:
        return jsonify({'error': 'Project not found.'}), 404

    project_entry = projects_collection.find_one({'_id': obj_id})
    project_entry['_id'] = str(project_entry['_id'])
    return jsonify({'success': True, 'data': project_entry}), 200

@bp.route('/removeProject/<string:projectId>', methods=['DELETE'])
@login_required
def remove_project(projectId):
    try:
        obj_id = ObjectId(projectId)
    except Exception:
        return jsonify({'error': 'Invalid project ID format.'}), 400

    result = projects_collection.delete_one({'_id': obj_id})
    if result.deleted_count == 0:
        return jsonify({'error': 'Project not found.'}), 404

    return jsonify({'success': True}), 200

@bp.route('/getProject/<string:projectId>', methods=['GET'])
@login_required
def get_project(projectId):
    try:
        obj_id = ObjectId(projectId)
    except Exception:
        return jsonify({'error': 'Invalid project ID format.'}), 400

    project_entry = projects_collection.find_one({'_id': obj_id})
    if not project_entry:
        return jsonify({'error': '프로젝트를 찾을 수 없습니다.'}), 404

    project_entry['_id'] = str(project_entry['_id'])
    return jsonify({'success': True, 'data': project_entry}), 200

@bp.route('/searchProject', methods=['GET'])
@login_required
def search_project():
    keywords = request.args.get('keywords', '')
    keywords_list = keywords.split()

    if not keywords_list:
        return jsonify({'error': 'No keywords provided.'}), 400

    and_conditions = []
    for keyword in keywords_list:
        or_condition = {
            "$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"summary": {"$regex": keyword, "$options": "i"}},
                {"contents": {"$regex": keyword, "$options": "i"}}
            ]
        }
        and_conditions.append(or_condition)

    query = {"$and": and_conditions} if and_conditions else {}
    results = list(projects_collection.find(query))
    for r in results:
        r['_id'] = str(r['_id'])
    return jsonify({'success': True, 'results': results}), 200

@bp.route('/exportProjecttoServer', methods=['POST'])
def export_project_to_server():
    data = request.json
    if not data or 'id' not in data or 'pwd' not in data:
        return jsonify({'error': 'ID and password are required.'}), 400

    user = users_collection.find_one({'ID': data['id']})
    if not user or not bcrypt.checkpw(data['pwd'].encode('utf-8'), user['password']):
        return jsonify({'error': 'Invalid ID or password.'}), 401

    userId = str(user['_id'])  # 사용자 ID를 가져옵니다.

    if data:
        contents = data.get('contents')
        summary = data.get('summary')
        title = data.get('title')

        current_time = datetime.now().isoformat()

        project_data = {
            'contents': contents,
            'summary': summary,
            'title': title,
            'owner': userId,
            'createdAt': current_time,
            'updatedAt': current_time,
        }

        result = projects_collection.insert_one(project_data)
        return jsonify({'status': 'success', 'message': 'Project added successfully!', 'data': {'_id': str(result.inserted_id)}}), 201

    return jsonify({'status': 'fail', 'message': 'Invalid data'}), 400
