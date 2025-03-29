import bcrypt, requests
from flask import current_app
from flask import Blueprint, request, jsonify, render_template, session
from bson import ObjectId
from datetime import datetime
from ..config.config import Config

bp = Blueprint('search', __name__, url_prefix='/search')

@bp.route('/AISearch', methods=['POST'])
def AI_search():
    data = request.get_json()
    if not data or not isinstance(data, list) or not data:
        return jsonify({'status':'error', 'data':'Invalid JSON data.'}), 400

    chatInput = data[0].get('chatInput', '')
    AI_url = 'https://api.openai.com/v1/chat/completions'
    search_results = chat_with_openai(AI_url, chatInput)

    return jsonify({'reply': search_results})


@bp.route('/complexSearch', methods=['POST'])
def complex_search():
    data = request.get_json()

    if not isinstance(data, list) or len(data) == 0:
        return jsonify({'error': 'Invalid data format'}), 400

    YlemURL = f"{Config.N8N_URL}/webhook/complex-search"

    try:
        response = requests.post(
            YlemURL,
            json=[{
                "sessionId": data[0].get('sessionId'),
                "action": data[0].get('action'),
                "chatInput": data[0].get('chatInput'),
            }]
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': f'HTTP error occurred: {str(e)}'}), 500
    except requests.exceptions.ConnectionError as e:
        return jsonify({'error': f'Connection error occurred: {str(e)}'}), 500
    except requests.exceptions.Timeout as e:
        return jsonify({'error': f'Timeout error occurred: {str(e)}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
@bp.route('/WebSearch', methods=['POST'])
def web_search():
    data = request.get_json()

    if not isinstance(data, list) or len(data) == 0:
        return jsonify({'error': 'Invalid data format'}), 400

    YlemURL = f"{Config.N8N_URL}/webhook/web-search"

    try:
        response = requests.post(
            YlemURL,
            json=[{
                "sessionId": data[0].get('sessionId'),
                "action": data[0].get('action'),
                "chatInput": data[0].get('chatInput'),
            }]
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': f'HTTP error occurred: {str(e)}'}), 500
    except requests.exceptions.ConnectionError as e:
        return jsonify({'error': f'Connection error occurred: {str(e)}'}), 500
    except requests.exceptions.Timeout as e:
        return jsonify({'error': f'Timeout error occurred: {str(e)}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

def chat_with_openai(Requrl, chatInput):
    url = Requrl
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {Config.OPENAI_KEY}'
    }

    data = {
        'model': "gpt-4o-mini",
        'messages': [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": chatInput}
        ],
        'max_tokens': 4096,
        'temperature': 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        logging.info('Response received from OpenAI API')
        summary = result['choices'][0]['message']['content'].strip()
        return summary
    except requests.exceptions.HTTPError as err:
        logging.error(f'HTTP error occurred: {err}')
        try:
            error_details = response.json()
            logging.error(f'Error details: {error_details}')
        except Exception:
            logging.error('No error details available.')
        return "An error occurred while processing your request."
    except Exception as ex:
        logging.error(f'Unexpected error: {ex}')
        return "An unexpected error occurred."
