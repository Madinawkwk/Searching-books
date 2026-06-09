import datetime
import os

from flask import render_template, request, redirect, url_for, flash, abort, current_app
from flask.views import MethodView
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models import db, User, Post, Profile
from oauth import oauth
from user.forms import RegisterForm, LoginForm, PostForm, EditPostForm, AccountSettingsForm


class RegisterView(MethodView):
    def get(self):
        form = RegisterForm()
        return render_template('register.html', form=form)

    def post(self):
        form = RegisterForm()
        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data).first():
                flash('Email уже зарегистрирован', 'danger')
            else:
                user = User(
                    username=form.username.data,
                    email=form.email.data,
                    password_hash=generate_password_hash(form.password.data)
                )
                db.session.add(user)
                db.session.commit()
                profile = Profile(user_id=user.id)
                db.session.add(profile)
                db.session.commit()
                flash('registration was successful! Sign in.', 'success')
                return redirect(url_for('login'))
        return render_template('register.html', form=form)

class LoginView(MethodView):
    def get(self):
        form = LoginForm()
        return render_template('login.html', form=form)

    def post(self):
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash('you entered to the system', 'success')
                return redirect(url_for('search'))
            flash('wrong email', 'danger')
        return render_template('login.html', form=form)

class LogoutView(MethodView):
    @login_required
    def get(self):
        logout_user()
        flash('you are logged out', 'info')
        return redirect(url_for('search'))

class ProfileView(MethodView):
    @login_required
    def get(self):
        posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
        return render_template('profile.html', user=current_user, posts=posts)

class PostCreateView(MethodView):
    @login_required
    def get(self):
        form = PostForm()
        return render_template('create_post.html', form=form)

    def post(self):
        form = PostForm()
        if form.validate_on_submit():
            post = Post(
                user_id=current_user.id,
                title=form.title.data,
                content=form.content.data
            )
            db.session.add(post)
            db.session.commit()
            flash('post has published', 'success')
            return redirect(url_for('profile'))
        return render_template('create_post.html', form=form)

class PostEditView(MethodView):
    @login_required
    def get(self, post_id):
        post = Post.query.get_or_404(post_id)
        if post.user_id != current_user.id:
            abort(403)
        form = EditPostForm(obj=post)
        return render_template('edit_post.html', form=form, post=post)

    @login_required
    def post(self, post_id):
        post = Post.query.get_or_404(post_id)
        if post.user_id != current_user.id:
            abort(403)
        form = EditPostForm()
        if form.validate_on_submit():
            post.title = form.title.data
            post.content = form.content.data
            db.session.commit()
            flash('post has changed', 'success')
            return redirect(url_for('profile'))
        return render_template('edit_post.html', form=form, post=post)


class PostDeleteView(MethodView):
    @login_required
    def post(self, post_id):
        post = Post.query.get_or_404(post_id)
        if post.user_id != current_user.id:
            abort(403)
        db.session.delete(post)
        db.session.commit()
        flash('Пост удалён', 'success')
        return redirect(url_for('profile'))

class OAuthAuthorizeView(MethodView):
    def get(self, provider):
        if current_user.is_authenticated:
            return redirect(url_for('search'))
        client = oauth.create_client(provider)
        if not client:
            return redirect(url_for('login'))
        redirect_uri = url_for('oauth_callback', provider=provider, _external=True)
        return client.authorize_redirect(redirect_uri)

class OAuthCallbackView(MethodView):
    def get(self, provider):
        if current_user.is_authenticated:
            return redirect(url_for('search'))
        client = oauth.create_client(provider)
        if not client:
            return redirect(url_for('login'))
        token = client.authorize_access_token()
        email = None
        username = None

        if provider == 'github':
            resp = client.get('user', token=token)
            user_info = resp.json()
            email = user_info.get('email')
            if not email:
                emails_resp = client.get('user/emails', token=token)
                emails = emails_resp.json()
                primary = next((e for e in emails if e['primary']), None)
                email = primary['email'] if primary else None
            username = user_info.get('login')
            oauth_id = str(user_info['id'])

        elif provider == 'yandex':
            resp = client.get('info', token=token)
            user_info = resp.json()
            email = user_info.get('default_email')
            username = user_info.get('login')
            oauth_id = user_info.get('id')

        if not email:
            return redirect(url_for('login'))

        user = User.query.filter_by(oauth_provider=provider, oauth_id=oauth_id).first()
        if not user:
            user = User.query.filter_by(email=email).first()
            if user:
                user.oauth_provider = provider
                user.oauth_id = oauth_id
                db.session.commit()
            else:
                base_username = username or email.split('@')[0]
                unique_username = base_username
                suffix = 1
                while User.query.filter_by(username=unique_username).first():
                    unique_username = f"{base_username}{suffix}"
                    suffix += 1
                user = User(
                    username=unique_username,
                    email=email,
                    oauth_provider=provider,
                    oauth_id=oauth_id
                )
                db.session.add(user)
                db.session.commit()
                from models import Profile
                profile = Profile(user_id=user.id)
                db.session.add(profile)
                db.session.commit()
        login_user(user)
        flash(f'you entered via {provider.capitalize()}', 'success')
        return redirect(url_for('search'))

class AccountSettingsView(MethodView):
    @login_required
    def post(self):
        form = AccountSettingsForm()
        if form.validate_on_submit():
            if form.avatar.data:
                file = form.avatar.data
                filename = secure_filename(file.filename)
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ('.png', '.jpg', '.jpeg', '.gif'):
                    flash('use another format', 'danger')
                    return render_template('account_settings.html', form=form)

                avatar_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
                os.makedirs(avatar_dir, exist_ok=True)

                unique_name = f"avatar_{current_user.id}_{int(datetime.utcnow().timestamp())}{ext}"
                file_path = os.path.join(avatar_dir, unique_name)
                file.save(file_path)

                current_user.profile.avatar_url = f"uploads/avatars/{unique_name}"
                db.session.commit()
                flash('avatar changed', 'success')

            if form.new_password.data:
                if current_user.is_oauth_user:
                    current_user.set_password(form.new_password.data)
                else:
                    if not current_user.check_password(form.current_password.data):
                        flash('wrong current password', 'danger')
                        return render_template('account_settings.html', form=form)
                    current_user.set_password(form.new_password.data)

            if User.query.filter(User.email == form.email.data, User.id != current_user.id).first():
                flash('this email is using now', 'danger')
                return render_template('account_settings.html', form=form)
            if User.query.filter(User.username == form.username.data, User.id != current_user.id).first():
                flash('this user name is occupied', 'danger')
                return render_template('account_settings.html', form=form)

            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('settings saved', 'success')
            return redirect(url_for('account_settings'))
        return render_template('account_settings.html', form=form)