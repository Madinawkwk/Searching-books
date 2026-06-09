import os
from flask_socketio import SocketIO
from flask import Flask
from flask_restful import Api
from chat_view import ChatView
from flask_session import Session
from sqlalchemy import select
from extenstions import db, login_manager, api
from websocket import register_socketio_handlers
from models import db, User, create_db, fill_db
from book.views import (
    SearchView, BookDetailView, FavoriteAddView, FavoriteRemoveView,
    FavoritesView, ReviewCreateView, AccountSettingsView, ReviewEditView, ReviewDeleteView
)
from book.api import SearchAPIResource, BookDetailAPIResource, FavoriteListAPIResource
from oauth import configure_oauth
from user.oauth import OAuthAuthorizeView, OAuthCallbackView
from user.views import RegisterView, LoginView, LogoutView, ProfileView, PostCreateView, PostEditView, PostDeleteView

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

socketio = SocketIO(cors_allowed_origins="*")
def create_app(config: dict=None):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    app.secret_key = 'sdfdghgdsgdf hkfgnfdgfdbgxjdf'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    if config:
        app.config.update(config)

    db.init_app(app)
    login_manager.init_app(app)

    create_db(app)
    Session(app)
    configure_oauth(app)
    socketio.init_app(app)
    register_socketio_handlers(socketio)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)


    @login_manager.user_loader
    def load_user(user_id: int) -> User | None:
        stmt: str = select(User).where(User.id == int(user_id))
        return db.session.execute(stmt).scalar_one_or_none()

    app.add_url_rule('/', view_func=SearchView.as_view('search'), methods=['GET', 'POST'])
    app.add_url_rule('/book/<olid>', view_func=BookDetailView.as_view('book_detail'))
    app.add_url_rule('/favorite/add/<olid>', view_func=FavoriteAddView.as_view('favorite_add'), methods=['POST'])
    app.add_url_rule('/favorite/remove/<olid>', view_func=FavoriteRemoveView.as_view('favorite_remove'), methods=['POST'])
    app.add_url_rule('/favorites', view_func=FavoritesView.as_view('favorites'))
    app.add_url_rule('/review/<olid>', view_func=ReviewCreateView.as_view('review_create'), methods=['POST'])
    app.add_url_rule('/register', view_func=RegisterView.as_view('register'), methods=['GET', 'POST'])
    app.add_url_rule('/login', view_func=LoginView.as_view('login'), methods=['GET', 'POST'])
    app.add_url_rule('/logout', view_func=LogoutView.as_view('logout'))
    app.add_url_rule('/profile', view_func=ProfileView.as_view('profile'))
    app.add_url_rule('/post/create', view_func=PostCreateView.as_view('post_create'), methods=['GET', 'POST'])
    app.add_url_rule('/account/settings', view_func=AccountSettingsView.as_view('account_settings'), methods=['GET', 'POST'])
    app.add_url_rule('/post/<int:post_id>/edit', view_func=PostEditView.as_view('post_edit'), methods=['GET', 'POST'])
    app.add_url_rule('/post/<int:post_id>/delete', view_func=PostDeleteView.as_view('post_delete'), methods=['POST'])
    app.add_url_rule('/review/<int:review_id>/edit', view_func=ReviewEditView.as_view('review_edit'), methods=['GET', 'POST'])
    app.add_url_rule('/review/<int:review_id>/delete', view_func=ReviewDeleteView.as_view('review_delete'), methods=['POST'])
    app.add_url_rule('/oauth/<provider>', view_func=OAuthAuthorizeView.as_view('oauth_authorize'))
    app.add_url_rule('/oauth/<provider>/callback', view_func=OAuthCallbackView.as_view('oauth_callback'))
    app.add_url_rule('/chat', view_func=ChatView.as_view('chat'))
    api = Api(app)
    api.add_resource(SearchAPIResource, '/api/search')
    api.add_resource(BookDetailAPIResource, '/api/book/<string:olid>')
    api.add_resource(FavoriteListAPIResource, '/api/favorites')


    return app
