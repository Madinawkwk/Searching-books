from flask import render_template
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_socketio import emit


def register_socketio_handlers(socketio):
    # @socketio.on('connect')
    # def handle_connect():
    #     username = current_user.username if current_user.is_authenticated else 'anonymous'
    #     print(f'client connected: {username}')
    #
    # @socketio.on('disconnect')
    # def handle_disconnect():
    #     print('Client disconnected')

    @socketio.on('send_message')
    def handle_send_message(data):
        if current_user.is_authenticated:
            username = current_user.username
        else:
            username = 'anonymous'

        message = data.get('message', '').strip()
        if message:
            print(f'Message from {username}: {message}')
            socketio.emit('new_message', {
                'username': username,
                'message': message
            })