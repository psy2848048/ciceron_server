# -*- coding: utf-8 -*-
from flask import Flask

from flask_cors import CORS
from flask_session import Session
from flask_cache import Cache
from flask_oauth import OAuth
import psycopg2

try:
    from i18nHandler import I18nHandler
except:
    from .i18nHandler import I18nHandler

try:
    from detourserverConnector import Connector
except:
    from .detourserverConnector import Connector

try:
    from ciceron_lib import *
except:
    from .ciceron_lib import *

try:
    from requestwarehouse import Warehousing
except:
    from .requestwarehouse import Warehousing

try:
    from groupRequest import GroupRequest
except:
    from .groupRequest import GroupRequest

try:
    from requestResell import RequestResell
except:
    from .requestResell import RequestResell

try:
    from payment import Payment
except:
    from .payment import Payment

try:
    from localizer import LocalizerAPI
except:
    from .localizer import LocalizerAPI

try:
    from userControl import UserControlAPI
except:
    from .userControl import UserControlAPI


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

# CELERY_BROKER_URL = 'redis://localhost'

HOST = ""
if os.environ.get('PURPOSE') == 'PROD':
    HOST = 'http://ciceron.me'
    SESSION_COOKIE_DOMAIN = ".ciceron.me"
    SESSION_COOKIE_PATH = "/"
    
elif os.environ.get('PURPOSE') == 'DEV':
    HOST = 'http://ciceron.xyz'
    SESSION_COOKIE_DOMAIN = ".ciceron.xyz"
    SESSION_COOKIE_PATH = "/"

else:
    HOST = 'http://localhost'

# APP setting
app = Flask(__name__)
app.secret_key = 'Yh1onQnWOJuc3OBQHhLFf5dZgogGlAnEJ83FacFv'
app.config.from_object(__name__)
app.project_number = 145456889576

# CORS
cors = CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": "true"}})

# Flask-Session
Session(app)

ENDPOINTS = ['/api/v2']
LocalizerAPI(app, ENDPOINTS)
UserControlAPI(app, ENDPOINTS)

# Celery
# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)

date_format = "%Y-%m-%d %H:%M:%S.%f"
super_user = ["pjh0308@gmail.com", "admin@ciceron.me", "yysyhk@naver.com"]

def connect_db():
    """
    DB connector 함수
    """
    return psycopg2.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    """
    모든 API 실행 전 실행하는 부분. 여기서는 DB 연결.
    """
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    """
    모든 API 실행 후 실행하는 부분. 여기서는 DB 연결종료.
    """
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    from gevent.wsgi import WSGIServer
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
