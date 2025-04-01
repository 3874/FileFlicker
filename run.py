from flask import send_from_directory
from app import create_app
import os

app = create_app()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=21213, debug=True, threaded=True, use_reloader=False)