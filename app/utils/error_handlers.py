from flask import jsonify
import logging

def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error(f"Server error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred.'}), 500
