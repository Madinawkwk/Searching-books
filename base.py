from flask.views import MethodView
from flask_restful import Resource
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user, login_required


class BaseMethodView(MethodView):
	def __init__(self, engine):
		self.engine: SQLAlchemy = engine



class BaseResource(Resource):
	def __init__(self, **kwargs):
		self.engine: SQLAlchemy = kwargs['engine']