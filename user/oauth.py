from flask import redirect, url_for, flash, session
from flask_login import login_user, current_user
from flask.views import MethodView

from oauth import oauth
from models import db, User
import uuid

class OAuthAuthorizeView(MethodView):
    def get(self, provider):
        if current_user.is_authenticated:
            return redirect(url_for('search'))
        client = oauth.create_client(provider)
        if not client:
            flash('Unknown provider', 'danger')
            return redirect(url_for('login'))
        redirect_uri = url_for('oauth_callback', provider=provider, _external=True)
        return client.authorize_redirect(redirect_uri)

class OAuthCallbackView(MethodView):
    def get(self, provider):
        if current_user.is_authenticated:
            return redirect(url_for('search'))
        client = oauth.create_client(provider)
        if not client:
            flash('Unknown provider', 'danger')
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
            flash('Couldnt get email', 'danger')
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
        flash(f'You signin via {provider.capitalize()}', 'success')
        return redirect(url_for('search'))