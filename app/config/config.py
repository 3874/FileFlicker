import os, json

class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SETTING_FOLDER = os.path.join(BASE_DIR, 'setting')
    
    os.makedirs(SETTING_FOLDER, exist_ok=True)
    config_path = os.path.join(SETTING_FOLDER, "config.json")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError("Config file not found. Ensure config.json exists in the setting directory.")

    with open(config_path, "r") as json_file:
        config = json.load(json_file)

    # Flask configuration
    SECRET_KEY = config.get('SECRET_KEY')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = config.get('SESSION_COOKIE_SECURE')
    SESSION_COOKIE_SAMESITE = 'Lax'

    # MongoDB configuration
    MONGO_URI = config.get('MONGO_URI')
    MONGO_DB_NAME = config.get('MONGO_DB_NAME')

    # AWS configuration
    AWS_ACCESS_KEY_ID = config.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = config.get('AWS_REGION')
    AWS_S3_BUCKET = config.get('AWS_S3_BUCKET')

    # OpenAI configuration
    OPENAI_KEY = config.get('OPENAI_KEY')

    # N8N configuration
    N8N_URL = config.get('n8n_URL')

    SENDER_EMAIL = config.get('SENDER_EMAIL')
    SENDER_PWD = config.get('SENDER_PWD')
    QDRANT_URL = config.get('QDRANT_URL')