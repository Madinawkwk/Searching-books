import os
from authlib.integrations.flask_client import OAuth
import app

GITHUB_CLIENT_ID = os.environ.get('Ov23liTNAxHsm9gu0okL ') or 'your-github-client-id'
GITHUB_CLIENT_SECRET = os.environ.get('b874616b130622d1805447ff06a1c751c4f390b2') or 'your-github-client-secret'
YANDEX_CLIENT_ID = os.environ.get('YANDEX_CLIENT_ID') or 'your-yandex-client-id'
YANDEX_CLIENT_SECRET = os.environ.get('YANDEX_CLIENT_SECRET') or 'your-yandex-client-secret'

oauth = OAuth(app)


def configure_oauth(app):
    oauth.init_app(app)

    oauth.register(
        name='github',
        client_id='Ov23liTNAxHsm9gu0okL',
        client_secret='4731b7c782a076b30941c47699bff6520519366e',
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
        api_base_url='https://api.github.com',
        client_kwargs={'scope': 'user:email'},
    )

    oauth.register(
        name='yandex',
        client_id="cb9343e241364f17a7472dfe096eb324",
        client_secret="44f8e45350d34b408fda8b91f2386691",
        access_token_url='https://oauth.yandex.ru/token',
        authorize_url='https://oauth.yandex.ru/authorize',
        api_base_url='https://login.yandex.ru/',
        client_kwargs={'scope': 'login:email login:info'},
    )