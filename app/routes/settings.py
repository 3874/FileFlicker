from flask import current_app
from flask import Blueprint, request, jsonify, render_template, session
from datetime import datetime
from .. import prompts_collection
from ..utils.decorators import login_required

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/saveSettings', methods=['POST'])
@login_required
def save_settings():
    data = request.get_json()
    if data:
        config_path_local = os.path.join(SETTING_FOLDER, 'config.json')

        try:
            with open(config_path_local, 'r+') as config_file:
                config = json.load(config_file)
                
                # Update the configuration with the incoming data
                for key, value in data.items():
                    config[key] = value  # Update the config with new values
                
                # Write the updated configuration back to the file
                config_file.seek(0)
                json.dump(config, config_file, indent=4)
                config_file.truncate()
            return jsonify({'success': True}), 200
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Invalid data'}), 400


@bp.route('/getSettings', methods=['GET'])
@login_required
def get_settings():
    if not check_admin_role():
        return jsonify({'success': False, 'message': 'Access denied. Admins only.'}), 403


    config_path_local = os.path.join(SETTING_FOLDER, "config.json")
    if not os.path.exists(config_path_local):
        raise FileNotFoundError("Config file not found. Ensure config.json exists in the setting directory.")

    with open(config_path_local, "r") as json_file2:
        FF_configs = json.load(json_file2)
    return jsonify({'success': True, 'data': FF_configs}), 200

@bp.route('/getPrompts', methods=['POST'])
@login_required
def get_prompts():
    data = request.get_json()
    user_id = session['user_id']
    contents = prompts_collection.find_one({'user_id': user_id})
    
    if not contents:
        return jsonify({'status': "error", 'message': 'No prompts found for the user.'}), 404

    return jsonify({'status': 'success', 'data': contents['prompts']}), 200

@bp.route('/updatePrompts', methods=['PUT'])
@login_required
def update_prompts():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data.'}), 400
    print(data)
    user_id = session['user_id']
    result = prompts_collection.update_one(
        {'user_id': user_id},
        {'$set': {'prompts': data}},
        upsert=True
    )

    return jsonify({'status': 'success', 'data': data}), 200





