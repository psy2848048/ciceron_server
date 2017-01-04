# -*- coding: utf-8 -*-
from flask import Flask

from flask.ext.cors import CORS
from flask.ext.session import Session
from flask.ext.cache import Cache
from flask_oauth import OAuth

import i18nHandler.inject_api
import detourserverConnector.inject_api
from ciceron_lib import *
import requestwarehouse.inject_api
import groupRequest.inject_api
import requestResell.inject_api

if os.environ.get('PURPOSE') == 'PROD':
    DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"
else:
    DATABASE = "host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"

VERSION = '2.0'
DEBUG = True
BASEPATH = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER_RESULT = "translate_result"
MAX_CONTENT_LENGTH = 4 * 1024 * 1024
FACEBOOK_APP_ID = 256525961180911
FACEBOOK_APP_SECRET = 'e382ac48932308c15641803022feca13'
JSON_SORT_KEYS = False

SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = "CiceronCookie"
PERMANENT_SESSION_LIFETIME = timedelta(days=15)

ALLOWED_EXTENSIONS_PIC = set(['jpg', 'jpeg', 'png', 'tiff'])
ALLOWED_EXTENSIONS_DOC = set(['doc', 'hwp', 'docx', 'pdf', 'ppt', 'pptx', 'rtf'])
ALLOWED_EXTENSIONS_WAV = set(['wav', 'mp3', 'aac', 'ogg', 'oga', 'flac', '3gp', 'm4a'])
VERSION = "2015.11.15"

# CELERY_BROKER_URL = 'redis://localhost'

HOST = ""
if os.environ.get('PURPOSE') == 'PROD':
    HOST = 'http://ciceron.me'
    SESSION_COOKIE_DOMAIN = ".ciceron.me"
    
else:
    HOST = 'http://ciceron.xyz'
    SESSION_COOKIE_DOMAIN = ".ciceron.xyz"

SESSION_COOKIE_PATH = "/"

# APP setting
app = Flask(__name__)
app.secret_key = 'Yh1onQnWOJuc3OBQHhLFf5dZgogGlAnEJ83FacFv'
app.config.from_object(__name__)
app.project_number = 145456889576

# CORS
cors = CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": "true"}})

# Flask-Session
Session(app)

# Flask-Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Celery
# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)

# Flask-OAuth for facebook
oauth = OAuth()
facebook = oauth.remote_app('facebook',
                            base_url='https://graph.facebook.com/',
                            request_token_url=None,
                            access_token_url='/oauth/access_token',
                            authorize_url='https://www.facebook.com/dialog/oauth',
                            consumer_key=FACEBOOK_APP_ID,
                            consumer_secret=FACEBOOK_APP_SECRET,
                            request_token_params={'scope': 'email'}
                            )
date_format = "%Y-%m-%d %H:%M:%S.%f"
super_user = ["pjh0308@gmail.com", "admin@ciceron.me", "yysyhk@naver.com"]







if __name__ == '__main__':
    from gevent.wsgi import WSGIServer
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
