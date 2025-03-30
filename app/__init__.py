from flask import Flask, render_template
import os
from flask_cors import CORS
from pymongo import MongoClient
import boto3
from .config.config import Config

# Global MongoDB collections
users_collection = None
projects_collection = None
files_collection = None
companies_collection = None
prompts_collection = None

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Load configuration
    app.config.from_object(Config)
    
    # Initialize MongoDB and set global collections
    global users_collection, projects_collection, files_collection, companies_collection, prompts_collection
    mongo_client = MongoClient(app.config['MONGO_URI'])
    db = mongo_client[app.config['MONGO_DB_NAME']]
    
    users_collection = db.users
    projects_collection = db.projects
    files_collection = db.files
    companies_collection = db.companies
    prompts_collection = db.prompts
    
    # Make collections available to the app context
    app.mongo_db = db

    # Initialize S3
    app.s3_client = boto3.client(
        's3',
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=app.config['AWS_REGION']
    )

    # Register blueprints - ensure each blueprint is registered only once
    from app.routes.auth import bp as auth_bp
    from app.routes.user import bp as user_bp
    from app.routes.file import bp as file_bp
    from app.routes.project import bp as project_bp
    from app.routes.company import bp as company_bp
    from app.routes.settings import bp as settings_bp
    from app.routes.search import bp as search_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(search_bp)

    # Set template folder path
    app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    
    # Add a basic route for testing
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/<page>')
    def render_page(page):
        return render_template(f'{page}.html')
    
    return app