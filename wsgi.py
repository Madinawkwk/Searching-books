from app import create_app, socketio
from models import fill_db

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
    #app.run(port=9000, debug=True, use_reloader=False)

