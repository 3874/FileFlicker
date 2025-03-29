import bcrypt
from flask import current_app
from flask import Blueprint, request, jsonify, render_template, session
from bson import ObjectId
from datetime import datetime
from .. import users_collection, companies_collection 
from ..utils.decorators import login_required

bp = Blueprint('company', __name__, url_prefix='/companies')

@bp.route('/', methods=['GET'])
@login_required
def get_companies():
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 100))
    search_value = request.args.get('search[value]', '').lower()

    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    query = {}

    if user and user.get('role') == 'admin':
        # Admin인 경우 모든 데이터에서 검색
        if search_value:
            query["$or"] = [
                {"companyName": {"$regex": search_value, "$options": "i"}},
                {"companyEnName": {"$regex": search_value, "$options": "i"}},
                {"industry": {"$regex": search_value, "$options": "i"}},
                {"summary": {"$regex": search_value, "$options": "i"}},
                {"comment": {"$regex": search_value, "$options": "i"}}
            ]
    else:
        # 일반 사용자일 경우 소유자에 따라 검색
        query = {"owner": session['user_id']}
        if search_value:
            query["$or"] = [
                {"companyName": {"$regex": search_value, "$options": "i"}},
                {"companyEnName": {"$regex": search_value, "$options": "i"}},
                {"industry": {"$regex": search_value, "$options": "i"}},
                {"summary": {"$regex": search_value, "$options": "i"}},
                {"comment": {"$regex": search_value, "$options": "i"}}
            ]

    total = companies_collection.count_documents(query)
    cursor = companies_collection.find(query).sort("createdAt", -1).skip(start).limit(length)
    paginated_companies = list(cursor)
    for c in paginated_companies:
        c['_id'] = str(c['_id'])

    response = {
        "draw": int(request.args.get('draw', 1)),
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": paginated_companies
    }
    return jsonify(response)

@bp.route('/getCompany/<company_id>', methods=['GET'])
@login_required
def get_company(company_id):
    try:
        company = companies_collection.find_one({'_id': ObjectId(company_id)})
        if not company:
            return jsonify({'status': 'error', 'message': 'Company not found'}), 404 

        company['_id'] = str(company['_id']) 

        return jsonify({'status': 'success', 'data': company})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/addCompany', methods=['POST'])
@login_required
def add_company():
    data = request.get_json()
    if data:
        companyName = data.get('companyName')
        companyEnName = data.get('companyEnName')
        industry = data.get('industry')
        summary = data.get('summary')
        comment = data.get('comment')

        current_time = datetime.now().isoformat()

        company_data = {
            'companyName': companyName,
            'companyEnName': companyEnName,
            'industry': industry,
            'summary': summary,
            'comment': comment,
            'owner': session['user_id'],
            'createdAt': current_time,
            'updatedAt': current_time,
        }

        result = companies_collection.insert_one(company_data)
        return jsonify({'status': 'success', 'message': 'Company added successfully!', 'data': {'_id': str(result.inserted_id)}}), 201

    return jsonify({'status': 'fail', 'message': 'Invalid data'}), 400


@bp.route('/exportCompanytoServer', methods=['POST'])
def export_company_to_server():
    data = request.json

    if not data or 'id' not in data or 'pwd' not in data:
        return jsonify({'error': 'ID and password are required.'}), 400

    user = users_collection.find_one({'ID': data['id']})
    if not user or not bcrypt.checkpw(data['pwd'].encode('utf-8'), user['password']):
        return jsonify({'error': 'Invalid ID or password.'}), 401

    userId = str(user['_id'])  # 사용자 ID를 가져옵니다.

    if data:
        companyName = data.get('companyName')
        companyEnName = data.get('companyEnName')
        industry = data.get('industry')
        summary = data.get('summary')
        comment = data.get('comment')

        current_time = datetime.now().isoformat()

        company_data = {
            'companyName': companyName,
            'companyEnName': companyEnName,
            'industry': industry,
            'summary': summary,
            'comment': comment,
            'owner': userId,
            'createdAt': current_time,
            'updatedAt': current_time,
        }

        result = companies_collection.insert_one(company_data)
        return jsonify({'status': 'success', 'message': 'Company added successfully!', 'data': {'_id': str(result.inserted_id)}}), 201

    return jsonify({'status': 'fail', 'message': 'Invalid data'}), 400

@bp.route('/updateCompany/<string:companyId>', methods=['PUT'])
@login_required
def update_company(companyId):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data.'}), 400
    try:
        obj_id = ObjectId(companyId)
    except Exception:
        return jsonify({'error': 'Invalid company ID format.'}), 400
    update_data = {key: value for key, value in data.items() if value is not None}
    update_data['updatedAt'] = datetime.now().isoformat()
    
    # update_one 결과에서 matched_count와 modified_count를 추출합니다.
    company_entry = companies_collection.update_one({'_id': obj_id}, {'$set': update_data})
    
    # 반환할 응답을 수정
    if company_entry.matched_count == 0:
        return jsonify({'status': 'error', 'message': 'No company found with the given ID.'}), 404
        
    return jsonify({'status': 'success', 'modified_count': company_entry.modified_count}), 200

@bp.route('/deleteCompany/<string:companyId>', methods=['DELETE'])
@login_required
def delete_company(companyId):
    try:
        obj_id = ObjectId(companyId)
    except Exception:
        return jsonify({'error': 'Invalid company ID format.'}), 400

    company_entry = companies_collection.find_one({'_id': obj_id})
    if not company_entry:
        return jsonify({'error': 'Company not found.'}), 404

    companies_collection.delete_one({'_id': obj_id})
    return jsonify({'success': True, 'message': 'Company deleted successfully!'}), 200
