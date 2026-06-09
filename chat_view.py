from flask import render_template
from flask.views import MethodView
from flask_login import login_required


class ChatView(MethodView):
    @login_required
    def get(self):
        return render_template('chat.html')
