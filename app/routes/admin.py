from flask import Blueprint, request, jsonify, render_template, session
from flask import current_app

from app import mongo_db, s3_client

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/', methods=['GET'])
def get_admin():
    return render_template(f'/admin/index.html')

@bp.route('/<page>')
def render_page(page):
    return render_template(f'/admin/{page}.html')