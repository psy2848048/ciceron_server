# -*- coding: utf-8 -*-
"""
어플리케이션 서버 본 코드
URL rule과 Response가 정의되어 있음.

TODO: 이 파일에서는 Function call만 하고, Query 날리는 것은 모두 라이브러리화 시켜 서버 갈아타기 쉽게 하기
"""

from flask import Flask, session, redirect, escape, request, g, abort, json, flash, make_response, send_from_directory, url_for, send_file
from contextlib import closing
from datetime import datetime, timedelta
import hashlib, sqlite3, os, time, requests, sys, logging, io, argparse
#os.environ['DYLD_LIBRARY_PATH'] = '/usr/local/opt/openssl/lib'
""" Execute following first!!"""
""" export DYLD_LIBRARY_PATH='/usr/local/opt/openssl/lib' """

import psycopg2
from functools import wraps
from werkzeug import secure_filename
from decimal import Decimal
from i18nHandler import I18nHandler
from ciceron_lib import *
from requestwarehouse import Warehousing
from flask.ext.cors import CORS
from flask.ext.session import Session
from multiprocessing import Process
from flask.ext.cache import Cache
from flask_oauth import OAuth

#DATABASE = '../db/ciceron.db'
DATABASE = None
#parser = argparse.ArgumentParser(description='Translation agent')
#parser.add_argument('--dbpass', dest='dbpass', help='DB password')
#args = parser.parse_args()

if os.environ.get('PURPOSE') == 'PROD':
    DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"
else:
    DATABASE = "host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"

VERSION = '1.1'
DEBUG = True
BASEPATH = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER_RESULT = "translate_result"
MAX_CONTENT_LENGTH = 4 * 1024 * 1024
FACEBOOK_APP_ID = 256525961180911
FACEBOOK_APP_SECRET = 'e382ac48932308c15641803022feca13'

SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = "CiceronCookie"
PERMANENT_SESSION_LIFETIME = timedelta(days=15)

ALLOWED_EXTENSIONS_PIC = set(['jpg', 'jpeg', 'png', 'tiff'])
ALLOWED_EXTENSIONS_DOC = set(['doc', 'hwp', 'docx', 'pdf', 'ppt', 'pptx', 'rtf'])
ALLOWED_EXTENSIONS_WAV = set(['wav', 'mp3', 'aac', 'ogg', 'oga', 'flac', '3gp', 'm4a'])
VERSION= "2015.11.15"

#CELERY_BROKER_URL = 'redis://localhost'

HOST = ""
if os.environ.get('PURPOSE') == 'PROD':
    HOST = 'http://ciceron.me'
else:
    HOST = 'http://ciceron.xyz'

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
#celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
#celery.conf.update(app.config)

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

def pic_allowed_file(filename):
    """
    확장자를 보고 사진(그림)인지 아닌지 판별
    :param string filename: 파일 이름
    """
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_PIC']

def doc_allowed_file(filename):
    """
    확장자를 보고 문서인지 아닌지 판별
    :param string filename: 파일 이름
    """
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_DOC']

def sound_allowed_file(filename):
    """
    확장자를 보고 음성인지 아닌지 판별
    :param string filename: 파일 이름
    """
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_WAV']

def connect_db():
    """
    DB connector 함수
    """
    return psycopg2.connect(app.config['DATABASE'])

################################################################################
#########                     MAIN APPLICATION                         #########
################################################################################

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

@facebook.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

@app.route('/api', methods=['GET'])
#@exception_detector
@cache.cached(timeout=50, key_prefix='loginStatusCheck')
def loginCheck():
    """
    해당 세션의 상태를 보여준다.
    아래 return값은 session[var_name]으로 접근 가능하다

    :returns JSON response
        useremail: 로그인한 유저의 이메일주소. 로그인 상태 아니면 null
        isLoggedIn: 로그인 여부 True/False
        isTranslator: 로그인한 유저의 번역가여부 True/False
    """
    if 'useremail' in session:
        client_os = request.args.get('client_os', None)
        isTranslator = translator_checker_plain(g.db, session['useremail'])
        #if client_os is not None and registration_id is not None:
        #    check_and_update_reg_key(g.db, client_os, registration_id)
        #    g.db.coomit()

        return make_response(json.jsonify(
            useremail=session['useremail'],
            isLoggedIn = True,
            isTranslator=isTranslator,
            message="User %s is logged in" % session['useremail'])
            , 200)
    else:
        return make_response(json.jsonify(
            useremail=None,
            isLoggedIn=False,
            isTranslator=False,
            message="No user is logged in")
            , 403)

@app.route('/api/login', methods=['POST', 'GET'])
#@exception_detector
def login():
    """
    로그인 함수

    로그인 로직
        1. GET /api/login에 접속
        2. 로그인 Salt를 받는다.
        3. 클라이언트에서는 sha256(salt + sha256(password) + salt) 값을 만들어 서버에 전송한다.
        4. Password 테이블 값과 비교하여 일치하면 session 값들을 고쳐준다.

    GET
        No parameter

    POST
        :param string email: 유저 email 주소 (ciceron_lib.get_user_id를 통하여 email에서 user_id를 추출할 수 있다.)
        :param string password: 3번 참조
    """
    if request.method == "POST":
        # Parameter
        #     email:        E-mail ID
        #     password:     password
        #     client_os:    := Android, iPhone, Blackberry, web.. (OPTIONAL)
        #     machine_id:   machine_id of client phone device (OPTIONAL)

        # Get parameters
        parameters = parse_request(request)
        email = parameters['email']
        hashed_password = parameters['password']
        #machine_id = parameters.get('machine_id', None)
        #client_os = parameters.get('client_os', None)
        user_id = get_user_id(g.db, email)

        # Get hashed_password using user_id for comparing
        cursor = g.db.cursor()
        cursor.execute("SELECT hashed_pass FROM CICERON.PASSWORDS WHERE user_id = %s", (user_id, ))
        rs = cursor.fetchall()

        if len(rs) > 1:
            # Status code 500 (ERROR)
            # Description: Same e-mail address tried to be inserted into DB
            return make_response (json.jsonify(message='Constraint violation error!'), 501)

        elif len(rs) == 0:
            # Status code 403 (ERROR)
            # Description: Not registered
            return make_response (json.jsonify(message='Not registered %s' % email), 403)
        
        elif len(rs) == 1 and get_hashed_password(str(rs[0][0]), session['salt']) == hashed_password:
            # Status code 200 (OK)
            # Description: Success to log in
            isTranslator = translator_checker_plain(g.db, email)
            session['logged_in'] = True
            session['useremail'] = email
            session['isTranslator'] = isTranslator
            session.pop('salt', None)
        
            #if client_os is not None and registration_id is not None:
            #    check_and_update_reg_key(g.db, client_os, registration_id)
        
            return make_response(json.jsonify(
                message='Logged in',
                isTranslator=isTranslator,
                email=email)
                , 200)

        else:
            # Status code 406 (ERROR)
            # Description: Password incorrect
            return make_response(json.jsonify(
                message='Please check the password'
                ), 403)

        return

    else:
        salt = random_string_gen()
        session['salt'] = salt
        return make_response(json.jsonify(identifier=salt), 200)

@app.route("/api/facebook_login")
def facebook_auth():
    return facebook.authorize(callback=url_for('facebook_authorized', is_signUp='N', _external=True))

@app.route("/api/facebook_signUpCheck")
def facebook_signUpCheck():
    return facebook.authorize(callback=url_for('facebook_authorized', is_signUp='Y', _external=True))

@app.route("/api/facebook_authorized")
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None or 'access_token' not in resp:
        return make_response(json.jsonify(
            message="No access token from facebook"), 403)

    session['facebook_token'] = (resp['access_token'], '')
    user_data = facebook.get('/me').data

    # Login with facebook
    if request.args.get('is_signUp') == 'N':
        facebook_id, user_id = get_facebook_user_id(g.db, user_data['email'])
        if facebook_id == -1:
            return make_response(json.jsonify(
                message='No user signed up with %s' % user_data['email']
                ), 403)

        session['logged_in'] = True
        session['useremail'] = get_user_email(g.db, user_id[1])

        return make_response(json.jsonify(
            show_signUpView=False,
            is_alreadySignedUp=None,
            email=None,
            user_name=None), 200)

    # SignUp with facebook
    elif request.args.get('is_signUp') == 'Y':
        facebook_id, _ = get_facebook_user_id(g.db, user_data['email'])
        # Defence duplicated facebook ID signing up
        if facebook_id != -1:
            return make_repsonse(json.jsonify(
                message="You already signed up on facebook"), 403)

        user_id = get_user_id(g.db, user_data['email'])
        if user_id == -1:
            return make_response(json.jsonify(
                show_signUpView=True,
                is_alreadySignedUp=False,
                email=user_data['email'],
                user_name=user_data['name']), 200)
        else:
            new_facebook_id = get_new_id(g.db, "D_FACEBOOK_USERS")
            g.db.execute("INSERT INTO CICERON.D_FACEBOOK_USERS VALUES (%s,%s,%s) ",
                    (new_facebook_id, user_data['email'], user_id))
            g.db.commit()
            return make_response(json.jsonify(
                show_signUpView=True,
                is_alreadySignedUp=True,
                email=user_data['email'],
                user_name=user_data['name']), 200)

@app.route("/api/facebook_connectUser", methods=["GET"])
@facebook.authorized_handler
def facebook_connectUser(resp):
    parameters = parse_request(request)
    email = parameters['email']
    user_id = get_user_id(g.db, email)

    if facebook.get('/me').data['email'] != email:
        return make_response(json.jsonify(
            message="DO NOT HACK!!!!"), 403)

    if user_id == -1:
        return make_response(json.jsonify(
            message="Not registered as normal user"), 403)

    new_facebook_id = get_new_id(g.db, "D_FACEBOOK_USERS")
    g.db.execute("INSERT INTO CICERON.D_FACEBOOK_USERS VALUES (%s,%s,%s) ",
            (new_facebook_id, email, user_id))
    g.db.commit()

    return make_response(json.jsonify(
        message="Successfully connected with facebook ID"), 200)

@app.route("/api/facebook_signUp", methods=["POST"])
@facebook.authorized_handler
def facebook_signUp(resp):
    parameters = parse_request(request)
    email = parameters['email']
    # OAuth hacking check
    if facebook.get('/me').data['email'] != email:
        return make_response(json.jsonify(
            message="DO NOT HACK!!!!"), 403)

    hashed_password = parameters['password']
    name = (parameters['name']).encode('utf-8')
    mother_language_id = int(parameters['mother_language_id'])
    nationality_id = int(parameters['nationality_id'])
    residence_id = int(parameters['residence_id'])
    result = signUpQuick(g.db, email, hashed_password, name, mother_language_id, nationality_id, residence_id, external__service_provider=["facebook"])

    if result == 200:
        return make_response(json.jsonify(message="Registration %s: successful" % email), 200)
    elif result == 412:
        return make_response(json.jsonify(
            message="ID %s is duplicated. Please check the email." % email), 412)

@app.route('/api/logout', methods=["GET"])
#@exception_detector
def logout():
    """
    로그아웃 함수
        - session에 들어있는 모든 키 제거
    """
    # No parameter needed
    if session['logged_in'] == True:
        cache.clear()
        username_temp = session['useremail']
        session.pop('logged_in', None)
        session.pop('useremail', None)
        # Status code 200 (OK)
        # Logout success
        return make_response(json.jsonify(
                   message = "Logged out",
                   email=username_temp
               ), 200)
    else:
        # Status code 403 (ERROR)
        # Description: Not logged in yet
        return make_response(json.jsonify(
                   message = "You've never logged in"
               ), 403)

@app.route('/api/signup', methods=['POST', 'GET'])
#@exception_detector
def signup():
    """
    회원가입 함수
    
    :param string email: 회원 email
    :param string password: sha256(password) 전송. Salt 없음
    :param string name: 이름
    :param int mother_tongue_id: 모국어 ID. ID-언어 대응은 원노트 참고

    핵심 동작 함수: ciceron_lib.signUpQuick()
    """

    if request.method == 'POST':
        # Get parameter values
        parameters = parse_request(request)
        email = parameters['email']
        hashed_password = parameters['password']
        name = (parameters['name']).encode('utf-8')
        if 'mother_language_id' in parameters:
            mother_language_id = int(parameters['mother_language_id'])
        else:
            return make_response(json.jsonify(message="Some parameters are missing"), 400)

        nationality_id = int(parameters.get('nationality_id')) if parameters.get('nationality_id') != None else None
        residence_id = int(parameters.get('residence_id')) if parameters.get('residence_id') != None else None

        status = signUpQuick(g.db, email, hashed_password, name, mother_language_id, nationality_id, residence_id)

        # Status code 200 (OK)
        # Description: Signed up successfully
        if status == 200:
            return make_response(json.jsonify(
                message="Registration successful",
                email=email
                ), 200)
        elif status == 412:
            return make_response(json.jsonify(message="Duplicate email: %s" % email), 412)
    
        elif status == 417:
            return make_response(json.jsonify(
                message="'%s' is not email" % email,
                email=email
                ), 417)
    return '''
        <!doctype html>
        <title>Sign up</title>
        <h1>Sign up</h1>
        <form action="" method="post">
      <p>ID: <input type=text name="email"></p>
      <p>Pass: <input type=password name="password"></p>
      <p>Name: <input type=text name="name"></p>
      <p>Mother language setting: <input type=text name="mother_language_id"></p>
          <p><input type=submit value="Sign up!"></p>
        </form>
        '''

@app.route('/api/idCheck', methods=['POST'])
#@exception_detector
def idChecker():
    """
    ID 중복조회

        CICERON.D_USERS에 중복된 이메일주소가 있는지 살펴본다.
    """
    cursor = g.db.cursor()

    # Method: GET
    # Parameter: String id
    parameters = parse_request(request)
    email = parameters['email']
    print "email_id: %s" % email
    cursor.execute("select id from CICERON.D_USERS where email = %s", (email, ))
    check_data = cursor.fetchall()
    if len(check_data) == 0:
        # Status code 200 (OK)
        # Description: Inputted e-mail ID is available
        return make_response(json.jsonify(
            message="You may use the ID %s" % email,
            email=email), 200)
    else:
        # Status code 400 (BAD)
        # Description: Inputted e-mail ID is duplicated with other's one
        return make_response(json.jsonify(
            message="Duplicated ID '%s'" % email,
            email=email), 400)

@app.route('/api/user/create_recovery_code', methods=['POST'])
#@exception_detector
def create_recovery_code():
    """
    패스워드 잊어버렸을 때 가입한 이메일로 복구 코드 전송
    담당하는 테이블: CICERON.EMERGENCY_CODE
    로직
        1. 유저 이름 받아옴 (핵심은 아니고, 이메일 보낼 때, Dear xx할 때 넣을 이름 조회 목적..)
        2. ciceron_lib.random_string_gen을 이용하여 랜덤 스트링 12자리로 이루어진 복구 코드를 받아옴
        3. UPDATE OR INSERT 복구코드
        4. 복구코드 이메일로 전송

    1 유저당 1레코드만 허용
    """
    cursor = g.db.cursor()

    parameters = parse_request(request)
    email = parameters['email']

    user_id = get_user_id(g.db, email)
    if user_id == -1:
        return make_response(json.jsonify(
            message="No user exists: %s" % email), 400)

    cursor.execute("SELECT name FROM CICERON.D_USERS WHERE id = %s ", (user_id, ))
    user_name = cursor.fetchall()[0][0]

    recovery_code = random_string_gen(size=12)
    hashed_code = get_hashed_password(recovery_code)
    query_insert_emergency="""
        WITH "RECOV_UPDATE" AS (
            UPDATE CICERON.EMERGENCY_CODE SET code = %s
                WHERE user_id = %s RETURNING *
        )
        INSERT INTO CICERON.EMERGENCY_CODE (user_id, code)
        SELECT %s, %s WHERE NOT EXISTS (SELECT * FROM "RECOV_UPDATE")
        """
    cursor.execute(query_insert_emergency, (hashed_code, user_id, user_id, hashed_code))
    g.db.commit()

    subject = "Here is your temporary password"
    message="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Here is your recovery code:<br>
                 <br>
                 <br>
                 <h2><b>%(password)s</b></h2>
                 <br>
                 <br>
                 Please input the code above to <a href="%(page)s">this page.</a><br>
                 Have a secure day! :)<br>
                 <br>
                 Best regards,<br>
                 Ciceron team""" % {
                         'user': user_name,
                         'password': recovery_code,
                         'page': HOST,
                         "host": HOST + ':5000'
                         }

    send_mail(email, subject, message)

    return make_response(json.jsonify(
        message="Password recovery code is issued for %s" % email), 200)

@app.route('/api/user/recover_password', methods=['POST'])
#@exception_detector
def recover_password():
    """
    복구 코드를 받아 패스워드 재설정하는 부분

    로직
        1. 해당 ID의 복구코드 조회
        2. 새 패스워드 중 패스워드가 아무것도 없는 빈 스트링인 경우 막기 위하여 elif에서 빈 스트링에 대한 hash값은 빠꾸처리
        3. 패스워드 변경 후 복구 코드는 비움.
    """
    cursor = g.db.cursor()
    parameters = parse_request(request)
    email = parameters['email']
    hashed_code = parameters['code']
    hashed_new_password = parameters['new_password']
    user_id = get_user_id(g.db, email)

    # Get hashed_password using user_id for comparing
    cursor.execute("SELECT code FROM CICERON.EMERGENCY_CODE where user_id = %s ", (user_id, ))
    rs = cursor.fetchall()

    if len(rs) > 1:
        # Status code 500 (ERROR)
        # Description: Same e-mail address tried to be inserted into DB
        return make_response (json.jsonify(message='Constraint violation error!'), 501)

    elif str(hashed_new_password) == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855':
        return make_response(json.jsonify(message='Need password'), 405)

    elif len(rs) == 1 and str(rs[0][0]) == hashed_code:
        cursor.execute("UPDATE CICERON.PASSWORDS SET hashed_pass = %s WHERE user_id = %s ", (hashed_new_password, user_id))
        cursor.execute("UPDATE CICERON.EMERGENCY_CODE SET code = null WHERE user_id = %s ", (user_id, ))
        g.db.commit()
        return make_response (json.jsonify(message='Password successfully changed for user %s' % email), 200)

    else:
        return make_response (json.jsonify(message='Security code incorrect!'), 403)

@app.route('/api/user/change_password', methods=['POST'])
@login_required
#@exception_detector
def change_password():
    """
    패스워드 변경

    로직
        1. 현재 패스워드의 sha256 값 불러와서 비교
        2. 일치하면 새로운 패스워드의 sha256값 엎어치기
    """
    cursor = g.db.cursor()

    parameters = parse_request(request)
    email = session['useremail']
    hashed_old_password = parameters['old_password']
    hashed_new_password = parameters['new_password']
    user_id = get_user_id(g.db, email)

    # Get hashed_password using user_id for comparing
    cursor.execute("SELECT hashed_pass FROM CICERON.PASSWORDS where user_id = %s ", (user_id, ))
    rs = cursor.fetchall()

    if len(rs) > 1:
        # Status code 500 (ERROR)
        # Description: Same e-mail address tried to be inserted into DB
        return make_response(json.jsonify(message='Constraint violation error!'), 501)

    elif str(hashed_new_password) == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855':
        return make_response(json.jsonify(message='Need password'), 405)

    elif len(rs) == 1 and str(rs[0][0]) == hashed_old_password:
        cursor.execute("UPDATE CICERON.PASSWORDS SET hashed_pass = %s WHERE user_id = %s ", (hashed_new_password, user_id))
        g.db.commit()
        return make_response(json.jsonify(message='Password successfully changed for user %s' % email), 200)

    else:
        return make_response(json.jsonify(message='Old password of user %s is incorrect!' % email), 403)

@app.route('/api/user/profile', methods = ['GET', 'POST'])
@login_required
#@exception_detector
def user_profile():
    """
    프로파일 조회 API (GET), 정보 업데이트 API (POST)

    1) GET
        응답 정보는 원노트 조회 요망

        엥간한 유저 정보: CICERON.D_USERS
        일반 유저의 적립금 정보: CICERON.REVENUE  (뜻은 안 맞지만... 이전 설계때문에 이리 되었으니 참아주세요 ㅜㅜ)
        번역가 유저의 수당 정보: CICERON.RETURN_POINT

        GET으로 불러올 때 ?user_email=<other_user_email> 파라미터로 다른 유저 정보를 조회해올 수 있음
        이 때에는, 다른 유저의 포인트 및 적립금은 -65535로 마스킹됨.

    2) POST
        프로필 소개글이나 프로필 사진 변경가능
        프로필 사진 올릴 때에는 Content-Type을 JSON이나 www-urlencode말고, multipart/form-data로 업로드하기 바람

        프로파일 사진 바이너리는 CICERON.F_USER_PROFILE_PIC 에 저장됨. 서버에 물리 파일로 저장하지 않음에 유의.
        API 경로랍시고 profile_pic_path에 스트링 넣긴 하지만, 의미없음.
    """
    if request.method == 'GET':
        # Method: GET
        # Parameters
        #     user_email: String, text
        # Get value
        email = request.args.get('user_email', session['useremail'])
        user_id = get_user_id(g.db, email)

        # Start logic
        cursor = g.db.cursor()
        cursor.execute("SELECT * FROM CICERON.D_USERS WHERE id = %s", (user_id, ))
        userinfo = cursor.fetchall()

        # Unique constraint check
        if len(userinfo) > 1:
            return make_response(json.jsonify(
                message = "More than 2 records for one ID! Internal server error!"),
                500)

        # Filter if there is no information with the given ID
        elif len(userinfo) == 0:
            return make_response(json.jsonify(
                message = "Please check the input ID: %s" % email),
                400)

        # ID check: Are you requesting yours, or others?
        #     Yours -> show including points
        #     Others-> show except points
        is_your_profile = None
        if email == session['useremail']: is_your_profile = True
        else:                             is_your_profile = False

        # Update statistics
        update_user_record(g.db, client_id=user_id, translator_id=user_id)

        profile = getProfile(g.db, user_id)
        if is_your_profile == True and profile['user_isTranslator'] == True:
            cursor.execute("SELECT amount FROM CICERON.REVENUE WHERE id = %s",  (user_id, ))
            profile['user_point'] = cursor.fetchone()[0]

        elif is_your_profile == True and profile['user_isTranslator'] == False:
            cursor.execute("SELECT amount FROM CICERON.RETURN_POINT WHERE id = %s",  (user_id, ))
            profile['user_point'] = cursor.fetchone()[0]

        else:
            profile['user_point'] = -65535

        return make_response(json.jsonify(profile), 200)

    elif request.method == "POST":
        # Method: GET
        # Parameters
        #     user_email: String, text
        #     user_profilePic: binary
        cursor = g.db.cursor()

        # Get parameter value
        parameters = parse_request(request)

        profileText = parameters.get('user_profileText', None)
        profile_pic = request.files.get('user_profilePic', None)
        pic_path = None

        # Start logic
        # Get user number
        user_id = get_user_id(g.db, session['useremail'])

        # Profile text update
        if profileText != None:
            cursor.execute("UPDATE CICERON.D_USERS SET profile_text = %s WHERE id = %s ", (profileText, user_id))

        # Profile photo update
        filename = ""
        path = ""
        if profile_pic and pic_allowed_file(profile_pic.filename):
            extension = profile_pic.filename.split('.')[-1]
            filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + '.' + extension
            pic_path = os.path.join("profile_pic", str(user_id), filename)

            cursor.execute("UPDATE CICERON.D_USERS SET profile_pic_path = %s WHERE id = %s ", (pic_path, user_id))
            profile_pic_bin = profile_pic.read()
            query_insert = """
                WITH "UPDATE_PROFILE_PIC" AS (
                    UPDATE CICERON.F_USER_PROFILE_PIC SET filename = %s, bin = %s
                        WHERE user_id = %s RETURNING *
                )
                INSERT INTO CICERON.F_USER_PROFILE_PIC (user_id, filename, bin)
                SELECT %s, %s, %s WHERE NOT EXISTS (SELECT * FROM "UPDATE_PROFILE_PIC")
                """
            cursor.execute(query_insert, (filename, bytearray(profile_pic_bin), user_id, user_id, filename, bytearray(profile_pic_bin)))

        #if is_translator:
        #    g.db.execute("UPDATE D_USERS SET is_translator = ? WHERE email = ?", [is_translator, buffer(session['useremail'])])

        g.db.commit()
        return make_response(json.jsonify(
            message="Your profile is susccessfully updated!",
            user_profileText=profileText,
            user_profilePicPath=pic_path), 200)

@app.route('/api/user/profile/keywords/<keyword>', methods = ['GET', 'POST', 'DELETE'])
@login_required
#@exception_detector
def user_keywords_control(keyword):
    """
    프로파일에서 자신을 표현할 수 있는 키워드 기 입력된 키워드에서 검색(GET), 추가(POST), 및 삭제(DELETE)
    1) GET
        <keyword>에 집어 넣은 글자를 처음으로 하는, 기 입력된 키워드를 조회하여 후보를 보여준다.
        키워드 입력시, 연관검색어를 제공하고자 함이다.

    2) POST
        <keyword>를 입력한다.
        Keyword Dimension table: CICERON.D_KEYWORDS
        Keyword Fact table: CICERON.D_USER_KEYWORDS

        기 입력된 키워드면 키워드ID를 찾아서 유저별로 Mapping한다.
        기존에 입력된 키워드가 아니라면 Dimension table에 INSERT한다.

    3) DELETE
        해당 유저의 키워드에서 입력된 <keyword>를 삭제한다.
        Dimension table의 레코드는 건드리지 않고, Fact table에 적혀있는 mapping만 지운다.

    """
    if request.method == "POST":
        cursor = g.db.cursor()

        if "%%2C" in keyword or ',' in keyword:
            return make_response(json.jsonify(
                message="No commna(',') in keyword"), 400)

        keyword_id = get_id_from_text(g.db, keyword, "D_KEYWORDS")
        if keyword_id == -1:
            keyword_id = get_new_id(g.db, "D_KEYWORDS")
            cursor.execute("INSERT INTO CICERON.D_KEYWORDS VALUES (%s,%s)", (keyword_id, keyword) )

        user_id = get_user_id(g.db, session['useremail'])
        cursor.execute("INSERT INTO CICERON.D_USER_KEYWORDS VALUES (%s,%s)", (user_id, keyword_id))
        g.db.commit()

        return make_response(json.jsonify(
            message="Keyword '%s' is inserted into user %s" % (keyword, session['useremail'])),
            200)

    elif request.method == "DELETE":
        cursor = g.db.cursor()

        user_id = get_user_id(g.db, session['useremail'])
        keyword_id = get_id_from_text(g.db, keyword, "D_KEYWORDS")
        cursor.execute("DELETE FROM CICERON.D_USER_KEYWORDS WHERE user_id = %s AND keyword_id = %s", (user_id, keyword_id))
        g.db.commit()

        return make_response(json.jsonify(
            message="Keyword '%s' is deleted from user %s" % (keyword, session['useremail'])),
            200)

    elif request.method == "GET":
        cursor = g.db.cursor()

        cursor.execute("""SELECT id, text FROM CICERON.D_KEYWORDS WHERE text like '%s%%' """ % keyword)
        similar_keywords = [str(item[1]) for item in cursor.fetchall()]
        return make_response(json.jsonify(
            message="Similarity search results",
            result=similar_keywords), 200)

@app.route('/api/requests', methods=["POST"])
#@exception_detector
def requests():
    """
    번역물 의뢰 API

    로직
        1. 로그인 판별
        2. CICERON.F_REQUEST의 새로운 ID따기 (ciceron_lib.get_new_id() 사용)
        3. 여러 파라미터 받아옴 (원노트 API 문서 참고)
        4. 텍스트, 사진, 음성, 문서, i18n 등등의 형식에 따라 후처리
        5. 단문 번역의 경우, isSos = True, 이 경우에는 결제와 상관없이 is_paid = True
        6. 일반 의뢰의 경우, isSos = False, 이 경우에는 결제 진행해야 리스트에 보이게 해야 하므로, is_paid = False
        7. splitTrans는 번역 공동구매 여부 선택. is_sound, is_text, is_doc 의 true/false와는 독립적이다.
    """
    if request.method == "POST":
        if session.get('useremail') == None or session.get('useremail') == False:
            return make_response(json.jsonify(
                status_code = 403,
                message="Not logged in"), 403)

        # Method: POST
        # Parameters -> Please check code
        cursor = g.db.cursor()
        parameters = parse_request(request)

        request_id = get_new_id(g.db, "F_REQUESTS")
        client_user_id = get_user_id(g.db, parameters['request_clientId'])
        original_lang_id = parameters['request_originalLang']
        target_lang_id = parameters['request_targetLang']
        isSos = parameter_to_bool(parameters['request_isSos'])
        format_id = parameters.get('request_format')
        subject_id = parameters.get('request_subject')
        is_text = parameter_to_bool(parameters.get('request_isText', False))

        if parameters.get('request_text', None) != None:
            text_string = parameters.get('request_text')
        else:
            text_string = None

        is_photo = parameter_to_bool(parameters.get('request_isPhoto', False))
        is_sound = parameter_to_bool(parameters.get('request_isSound', False))
        is_file = parameter_to_bool(parameters.get('request_isFile', False))
        is_i18n = parameter_to_bool(parameters.get('request_isI18n', False))
        is_movie = parameter_to_bool(parameters.get('request_isMovie', False))
        is_splitTrans = parameter_to_bool(parameters.get('request_isSplitTrans', False))

        if isSos == False:
            delta_from_due = int(parameters['request_deltaFromDue'])
        else:
            delta_from_due = 360 * 60

        point = float(parameters.get('request_points')) if isSos == False else 0
        context = parameters.get('request_context')

        new_photo_id = None
        new_sound_id = None
        new_file_id = None
        new_text_id = None
        is_paid = True if isSos == True else False

        if isSos == False and (original_lang_id == 500 or target_lang_id == 500):
            return make_response(json.jsonify(
                message="The language you requested is not yet registered. SOS request only"
                ), 204)

        if isSos == True and len(text_string) > 140:
            return make_response(json.jsonify(
                message="Too long text for sos request",
                length=len(text_string)
                ), 417)

        # Upload binaries into file and update each dimension table
        if (request.files.get('request_photo') != None):
            binary = request.files['request_photo']
            filename = ""
            path = ""
            new_photo_id = get_new_id(g.db, "D_REQUEST_PHOTOS")
            if pic_allowed_file(binary.filename):
                extension = binary.filename.split('.')[-1]
                filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + '.' + extension
                path = os.path.join("request_pic", str(new_photo_id), filename)

            photo_bin = binary.read()
            cursor.execute("INSERT INTO CICERON.D_REQUEST_PHOTOS (id, path, bin) VALUES (%s,%s,%s)", (new_photo_id, path, bytearray(photo_bin) ) )

        if (request.files.get('request_sound') != None):
            binary = request.files['request_sound']
            filename = ""
            path = ""
            new_sound_id = get_new_id(g.db, "D_REQUEST_SOUNDS")
            if sound_allowed_file(binary.filename):
                extension = binary.filename.split('.')[-1]
                filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + '.' + extension
                path = os.path.join("request_sounds", str(new_sound_id), filename)

            sound_bin = binary.read()
            cursor.execute("INSERT INTO CICERON.D_REQUEST_SOUNDS (id, path, bin) VALUES (%s,%s,%s)", (new_sound_id, path, bytearray(sound_bin) ) )
        
        if (request.files.get('request_file') != None):
            binary = request.files['request_file']
            filename = ""
            path = ""
            new_file_id = get_new_id(g.db, "D_REQUEST_FILES")
            if doc_allowed_file(binary.filename):
                extension = binary.filename.split('.')[-1]
                filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + '.' + extension
                path = os.path.join("request_doc", str(new_file_id), filename)

            file_bin = binary.read()
            cursor.execute("INSERT INTO CICERON.D_REQUEST_FILES (id, path, bin) VALUES (%s,%s,%s)", (new_file_id, path, bytearray(file_bin) ) )

            ############ Documentfile 2 TEXT ##################

            if (binary.filename).endswith('.docx'):
                from docx import Document
                try:
                    doc = Document(file_bin)
                    text_string = ('\n').join([ paragraph.text for paragraph in doc.paragraphs ])
                    print "DOCX file is converted into text."
                except Exception as e:
                    print "DOCX Error. Skip."
                    pass

            elif (binary.filename).endswith('.pdf'):
                import slate
                try:
                    doc = slate.PDF(file_bin)
                    text_string = ('\n\n').join(doc)
                except Exception as e:
                    print "PDF Error. Skip"
                    pass

            ##################################################

        if is_i18n == True:
            i18nObj = I18nHandler(g.db)
            i18n_file_format = parameters.get('request_i18nFileFormat')
            i18n_binary = request.files['request_i18nFileBinary']

            try:
                if i18n_file_format == 'android':
                    i18nObj.androidToDb(request_id, i18n_binary)
                elif i18n_file_format == 'json':
                    i18nObj.jsonToDb(request_id, original_lang_id, i18n_binary)
                elif i18n_file_format == 'iOS':
                    i18nObj.iosToDb(request_id, i18n_binary)
                elif i18n_file_format == 'xamarin':
                    i18nObj.xamarinToDb(request_id, i18n_binary)
                elif i18n_file_format == 'unity':
                    i18nObj.unityToDb(request_id, original_lang_id, i18n_binary)

            except Exception:
                g.db.rollback()
                return make_response(json.jsonify(
                    message="Something wrong in your file"), 413)

        new_translation_id = None
        if text_string and is_i18n == False and is_movie == False:
            filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + ".txt"
            new_text_id = get_new_id(g.db, "D_REQUEST_TEXTS")
            new_translation_id = get_new_id(g.db, "D_TRANSLATED_TEXT")
            path = os.path.join("request_text", str(new_text_id), filename)
            #cursor.execute("INSERT INTO CICERON.D_REQUEST_TEXTS (id, path, text) VALUES (%s,%s,%s)", (new_text_id, path, text_string))
            warehousing = Warehousing(g.db)
            warehousing.store(new_text_id, path, text_string, new_translation_id, original_lang_id, target_lang_id)

        # Input context text into dimension table
        new_context_id = get_new_id(g.db, "D_CONTEXTS")
        cursor.execute("INSERT INTO CICERON.D_CONTEXTS VALUES (%s,%s)", (new_context_id, context))

        cursor.execute("""INSERT INTO CICERON.F_REQUESTS
            (id, client_user_id, original_lang_id, target_lang_id, isSOS, status_id, format_id, subject_id, queue_id, ongoing_worker_id, is_text, text_id, is_photo, photo_id, is_file, file_id, is_sound, sound_id, client_completed_group_id, translator_completed_group_id, client_title_id, translator_title_id, registered_time, due_time, points, context_id, comment_id, tone_id, translatedText_id, is_paid, is_need_additional_points, is_i18n, is_movie, is_splitTrans, is_docx)
                VALUES
                (%s,%s,%s,%s,%s,
                 %s,%s,%s,%s,%s,
                 %s,%s,%s,%s,%s,
                 %s,%s,%s,%s,%s,
                 %s,%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + interval '%s seconds', %s,
                 %s,%s,%s,%s,%s,
                 %s,%s,%s,%s,%s)""", 
            (
                    request_id,                       # id
                    client_user_id,                   # client_user_id
                    original_lang_id,                 # original_lang_id
                    target_lang_id,                   # target_lang_id
                    isSos,                            # isSOS
                    0,                    # status_id
                    format_id,            # format_id
                    subject_id,           # subject_id
                    None,                 # queue_id
                    None,                 # ongoing_worker_id
                    is_text,     # is_text
                    new_text_id,          # text_id
                    is_photo,             # is_photo
                    new_photo_id,         # photo_id
                    is_file,              # is_file
                    new_file_id,          # file_id
                    is_sound,             # is_sound
                    new_sound_id,         # sound_id
                    None,                 # client_completed_group_id
                    None,                 # translator_completed_group_id
                    None,                 # client_title_id
                    None,                 # translator_title_id
                    delta_from_due,       # due_time
                    point,                # points
                    new_context_id,       # context_id
                    None,                 # comment_id
                    None,                 # tone_id
                    new_translation_id,                 # translatedText_id
                    is_paid,              # is_paid
                    False,                # is_need_additional_points
                    is_i18n,
                    is_movie,
                    is_splitTrans,
                    is_docx,
             )
        )

        g.db.commit()
        update_user_record(g.db, client_id=client_user_id)

        # Notification for SOS request
        if isSos == True:
            rs = pick_random_translator(g.db, 10, original_lang_id, target_lang_id)
            for item in rs:
                store_notiTable(g.db, item[0], 1, None, request_id)
                #regKeys_oneuser = get_device_id(g.db, item[0])

                #message_dict = get_noti_data(g.db, 1, item[0], request_id)
                #if len(regKeys_oneuser) > 0:
                #    gcm_noti = gcm_server.send(regKeys_oneuser, message_dict)

        g.db.commit()

        return make_response(json.jsonify(
            message="Request has been posted!",
            user_email=parameters['request_clientId'],
            request_id=request_id), 200)

@app.route('/api/user/translations/stoa', methods=["GET"])
#@exception_detector
def translator_stoa():
    """
    번역가의 스토아 보여주기

    Store 아니다. Stoa다. 상점 아니다. 기둥 사이, 토론 공간이다.

    로직
        1. 일반 번역인 경우 (isSos = False) 작업중인 번역가가 없으며, (ongoing_worker_id = null) 번역 진행 상태가 pending이고, (status_id = 0) 번역비 결제가 된 경우 (is_paid = True)
        2. 단문 번역인 경우 (isSos = True) 모든 상태를 다 보여줌.
        3. 쿼리 후 결과를 ciceron_lib.json_form_V_REQUESTS()를 이용하여 Response를 parsing한다.
        4. ciceron_lib.json_form_V_REQUESTS()이 하는 일은, 각 의뢰에 필요한 정보를 추려 JSON 꼴로 만들어 주는 라이브러리 함수다.
    """
    if request.method == "GET":
        # Request method: GET
        # Parameters
        #     since(optional): Timestamp, take recent 20 post before the timestamp.
        #                  If this parameter is not provided, recent 20 posts from now are returned
        cursor = g.db.cursor()

        query = None
        pager_date = None
        if session.get('useremail') in super_user:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE
                (((ongoing_worker_id is null AND status_id = 0 AND isSos = false) OR (isSos = true AND status_id IN (0, 1, 2) ))) AND due_time > CURRENT_TIMESTAMP """
        else:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE
                (((ongoing_worker_id is null AND status_id = 0 AND isSos = false AND is_paid = true) OR (isSos = true AND status_id IN (0, 1, 2) ))) AND due_time > CURRENT_TIMESTAMP """
        if 'since' in request.args.keys():
            query += "AND registered_time < to_timestamp(%s) " % request.args.get('since')

        query += " ORDER BY registered_time DESC LIMIT 20 "

        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (pager_date, ) )
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose='stoa_translator')

        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/pending', methods=["GET", "POST"])
@login_required
#@exception_detector
@translator_checker
def show_queue():
    """
    [현재는 사용 안함, 기획 후 사용할수도]
    번역가가 가격 네고를 건 티켓 보여주기 (GET), 가격제시하기 (POST)
    티켓 단가가 너무 낮아서 번역가들이 작업을 기피하고 있을 때, 번역가들이 티켓 가격을 좀만 올려주면 작업을 하겠다고 말해주는 가격제시 API

    GET 로직
        1. 장바구니 관리 테이블: CICERON.D_QUEUE_LISTS
        2. CICERON.D_QUEUE_LISTS에 있는 티켓 중 내 의뢰인 티켓 번호를 찾아 뿌려줌. 결제 완료 의뢰여야 함 (is_paid = True)

    POST 로직
        1. 기본적으로, 의뢰인 API에서는 의뢰인 입장에서 지불한 금액을 보여주고, 번역가 API에서는 번역가 입장에서 받을 수 있는 금액을 보여준다. 예를 들어, USD 5로 의뢰한 금액을 의뢰인한데는 USD 5로 보여주지만, 번역가에게는 USD 3.5로 보여준다. 번역가 입장에서는 5를 벌고 나중에 가져갈 때 1.5를 공제한다고 하는 것보단 아싸리 3.5 받는다고 하는게 여러모로 좋을 것이라 생각하기 때문이다.
        2. D_USERS 테이블을 보면 번역가의 등급에 따라 return_rate를 다르게 설정할 수 있다. 기본은 0.7이다. 즉, 의뢰금의 70%를 번역가가 가져간다.
        3. 이 원리를 거꾸로 생각하면, 번역가가 가격 제시를 할 때에는 return_rate를 고려하여 추가 결제금을 생각향 한다는 것이다. 예를 들어 0.7인 번역가가 7을 제시했으면 의뢰인한테 보여지는 금액은 10이 되어야 한다는 뜻이다.
        4. 나머지 짜글짜글한 exception의뜻들이 궁금하면 브라이언에게 문의..
    """
    if request.method == "GET":
        # Request method: GET
        # Parameters
        #     since(OPTIONAL): Timestamp integer, for paging
        cursor = g.db.cursor()

        my_user_id = get_user_id(g.db, session['useremail'])

        query_pending = None
        if session['useremail'] in super_user:
            query_pending = """SELECT * FROM CICERON.V_REQUESTS 
                WHERE request_id IN (SELECT request_id FROM CICERON.D_QUEUE_LISTS WHERE user_id = %s) """
        else:
            query_pending = """SELECT * FROM CICERON.V_REQUESTS 
                WHERE request_id IN (SELECT request_id FROM CICERON.D_QUEUE_LISTS WHERE user_id = %s) AND is_paid = true """

        if 'since' in request.args.keys():
            query_pending += "AND registered_time < to_timestamp(%s) " % request.args.get('since')
        query_pending += "ORDER BY registered_time DESC LIMIT 20"

        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query_pending, (my_user_id, ) )
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs)

        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        # In POST, it should be changed into /user/translations/pending/<request_id>
        # But Error must be occurred because form data is not needed in the case of above.

        # Request method: POST
        # Parameters
        #     request_id: Integer
        cursor = g.db.cursor()

        # Translators in queue
        # Get request ID
        parameters = parse_request(request)

        request_id = int(parameters['request_id'])
        translator_email = parameters.get('translator_email', session['useremail']) # WILL USE FOR REQUESTING WITH TRANSLATOR SELECTING
        translator_newPoint = float(parameters.get('translator_additionalPoint', 0))
        if translator_newPoint < 2.0:
            return make_response(json.jsonify(
                message="Additional point should be bigger than USD 2.0"
                ), 417)

        query_returnRate = "SELECT return_rate FROM CICERON.D_USERS WHERE email = %s"
        cursor.execute(query_returnRate, (session['useremail'], ))
        ret_returnRate = cursor.fetchone()
        return_rate = None
        if ret_returnRate is not None and len(ret_returnRate) > 0:
            return_rate = ret_returnRate[0]
        if return_rate != None:
            translator_newPoint = translator_newPoint / return_rate

        query = None
        if session['useremail'] in super_user:
            query = "SELECT queue_id, client_user_id, status_id, points, isSos FROM CICERON.F_REQUESTS WHERE id = %s "
        else:
            query = "SELECT queue_id, client_user_id, status_id, points, isSos FROM CICERON.F_REQUESTS WHERE id = %s AND is_paid = true "

        cursor.execute(query, (request_id, ))
        rs = cursor.fetchall()

        if len(rs) == 0: return make_response(json.jsonify(message = "There is no request ID %d" % request_id), 400)

        if translator_email == None: user_id = get_user_id(g.db, session['useremail'])
        else:                        user_id = get_user_id(g.db, translator_email)
        request_user_id = rs[0][1]
        status_id = rs[0][2]
        point = rs[0][3]
        is_sos = rs[0][4]

        if is_sos == True:
            return make_response(json.jsonify(
                message="'Pending' is not supported in SOS ticket"
                ), 409)

        if strict_translator_checker(g.db, user_id, request_id) == False:
            return make_response(
                json.jsonify(
                   message = "You have no translate permission of given language."
                   ), 401)

        if user_id == request_user_id:
            return make_response(json.jsonify(
                message = "You cannot translate your request. Request ID: %d" % request_id,
                request_id=request_id
                ), 406)

        if status_id in [-2, -1, 1, 2]:
            return make_response(json.jsonify(
                message="Gone ticket. (Canceled or translated by others)"
                ), 410)

        queue_id = rs[0][0]
        cursor.execute("SELECT user_id FROM CICERON.D_QUEUE_LISTS WHERE id = %s AND user_id = %s", (queue_id, user_id, ))
        rs = cursor.fetchall()
        if len(rs) != 0:
            return make_response(json.jsonify(
                message = "You've already stood in queue. Request ID: %d" % request_id
                ), 204)

        if point > translator_newPoint - 2.0:
            return make_response(json.jsonify(
                message="New point should be bigger than the requested point"
                ), 417)

        if queue_id == None:
            queue_id = get_new_id(g.db, "D_QUEUE_LISTS")
            cursor.execute("UPDATE CICERON.F_REQUESTS SET queue_id = %s WHERE id = %s", (queue_id, request_id, ))

        query="INSERT INTO CICERON.D_QUEUE_LISTS VALUES (%s,%s,%s,%s)"
        cursor.execute(query, (queue_id, request_id, user_id, translator_newPoint, ))
        g.db.commit()

        update_user_record(g.db, client_id=request_user_id, translator_id=user_id)
        g.db.commit()

        return make_response(json.jsonify(
            message = "You proposed a new price of request #%d" % request_id,
            request_id=request_id
            ), 200)

@app.route('/api/user/translations/pending/<int:request_id>', methods=["DELETE", "PUT"])
@login_required
@translator_checker
#@exception_detector
def work_in_queue(request_id):
    """
    네고를 걸었던 티켓 네고취소 (DELETE), 네고금액 수정 (PUT)
    네고 로직 돌아가는 원리는 바로 위 API의 설명 참고
    """
    if request.method == "DELETE":
        cursor = g.db.cursor()

        my_user_id = get_user_id(g.db, session['useremail'])
        cursor.execute("SELECT count(*) FROM CICERON.D_QUEUE_LISTS WHERE request_id = %s AND user_id = %s ", (request_id, my_user_id))
        rs = cursor.fetchall()
        if len(rs) == 0 or rs[0][0] == 0:
            return make_response(json.jsonify
                       (message="You are not in the queue of request ID #%d" % request_id),
                   204)
            
        cursor.execute("DELETE FROM CICERON.D_QUEUE_LISTS WHERE request_id = %s AND user_id = %s ", (request_id, my_user_id))
        update_user_record(g.db, translator_id=my_user_id)

        return make_response(json.jsonify(
            message="You've dequeued from request #%d" % request_id,
            request_id=request_id), 200)

    elif request.method == "PUT":
        cursor = g.db.cursor()
        parameters = parse_request(request)

        request_id = int(str_request_id)
        my_user_id = get_user_id(g.db, session['useremail'])
        translator_newPoint = parameters['translator_newPoint']

        query_getQueueID = "SELECT queue_id, client_user_id, status_id, points FROM CICERON.F_REQUESTS WHERE id = %s "
        cursor.execute(query_getQueueID, (request_id, ))
        rs = cursor.fetchone()
        if rs is None or len(rs) == 0:
            return make_response(json.jsonify(
                message="You cannot update the point if you didn't join the nego"), 410)

        if translator_newPoint < 2.0:
            return make_response(json.jsonify(
                message="Additional point should be bigger than USD 2.0"
                ), 417)

        queue_id = rs[0]
        query_updateNego = "UPDATE CICERON.D_QUEUE_LISTS SET nego_price = %s WHERE id = %s"
        cursor.execute(query_updateNego, (translator_newPoint, queue_id, ))

        g.db.commit()

        return make_response(json.jsonify(
            message="Point updated",
            point=translator_newPoint), 200)

@app.route('/api/user/translations/ongoing', methods=['GET', 'POST'])
@login_required
@translator_checker
#@exception_detector
def pick_request():
    """
    내가 번역중인 티켓 리스트 보여주기 (GET), 내가 번역하기 (POST)

    POST 로직
        1. 혹시 다른 번역가가 작업중인지 체크
        2. 이미 내가 번역중인지 체크
        3. 내가 해당 언어쌍에 번역 권한이 있는지 체크 (ciceron_lib.strict_translator_checker() )
        4. 번역중 상태로 바꿈 (status_id = 1), 번역중인 번역가를 내 ID로 고침 (ongoing_worker_id = %s)
        5. 네고 중이었다면, 네고 테이블에서 삭제
        6. 이메일 알람 전송
    """
    if request.method == "POST":
        # Request method: POST
        # Parameters
        #    request_id: requested post id
        cursor = g.db.cursor()
        parameters = parse_request(request)

        request_id = int(parameters['request_id'])
        user_id = get_user_id(g.db, session['useremail'])

        cursor.execute("SELECT queue_id, client_user_id FROM CICERON.F_REQUESTS WHERE id = %s AND status_id = 0", (request_id, ) )
        rs = cursor.fetchall()
        if len(rs) == 0:
            return make_response(
                json.jsonify(
                    message = "Request %d has already benn taken by other translator, or deleted." % request_id
                    ), 410)

        queue_id = rs[0][0]
        request_user_id = rs[0][1]
        if user_id == request_user_id:
            return make_response(json.jsonify(
                message = "You cannot translate your request. Request ID: %d" % request_id
                ), 406)

        if strict_translator_checker(g.db, user_id, request_id) == False:
            return make_response(
                json.jsonify(
                   message = "You have no translate permission of given language."
                   ), 401)

        cursor.execute("UPDATE CICERON.F_REQUESTS SET status_id = 1, ongoing_worker_id = %s, start_translating_time = CURRENT_TIMESTAMP WHERE id = %s AND status_id = 0", (user_id, request_id))

        cursor.execute("DELETE FROM CICERON.D_QUEUE_LISTS WHERE id = %s and request_id = %s and user_id = %s", (queue_id, request_id, user_id))
        g.db.commit()

        update_user_record(g.db, client_id=request_user_id, translator_id=user_id)

        # Notification
        send_noti_lite(g.db, request_user_id, 7, user_id, request_id,
                optional_info={"hero": user_id})

        g.db.commit()
        return make_response(json.jsonify(
            message = "You are now tranlator of request #%d" % request_id,
            request_id=request_id
            ), 200)

    elif request.method == "GET":
        # Request method: GET
        # Parameters
        #     page (optional): Integer
        cursor = g.db.cursor()

        query_ongoing = None
        if session['useremail'] in super_user:
            query_ongoing = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 1 AND ongoing_worker_id = %s """
        else:
            query_ongoing = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 1 AND ongoing_worker_id = %s
            AND ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """

        if 'since' in request.args.keys():
            query_ongoing += "AND start_translating_time < to_timestamp(%s) " % request.args.get('since')
        query_ongoing += " ORDER BY start_translating_time DESC LIMIT 20 "

        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        my_user_id = get_user_id(g.db, session['useremail'])
        cursor.execute(query_ongoing, (my_user_id, ) )
        rs = cursor.fetchall()

        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/ongoing/<int:request_id>', methods=["GET"])
#@exception_detector
@translator_checker
@login_required
def working_translate_item(request_id):
    """
    번역중인 티켓 개별로 보기

    로직
        1. 기본적으로 위와 로직은 동일
        2. 그런데 웨어하우징된 티켓을 프론트에 맞게 재구성하여 보여줌
    """
    if request.method == "GET":
        user_id = get_user_id(g.db, session['useremail'])
        cursor = g.db.cursor()

        query = """SELECT count(*) FROM CICERON.V_REQUESTS WHERE status_id = 1 AND request_id = %s AND ongoing_worker_id = %s """
        cursor.execute(query, (request_id, user_id, ))
        count = cursor.fetchone()[0]
        if count == 0:
            return make_response(json.jsonify(
                message="You are not translator of the request"), 406)

        warehousing = Warehousing(g.db)

        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 1 AND request_id = %s "
        else:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 1 AND request_id = %s AND
            ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """
        if 'since' in request.args.keys():
            query += "AND start_translating_time < to_timestamp(%s) " % request.args.get('since')

        query += " ORDER BY start_translating_time desc LIMIT 20 "

        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (request_id, ))

        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator")
        return make_response(json.jsonify(
            data=result,
            realData=warehousing.restoreArray(request_id)
            ), 200)

@app.route('/api/user/translations/ongoing/<int:request_id>/paragraph/<int:paragraph_id>/sentence/<int:sentence_id>', methods=["GET", "PUT"])
#@exception_detector
@translator_checker
@login_required
def reviseTranslatedItemByEachLine(request_id, paragraph_id, sentence_id):
    """
    문장별 번역 업데이트(PUT), 문장별 원문/번역 살펴보기 (GET)

    로직
        1. 일단 자신이 번역하는 티켓인지 체크
        2. 그 다음 보여줄 지, 업데이트할지 하는거 함.
    """
    user_id = get_user_id(g.db, session['useremail'])
    cursor = g.db.cursor()

    query = """SELECT count(*) FROM CICERON.V_REQUESTS WHERE status_id = 1 AND request_id = %s AND ongoing_worker_id = %s """
    cursor.execute(query, (request_id, user_id, ))
    count = cursor.fetchone()[0]
    if count == 0:
        return make_response(json.jsonify(
            message="You are not translator of the request"), 406)

    if request.method == "PUT":
        parameters = parse_request(request)

        text = parameters['text']
        warehousing = Warehousing(g.db)
        is_ok = warehousing.updateTranslationOneLine(request_id, paragraph_id, sentence_id, text)
        
        if is_ok == True:
            return make_response(json.jsonify(
                message="Sentence saved.",
                request_id=request_id
                ), 200)
        else:
            return make_response(json.jsonify(
                message="Sentence save failure.",
                request_id=request_id
                ), 401)

    elif request.method == "GET":
        warehousing = Warehousing(g.db)
        is_ok, sentence = warehousing.getTranslationOneLine(request_id, paragraph_id, sentence_id)
        if is_ok == True:
            return make_response(json.jsonify(
                sentence=sentence
                ), 200)
        else:
            return make_response(json.jsonify(
                message="Get sentence failure."
                ), 401)

@app.route('/api/user/translations/comment/<int:request_id>/paragraph/<int:paragraph_id>/sentence/<int:sentence_id>', methods=["PUT"])
#@exception_detector
@translator_checker
@login_required
def updateSentenceComment(request_id, paragraph_id, sentence_id):
    """
    문장별 주석 달기
    """

    user_id = get_user_id(g.db, session['useremail'])
    cursor = g.db.cursor()

    query = """SELECT count(*) FROM CICERON.V_REQUESTS WHERE status_id = 1 AND request_id = %s AND ongoing_worker_id = %s """
    cursor.execute(query, (request_id, user_id, ))
    count = cursor.fetchone()[0]
    if count == 0:
        return make_response(json.jsonify(
            message="You are not translator of the request"), 406)

    if request.method == "PUT":
        warehousing = Warehousing(g.db)
        parameter = parse_request(request)

        comment_string = parameter.get('comment_string')

        warehousing.updateSentenceComment(request_id, paragraph_id, sentence_id, comment_string)
        return make_response(
                json.jsonify(
                    message='Update success',
                    request_id=request_id,
                    paragraph_seq=paragraph_id,
                    sentence_seq=sentence_id,
                    comment_string=comment_string
                    ), 200)

@app.route('/api/user/translations/comment/<int:request_id>/paragraph/<int:paragraph_id>', methods=["PUT"])
#@exception_detector
@translator_checker
@login_required
def updateParagraphComment(request_id, paragraph_id):
    """
    문단별 주석 달기 (혼동주의: 위는 문장별, 여기는 문단별)
    """
    user_id = get_user_id(g.db, session['useremail'])
    cursor = g.db.cursor()

    query = """SELECT count(*) FROM CICERON.V_REQUESTS WHERE status_id = 1 AND request_id = %s AND ongoing_worker_id = %s """
    cursor.execute(query, (request_id, user_id, ))
    count = cursor.fetchone()[0]
    if count == 0:
        return make_response(json.jsonify(
            message="You are not translator of the request"), 406)

    if request.method == "PUT":
        warehousing = Warehousing(g.db)
        parameter = parse_request(request)

        comment_string = parameter.get('comment_string')

        warehousing.updateParagraphComment(request_id, paragraph_id, comment_string)
        return make_response(
                json.jsonify(
                    message='Update success',
                    request_id=request_id,
                    paragraph_seq=paragraph_id,
                    comment_string=comment_string
                    ), 200)

@app.route('/api/user/translations/ongoing/i18n/<int:request_id>', methods=["GET"])
#@exception_detector
@translator_checker
@login_required
def i18n_checkSourceAndTranslation(request_id):
    """
    i18n 번역 불러오기
    i18nHandler.jsonResponse() 사용
    """
    if request.method == 'GET':
        user_id = get_user_id(g.db, session['useremail'])
        has_translation_auth = translationAuthChecker(g.db, user_id, request_id, 1)
        if has_translation_auth == False:
            return make_response(json.jsonify(
                message="You are not translator of the request"), 406)

        i18nObj = I18nHandler(g.db)
        result = i18nObj.jsonResponse(request_id, is_restricted=False)

        return make_response(json.jsonify(
            realData=result
            ), 200)

@app.route('/api/user/translations/ongoing/i18n/<int:request_id>/variable/<int:variable_id>/paragraph/<int:paragraph_seq>/sentence/<int:sentence_seq>', methods=["PUT"])
#@exception_detector
@translator_checker
@login_required
def i18n_updateSentence(request_id, variable_id, paragraph_seq, sentence_seq):
    """
    해당 Variable, 해당 문단의 해당 문장 번역 업데이트.
    i18nHandler.updateTranslation() 사용
    """
    if request.method == 'PUT':
        user_id = get_user_id(g.db, session['useremail'])
        has_translation_auth = translationAuthChecker(g.db, user_id, request_id, 1)
        if has_translation_auth == False:
            return make_response(json.jsonify(
                message="You are not translator of the request"), 406)

        parameters = parse_request(request)
        text = parameters['text']

        i18nObj = I18nHandler(g.db)
        i18nObj.updateTranslation(request_id, variable_id, paragraph_seq, sentence_seq, text)

        return make_response(json.jsonify(
                message="Update success",
                request_id=request_id,
                variable_id=variable_id,
                paragraph_seq=paragraph_seq,
                sentence_seq=sentence_seq
            ), 200)

@app.route('/api/user/translations/ongoing/i18n/<int:request_id>/variable/<int:variable_id>/comment', methods=["PUT"])
#@exception_detector
@translator_checker
@login_required
def i18n_updateComment(request_id, variable_id):
    """
    각 Variable의 comment를 다는 API
    평문 번역과는 다르게 i18n 번역에서는 comment를 문장별로 달지 않고 variable 별로 단다.
    """
    if request.method == 'PUT':
        user_id = get_user_id(g.db, session['useremail'])
        has_translation_auth = translationAuthChecker(g.db, user_id, request_id, 1)
        if has_translation_auth == False:
            return make_response(json.jsonify(
                message="You are not translator of the request"), 406)

        parameters = parse_request(request)
        comment_string = parameters['comment_string']

        i18nObj = I18nHandler(g.db)
        i18nObj.updateComment(request_id, variable_id, comment_string)

        return make_response(json.jsonify(
                message="Update success",
                request_id=request_id,
                variable_id=variable_id
            ), 200)

@app.route('/api/user/translations/ongoing/<int:request_id>/expected', methods=["GET", "POST", "DELETE"])
#@exception_detector
@translator_checker
@login_required
def expected_time(request_id):
    """
    (현재 사용하지 않음)
    예상완료시간 보기 (GET), 입력(POST), 번역포기 (DELETE)

    번역가가 번역을 하겠다고 마킹을 하면 바로 번역을 진행하는 것이 아니라, 먼저 본문을 한 번 열람을 하고,
    언제까지 번역이 가능한지 예상 시간을 입력한다. (혹은 번역 포기를 한다.)
    만약 번역하겠다고 한 시간에서 1/3 시점까지 예상시간을 입력하지 않으면 자동으로 번역불가로 간주하고 도로 스토아로 되돌려놓는다.
    주가 되는 column은 CICERON.F_REQUESTS.expected_time이다.
    """
    if request.method == "GET":
        cursor = g.db.cursor()
        user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT expected_time, due_time FROM CICERON.F_REQUESTS WHERE status_id = 1 AND id = %s "
        else:
            query = """SELECT expected_time, due_time FROM CICERON.F_REQUESTS WHERE status_id = 1 AND id = %s AND ongoing_worker_id = %s
            AND ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """
        if 'since' in request.args.keys():
            query += "AND start_translating_time < to_timestamp(%s) " % request.args.get('since')

        query += " ORDER BY start_translating_time desc LIMIT 20 "
        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (request_id, user_id, ) )
        rs = cursor.fetchall()
        if len(rs) > 0:
            return make_response(json.jsonify(currentExpectedTime=rs[0][0], currentDueTime=rs[0][1]), 200)
        else:
            return make_response(json.jsonify(message="Outscoped (Completed, canceled, etc)"), 400)

    elif request.method == "POST":
        cursor = g.db.cursor()
        parameters = parse_request(request)
        user_id = get_user_id(g.db, session['useremail'])

        deltaFromRegTime = int(parameters['deltaFromNow'])
        cursor.execute("UPDATE CICERON.F_REQUESTS SET expected_time = CURRENT_TIMESTAMP + interval '%s seconds' WHERE status_id = 1 AND id = %s AND ongoing_worker_id = %s ", (deltaFromRegTime, request_id, user_id, ) )
        g.db.commit()


        # Notification
        query = "SELECT client_user_id, expected_time FROM CICERON.F_REQUESTS WHERE id = %s"
        cursor.execute(query, (request_id, ))
        rs = cursor.fetchall()
        send_noti_lite(g.db, rs[0][0], 8, user_id, request_id, optional_info={"expected": rs[0][1]})

        g.db.commit()
        return make_response(json.jsonify(
            message="Thank you for responding!",
            currentExpectedTime=rs[0][1],
            request_id=request_id), 200)

    elif request.method == "DELETE":
        cursor = g.db.cursor()
        user_id = get_user_id(g.db, session['useremail'])
        cursor.execute("UPDATE CICERON.F_REQUESTS SET ongoing_worker_id = null, status_id = 0, points = points + additional_points, is_need_additional_points = false, is_additional_points_paid = null WHERE status_id = 1 AND id = %s AND ongoing_worker_id = %s ", (request_id, user_id, ))
        g.db.commit()

        query = None
        if session['useremail'] in super_user:
            query = "SELECT due_time FROM CICERON.F_REQUESTS WHERE status_id = 1 AND id = %s "
        else:
            query = """SELECT due_time FROM CICERON.F_REQUESTS WHERE status_id = 1 AND id = %s
                AND ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """
        cursor.execute(query, (request_id, ))

        client_user_id = cursor.fetchall()[0][0]
        translator_user_id = get_user_id(g.db, session['useremail'])

        update_user_record(g.db, client_id=client_user_id, translator_id=translator_user_id)

        # Notification
        query = "SELECT client_user_id, ongoing_worker_id FROM CICERON.F_REQUESTS WHERE id = %s "
        cursor.execute(query, (request_id, ))
        rs = cursor.fetchall()
        send_noti_lite(g.db, rs[0][0], 9, rs[0][1], request_id, optional_info={"hero": rs[0][1]})

        g.db.commit()
        return make_response(json.jsonify(
            message="Wish a better tomorrow!",
            request_id=request_id), 200)

@app.route('/api/user/translations/complete', methods=["POST"])
#@exception_detector
@login_required
@translator_checker
def post_translate_item():
    """
    해당 의뢰 번역 완료 선언을 하는 곳이다.
    로직
        1. status_id = 1인 놈을 status_id = 2로 업데이트
        2. 작업 완료한 번역은 폴더 관리가 된다. 폴더 중 Incoming 폴더에 갖다 집어넣는다. 만약 없다면 만들어 준 다음 집어넣는다.
        3. 처음 가입할 때에는 작업 완료된 폴더가 없다. 처음 완료할 때 생성된다. 나중에 번역완료 탭에 가서 폴더를 옮길 수 있다.
        4. 해당 의뢰에 네고를 건 것들 모두 삭제한다.
        5. 이메일 노티 전송
    """
    cursor = g.db.cursor()
    parameters = parse_request(request)

    request_id = int(parameters['request_id'])

    # Assign default group to requester and translator
    query = None
    if session['useremail'] in super_user:
        query = "SELECT client_user_id, ongoing_worker_id FROM CICERON.V_REQUESTS WHERE request_id = %s AND status_id = 1 "
    else:
        query = """SELECT client_user_id, ongoing_worker_id FROM CICERON.V_REQUESTS WHERE request_id = %s AND status_id = 1 AND 
        ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) )"""

    cursor.execute(query, (request_id, ))
    rs = cursor.fetchall()
    if len(rs) == 0:
        return make_response(
            json.jsonify(
                message="Already completed request %d" % request_id,
                request_id=request_id), 410)

    requester_id = rs[0][0]
    translator_id = rs[0][1]

    requester_default_group_id = get_group_id_from_user_and_text(g.db, requester_id, "Incoming", "D_CLIENT_COMPLETED_GROUPS")
    translator_default_group_id =  get_group_id_from_user_and_text(g.db, translator_id, "Incoming", "D_TRANSLATOR_COMPLETED_GROUPS")

    # No default group. Insert new default group entry for user
    if requester_default_group_id == -1:
        requester_default_group_id = get_new_id(g.db, "D_CLIENT_COMPLETED_GROUPS")
        cursor.execute("INSERT INTO CICERON.D_CLIENT_COMPLETED_GROUPS VALUES (%s,%s,%s)",
            (requester_default_group_id, requester_id, "Incoming"))
    if translator_default_group_id == -1:
        translator_default_group_id = get_new_id(g.db, "D_TRANSLATOR_COMPLETED_GROUPS")
        cursor.execute("INSERT INTO CICERON.D_TRANSLATOR_COMPLETED_GROUPS VALUES (%s,%s,%s)",
            (translator_default_group_id, translator_id, "Incoming"))

    # Change the state of the request
    cursor.execute("UPDATE CICERON.F_REQUESTS SET status_id = 2, client_completed_group_id = %s, translator_completed_group_id = %s, submitted_time = CURRENT_TIMESTAMP WHERE id = %s AND ongoing_worker_id = %s ",
            (requester_default_group_id, translator_default_group_id, request_id, translator_id, ))
    g.db.commit()

    update_user_record(g.db, client_id=requester_id, translator_id=translator_id)

    # Delete users in queue
    cursor.execute("DELETE FROM CICERON.D_QUEUE_LISTS WHERE request_id = %s", (request_id, ))

    # Notification
    query = "SELECT client_user_id, ongoing_worker_id FROM CICERON.F_REQUESTS WHERE id = %s"
    cursor.execute(query, (request_id, ))
    rs = cursor.fetchall()
    send_noti_lite(g.db, rs[0][0], 11, rs[0][1], request_id, optional_info={"hero": rs[0][1]})

    g.db.commit()

    return make_response(json.jsonify(
        message="Request id %d is submitted." % request_id,
        request_id=request_id
        ), 200)

@app.route('/api/user/translations/complete/<int:request_id>', methods = ["GET"])
#@exception_detector
@login_required
@translator_checker
def translation_completed_items_detail(request_id):
    cursor = g.db.cursor()

    user_id = get_user_id(g.db, session['useremail'])
    query = """SELECT count(*) FROM CICERON.V_REQUESTS WHERE status_id = 2 AND request_id = %s AND ongoing_worker_id = %s """
    cursor.execute(query, (request_id, user_id, ))
    count = cursor.fetchone()[0]
    if count == 0:
        return make_response(json.jsonify(
            message="You are not translator of the request"), 406)

    warehousing = Warehousing(g.db)
    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 2 AND request_id = %s AND ongoing_worker_id = %s "
    else:
        query = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 2 AND request_id = %s AND ongoing_worker_id = %s AND 
        ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """

    if 'since' in request.args.keys():
        query += "AND submitted_time < to_timestamp(%s) " % request.args.get('since')
    query += " ORDER BY submitted_time DESC LIMIT 20 "
    if 'page' in request.args.keys():
        page = request.args.get('page')
        query += " OFFSET %d " % (( int(page)-1 ) * 20)

    cursor.execute(query, (request_id, user_id))
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_translator")
    return make_response(json.jsonify(
        data=result,
        realData=warehousing.restoreArray(request_id)
        ), 200)

@app.route('/api/user/translations/complete', methods = ["GET"])
#@exception_detector
@login_required
@translator_checker
def translation_completed_items_all():
    cursor = g.db.cursor()
    since = request.args.get('since', None)
    user_id = get_user_id(g.db, session['useremail'])

    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 2 AND ongoing_worker_id = %s "
    else:
        query = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 2 AND ongoing_worker_id = %s AND 
       ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """

    if 'since' in request.args.keys():
        query += "AND submitted_time < to_timestamp(%s) " % request.args.get('since')
    query += " ORDER BY submitted_time DESC LIMIT 20"

    if 'page' in request.args.keys():
        page = request.args.get('page')
        query += " OFFSET %d " % (( int(page)-1 ) * 20)

    cursor.execute(query, (user_id, ) )
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_translator")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/complete/<str_request_id>/title', methods = ["POST"])
#@exception_detector
@login_required
@translator_checker
def set_title_translator(str_request_id):
    if request.method == "POST":
        cursor = g.db.cursor()
        parameters = parse_request(request)

        request_id = int(str_request_id)
        title_text = (parameters['title_text']).encode('utf-8')

        my_user_id = get_user_id(g.db, session['useremail'])
        default_group_id = get_group_id_from_user_and_text(g.db, my_user_id, "Incoming", "D_TRANSLATOR_COMPLETED_GROUPS")

        # No default group. Insert new default group entry for user
        new_title_id = get_new_id(g.db, "D_TRANSLATOR_COMPLETED_REQUEST_TITLES")
        cursor.execute("INSERT INTO CICERON.D_TRANSLATOR_COMPLETED_REQUEST_TITLES VALUES (%s,%s)", (new_title_id, title_text))
        cursor.execute("UPDATE CICERON.F_REQUESTS SET translator_title_id = %s WHERE id = %s", (new_title_id, request_id))

        g.db.commit()

        return make_response(json.jsonify(
            message="The title is set as '%s' to the request #%d" % (title_text, request_id),
            request_id=request_id),
            200)

    else:
        return make_response(json.jsonify(
                message="Inappropriate method of this request. POST only",
                request_id=request_id),
            405)

@app.route('/api/user/translations/complete/groups', methods = ["GET", "POST"])
#@exception_detector
@login_required
def translators_complete_groups():
    if request.method == "GET":
        since = None
        if 'since' in request.args.keys():
            since = request.args['since']

        page = None
        if 'page' in request.args.keys():
            page = request.args.get('page')

        result = complete_groups(g.db, None, "D_TRANSLATOR_COMPLETED_GROUPS", "GET", since=since, page=page)
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        parameters = parse_request(request)
        group_name = complete_groups(g.db, parameters, "D_TRANSLATOR_COMPLETED_GROUPS", "POST")
        if group_name == -1:
            return make_response(json.jsonify(message="'Incoming' is reserved name"), 401)
        else:
            return make_response(json.jsonify(message="New group %s has been created" % group_name), 200)

@app.route('/api/user/translations/complete/groups/<str_group_id>', methods = ["DELETE", "PUT"])
#@exception_detector
@translator_checker
@login_required
def modify_translators_complete_groups(str_group_id):
    parameters = parse_request(request)

    if request.method == "DELETE":
        group_id = complete_groups(g.db, None, "D_TRANSLATOR_COMPLETED_GROUPS", "DELETE", url_group_id=str_group_id)
        if group_id == -1:
            return make_response(json.jsonify(message="Group 'Incoming' is default. You cannot delete it!"), 401)
        else:
            return make_response(json.jsonify(message="Group %d is deleted. Requests are moved into default group" % group_id), 200)

    elif request.method == "PUT":
        parameters = parse_request(request)
        group_name = complete_groups(g.db, parameters, "D_TRANSLATOR_COMPLETED_GROUPS", "PUT")
        if group_name == -1:
            return make_response(json.jsonify(message="You cannot change the name of the group to 'Incoming'. It is default group name" % group_name), 401)
        else:
            return make_response(json.jsonify(message="Group name is changed to %s" % group_name), 200)

@app.route('/api/user/translations/complete/groups/<str_group_id>', methods = ["POST", "GET"])
#@exception_detector
@translator_checker
@login_required
def translation_completed_items_in_group(str_group_id):
    if request.method == "POST":
        cursor = g.db.cursor()
        parameters = parse_request(request)

        group_id = int(str_group_id)
        request_id = int(parameters['request_id'])
        cursor.execute("UPDATE CICERON.F_REQUESTS SET translator_completed_group_id = %s WHERE id = %s", (group_id, request_id))
        group_name = get_text_from_id(g.db, group_id, "D_TRANSLATOR_COMPLETED_GROUPS")
        g.db.commit()
        return make_response(
                json.jsonify(message="Request #%d has been moved to the group '%s'" % (request_id, group_name)), 200)

    elif request.method == "GET":
        cursor = g.db.cursor()
        group_id = int(str_group_id)
        my_user_id = get_user_id(g.db, session['useremail'])

        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM CICERON.V_REQUESTS WHERE ongoing_worker_id = %s AND translator_completed_group_id = %s "
        else:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE ongoing_worker_id = %s AND translator_completed_group_id = %s AND 
           ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """
        if 'since' in request.args.keys():
            query += "AND submitted_time < to_timestamp(%s) " % request.args.get('since')
        query += " ORDER BY submitted_time DESC LIMIT 20"
        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (my_user_id, group_id))
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="complete_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/incomplete', methods = ["GET"])
#@exception_detector
@login_required
@translator_checker
def translation_incompleted_items_all():
    cursor = g.db.cursor()
    since = request.args.get('since', None)
    user_id = get_user_id(g.db, session['useremail'])

    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM CICERON.V_REQUESTS WHERE ((status_id IN (-1,1) AND ongoing_worker_id = %s) OR (request_id IN (SELECT request_id FROM CICERON.D_QUEUE_LISTS WHERE user_id = %s))) "
    else:
        query = """SELECT * FROM CICERON.V_REQUESTS
            WHERE (
                (status_id IN (-1,1) AND ongoing_worker_id = %s) 
              OR
                (request_id IN (SELECT request_id FROM CICERON.D_QUEUE_LISTS WHERE user_id = %s) )
            ) 
              AND
             ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """

    if 'since' in request.args.keys():
        query += "AND registered_time < to_timestamp(%s) " % request.args.get('since')
    query += " ORDER BY request_id DESC LIMIT 20"
    if 'page' in request.args.keys():
        page = request.args.get('page')
        query += " OFFSET %d " % (( int(page)-1 ) * 20)

    cursor.execute(query, (user_id, user_id))
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="pending_translator")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/incomplete/<int:request_id>', methods = ["GET"])
#@exception_detector
@login_required
@translator_checker
def translation_incompleted_items_each(request_id):
    if request.method == "GET":
        cursor = g.db.cursor()

        user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM CICERON.V_REQUESTS WHERE status_id IN (-1,1) AND ongoing_worker_id = %s AND request_id = %s "
        else:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id IN (-1,1) AND ongoing_worker_id = %s AND request_id = %s AND
           ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) )  """
        if 'since' in request.args.keys():
            query += "AND registered_time < to_timestamp(%s) " % request.args.get('since')
        query += " ORDER BY registered_time DESC LIMIT 20"
        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (user_id, request_id))
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="pending_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/stoa', methods=["GET"])
#@exception_detector
def user_stoa():
    if request.method == "GET":
        # Request method: GET
        # Parameters
        #     since(optional): Timestamp, take recent 20 post before the timestamp.
        #                  If this parameter is not provided, recent 20 posts from now are returned
        cursor = g.db.cursor()

        query = None
        pager_date = None
        query = """SELECT * FROM CICERON.V_REQUESTS WHERE
                isSos = true AND status_id IN (0, 1, 2) AND due_time > CURRENT_TIMESTAMP """
        if 'since' in request.args.keys():
            query += "AND registered_time < to_timestamp(%s) " % request.args.get('since')

        query += " ORDER BY registered_time DESC LIMIT 20 "

        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (pager_date, ) )
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose='stoa_client')

        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/pending', methods=["GET", "POST"])
#@exception_detector
@login_required
def show_pending_list_client():
    if request.method == "GET":
        cursor = g.db.cursor()

        user_id = get_user_id(g.db, session['useremail'])
        if session['useremail'] in super_user:
            query = "SELECT * FROM CICERON.V_REQUESTS WHERE client_user_id = %s AND status_id = 0 "
        else:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE client_user_id = %s AND status_id = 0 AND 
            ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """
        if 'since' in request.args.keys():
            query += "AND registered_time < to_timestamp(%s) " % request.args.get('since')

        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        query += " ORDER BY registered_time DESC LIMIT 20"
        cursor.execute(query, (user_id, ))
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        parameters = parse_request(request)

        pay_by = parameters['pay_by']
        pay_via = parameters['pay_via']
        request_id = int(parameters['request_id'])
        translator_id = get_user_id(g.db, parameters['translator_userEmail'])
        host_ip = HOST
        use_point = float(parameters.get('user_point', 0))
        promo_type = parameters.get('promo_type', 'null')
        promo_code = parameters.get('promo_code', 'null')

        payload_iamport = {}
        if pay_via == 'iamport':
            # 'merchant_uid' => Create internally
            payload_iamport['card_number']  = parameters['card_number']
            payload_iamport['expiry'] =       parameters['expiry']
            payload_iamport['birth'] =        parameters['birth']
            payload_iamport['pwd_2digit'] =   parameters['pwd_2digit']

        user_id = get_user_id(g.db, session['useremail'])

        status_code = approve_negoPoint(g.db, request_id, translator_id, user_id)

        if status_code == 406:
            return make_response(json.jsonify(
                message='Not valid hero email or ticket entry'), 406)

        elif status_code == 409:
            return make_response(json.jsonify(
                message='Suggested point is smaller than original point'), 409)

        elif status_code == 402:
            return make_response(json.jsonify(
                message="Somebody already working on the ticket"
                ), 402)

        # status_code == 200: pass

        diff_amount = get_total_amount(g.db, request_id, translator_id, is_additional='true')
        print diff_amount
        if diff_amount == "ERROR":
            return make_response(json.jsonify(
                message="Something wrong in DB record"
                ), 500)

        status_string, provided_link, current_point = payment_start(g.db, pay_by, pay_via, request_id, diff_amount, user_id, host_ip,
                use_point=use_point, promo_type=promo_type, promo_code=promo_code, is_additional='true', payload=payload_iamport)

        if status_string == 'point_exceeded_than_you_have':
            return make_response(json.jsonify(
                message="You requested to use your points more than what you have. Price: %.2f, Your purse: %.2f" % (use_point, current_point)), 401)

        elif status_string == 'paypal_error':
            return make_response(json.jsonify(
                message="Something wrong in paypal"), 410)

        elif status_string == 'paypal_success':
            return make_response(json.jsonify(
                message="Redirect link is provided!",
                link=provided_link), 200)

        elif status_string == 'alipay_success':
            return make_response(json.jsonify(
                message="Link to Alipay is provided.",
                link=provided_link), 200)

        elif status_string == 'alipay_failure':
            return make_response(json.jsonify(
                message="Error on alipay"), 411)

        elif status_string == 'point_success':
            return make_response(json.jsonify(
                message='Success',
                link='%s/stoa' % HOST), 200)

        elif status_string == 'iamport_success':
            return make_response(json.jsonify(
                message='Success',
                link='%s/stoa' % HOST), 200)

@app.route('/api/user/requests/pending/<int:request_id>', methods=["GET"])
#@exception_detector
@login_required
def show_pending_item_client(request_id):
    if request.method == "GET":
        cursor = g.db.cursor()

        user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM CICERON.V_REQUESTS WHERE request_id = %s AND client_user_id = %s AND status_id = 0 "
        else:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE request_id = %s AND client_user_id = %s AND status_id = 0 AND
           ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) )  """
        if 'since' in request.args.keys():
            query += "AND registered_time < to_timestamp(%s) " % request.args.get('since')
        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (request_id, user_id))
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/pending/<int:request_id>', methods=["DELETE"])
#@exception_detector
@login_required
def delete_item_client(request_id):
    if request.method == "DELETE":
        cursor = g.db.cursor()

        user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT points FROM CICERON.V_REQUESTS WHERE request_id = %s AND client_user_id = %s AND status_id = 0 "
        else:
            query = """SELECT points FROM CICERON.V_REQUESTS WHERE request_id = %s AND client_user_id = %s AND status_id = 0 AND
           ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) )  """
        cursor.execute(query, (request_id, user_id))
        points = cursor.fetchall()[0][0]
        cursor.execute("UPDATE CICERON.REVENUE SET amount = amount + %s WHERE id = %s", (points, user_id))
        cursor.execute("UPDATE CICERON.F_REQUESTS SET status_id = -2 WHERE id = %s AND client_user_id = %s AND status_id = 0", (request_id, user_id))
        g.db.commit()
        return make_response(json.jsonify(
            message="Request #%d is deleted. USD %.2f is returned as requester's points" % (request_id, float(points)), request_id=request_id), 200)

@app.route('/api/user/requests/ongoing', methods=["GET"])
#@exception_detector
@login_required
def show_ongoing_list_client():
    if request.method == "GET":
        cursor = g.db.cursor()

        user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM CICERON.V_REQUESTS WHERE client_user_id = %s AND status_id = 1 "
        else:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE client_user_id = %s AND status_id = 1 AND
           ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """
        if 'since' in request.args.keys():
            query += "AND start_translating_time < to_timestamp(%s) " % request.args.get('since')
        query += " ORDER BY start_translating_time DESC LIMIT 20"
        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (user_id, ))
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/ongoing/<int:request_id>', methods=["GET"])
#@exception_detector
@login_required
def show_ongoing_item_client(request_id):
    if request.method == "GET":
        cursor = g.db.cursor()

        user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM CICERON.V_REQUESTS WHERE request_id = %s AND client_user_id = %s AND status_id = 1 "
        else:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE request_id = %s AND client_user_id = %s AND status_id = 1 AND
           ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) )  """
        if 'since' in request.args.keys():
            query += "AND start_translating_time < to_timestamp(%s) " % request.args.get('since')
        query += " ORDER BY start_translating_time DESC LIMIT 20"
        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (request_id, user_id))
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/complete', methods = ["GET"])
#@exception_detector
@login_required
def client_completed_items():
    cursor = g.db.cursor()

    user_id = get_user_id(g.db, session['useremail'])
    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 2 AND client_user_id = %s "
    else:
        query = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 2 AND client_user_id = %s AND 
        ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """
    if 'since' in request.args.keys():
        query += "AND submitted_time < to_timestamp(%s) " % request.args.get('since')
    query += " ORDER BY submitted_time DESC LIMIT 20"
    if 'page' in request.args.keys():
        page = request.args.get('page')
        query += " OFFSET %d " % (( int(page)-1 ) * 20)

    cursor.execute(query, (user_id, ))
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/complete/<int:request_id>', methods = ["GET"])
#@exception_detector
@login_required
def client_completed_items_detail(request_id):
    warehousing = Warehousing(g.db)
    user_id = get_user_id(g.db, session['useremail'])
    cursor = g.db.cursor()

    query = """SELECT count(*) FROM CICERON.V_REQUESTS WHERE status_id = 2 AND request_id = %s AND client_user_id = %s """
    cursor.execute(query, (request_id, user_id, ))
    count = cursor.fetchone()[0]
    if count == 0:
        return make_response(json.jsonify(
            message="You are not client of the request"), 406)


    user_id = get_user_id(g.db, session['useremail'])
    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 2 AND client_user_id = %s AND request_id = %s "
    else:
        query = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 2 AND client_user_id = %s AND request_id = %s AND
         ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) )  """
    if 'since' in request.args.keys():
        query += "AND submitted_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += " ORDER BY submitted_time DESC LIMIT 20"
    if 'page' in request.args.keys():
        page = request.args.get('page')
        query += " OFFSET %d " % (( int(page)-1 ) * 20)

    cursor.execute(query, (user_id, request_id, ))
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")
    return make_response(json.jsonify(
        data=result,
        realData=warehousing.restoreArray(request_id)
        ), 200)

@app.route('/api/user/requests/complete/<int:request_id>/rate', methods=["POST"])
#@exception_detector
@login_required
def client_rate_request(request_id):
    cursor = g.db.cursor()

    parameters = parse_request(request)
    feedback_score = int(parameters['request_feedbackScore'])

    # Pay back part
    if session['useremail'] in super_user:
        query_getTranslator = "SELECT ongoing_worker_id, points, feedback_score, is_need_additional_points, additional_points FROM CICERON.F_REQUESTS WHERE id = %s "
    else:
        query_getTranslator = """SELECT ongoing_worker_id, points, feedback_score, is_need_additional_points, additional_points FROM CICERON.F_REQUESTS WHERE id = %s AND 
         ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """

    cursor.execute(query_getTranslator, (request_id, ) )
    rs = cursor.fetchall()
    formal_feedback_score = rs[0][2]

    # If the request is rated, another rate should be blocked
    if formal_feedback_score != None:
        return make_response(json.jsonify(
            message="The request is already rated!",
            request_id=request_id),
            403)

    translator_id = rs[0][0]
    pay_amount = None
    if rs[0][3] == False:
        pay_amount = rs[0][1]
    else:
        pay_amount = rs[0][1] + rs[0][4]

    user_id = get_user_id(g.db, session['useremail'])
    # Input feedback score
    cursor.execute("UPDATE CICERON.F_REQUESTS SET feedback_score = %s WHERE id = %s AND client_user_id = %s", (feedback_score, request_id, user_id, ))

    query_getCounts = "SELECT return_rate FROM CICERON.D_USERS WHERE id = %s"
    cursor.execute(query_getRate, (user_id, ))
    rs = cursor.fetchone()

    return_rate = rs[0]

    # Record payment record
    cursor.execute("UPDATE CICERON.PAYMENT_INFO SET translator_id = %s, is_payed_back = %s, back_amount = %s WHERE request_id = %s",
            (translator_id, False, return_rate*pay_amount, request_id) )

    # Update the translator's purse
    cursor.execute("UPDATE CICERON.REVENUE SET amount = amount + %s * %s WHERE id = %s",
            (return_rate, pay_amount, translator_id) )

    # Notification
    query = "SELECT ongoing_worker_id, client_user_id FROM CICERON.F_REQUESTS WHERE id = %s AND client_user_id = %s"
    cursor.execute(query, (request_id, user_id, ) )
    rs = cursor.fetchall()
    send_noti_lite(g.db, rs[0][0], 3, rs[0][1], request_id)

    g.db.commit()

    return make_response(json.jsonify(
        message="The requester rated to request #%d as %d points (in 0~2). And translator has been earned USD %.2f" % (request_id, feedback_score, pay_amount*return_rate),
        request_id=request_id),
        200)

@app.route('/api/user/requests/complete/<int:request_id>/title', methods=["POST"])
#@exception_detector
@login_required
def set_title_client(request_id):
    if request.method == "POST":
        cursor = g.db.cursor()
        parameters = parse_request(request)

        title_text = parameters['title_text']

        my_user_id = get_user_id(g.db, session['useremail'])
        default_group_id = get_group_id_from_user_and_text(g.db, my_user_id, "Incoming", "D_CLIENT_COMPLETED_GROUPS")

        # No default group. Insert new default group entry for user
        new_title_id = get_new_id(g.db, "D_CLIENT_COMPLETED_REQUEST_TITLES")
        cursor.execute("INSERT INTO CICERON.D_CLIENT_COMPLETED_REQUEST_TITLES VALUES (%s,%s)", (new_title_id, title_text) )

        cursor.execute("UPDATE CICERON.F_REQUESTS SET client_title_id = %s WHERE id = %s", (new_title_id, request_id))
        g.db.commit()
        return make_response(json.jsonify(
            message="The title is set as '%s' to the request #%d" % (title_text, request_id)),
            200)

    else:
        return make_response(json.jsonify(
                message="Inappropriate method of this request. POST only"),
            405)

@app.route('/api/user/requests/complete/groups', methods = ["GET", "POST"])
#@exception_detector
@login_required
def client_complete_groups():
    if request.method == "GET":
        since = None
        if 'since' in request.args.keys():
            since = request.args['since']

        page = None
        if 'page' in request.args.keys():
            page = request.args.get('page')

        result = complete_groups(g.db, None, "D_CLIENT_COMPLETED_GROUPS", "GET", since=since, page=page)
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        parameters = parse_request(request)

        group_name = complete_groups(g.db, parameters, "D_CLIENT_COMPLETED_GROUPS", "POST")
        if group_name != -1:
            return make_response(json.jsonify(message="New group %s has been created" % group_name), 200)
        else:
            return make_response(json.jsonify(message="'Incoming' is default group name"), 401)

@app.route('/api/user/requests/complete/groups/<str_group_id>', methods = ["PUT", "DELETE"])
#@exception_detector
@login_required
def modify_client_completed_groups(str_group_id):
    if request.method == "PUT":
        parameters = parse_request(request)
        group_name = complete_groups(g.db, parameters, "D_CLIENT_COMPLETED_GROUPS", "PUT", url_group_id=str_group_id)
        if group_name != -1:
            return make_response(json.jsonify(message="Group name is changed to %s" % group_name), 200)
        else:
            return make_response(json.jsonify(message="'Incoming' is default group name"), 401)

    elif request.method == "DELETE":
        group_id = complete_groups(g.db, None, "D_CLIENT_COMPLETED_GROUPS", "DELETE", url_group_id=str_group_id)
        if group_id == -1:
            return make_response(json.jsonify(message="You cannot delete 'Incoming' group"), 401)

        elif group_id == -2:
            return make_response(json.jsonify(message="Already deleted group"), 401)

        else:
            return make_response(json.jsonify(message="Group %d is deleted." % group_id), 200)

@app.route('/api/user/requests/complete/groups/<int:group_id>', methods = ["POST", "GET"])
#@exception_detector
@login_required
def client_completed_items_in_group(group_id):
    if request.method == "POST":
        cursor = g.db.cursor()
        parameters = parse_request(request)
        request_id = int(parameters['request_id'])
        cursor.execute("UPDATE CICERON.F_REQUESTS SET client_completed_group_id = %s WHERE id = %s", (group_id, request_id, ))
        group_name = get_text_from_id(g.db, group_id, "D_CLIENT_COMPLETED_GROUPS")
        g.db.commit()
        return make_response(
                json.jsonify(message="Request #%d has moved to the group '%s'" % (request_id, group_name)), 200)

    elif request.method == "GET":
        cursor = g.db.cursor()
        my_user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM CICERON.V_REQUESTS WHERE client_user_id = %s AND client_completed_group_id = %s "
        else:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE client_user_id = %s AND client_completed_group_id = %s AND
           ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) )  """
        if 'since' in request.args.keys():
            query += "AND submitted_time < to_timestamp(%s) " % request.args.get('since')
        query += "ORDER BY submitted_time DESC"
        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (my_user_id, group_id, ))
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/incomplete', methods = ["GET"])
#@exception_detector
@login_required
def client_incompleted_items():
    cursor = g.db.cursor()
    user_id = get_user_id(g.db, session['useremail'])
    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM CICERON.V_REQUESTS WHERE status_id IN (-1,0,1) AND client_user_id = %s "
    else:
        query = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id IN (-1,0,1) AND client_user_id = %s AND
        ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """
    if 'since' in request.args.keys():
        query += "AND registered_time < to-timestamp(%s) " % request.args.get('since')
    query += " ORDER BY registered_time DESC LIMIT 20"
    if 'page' in request.args.keys():
        page = request.args.get('page')
        query += " OFFSET %d " % (( int(page)-1 ) * 20)

    cursor.execute(query, (user_id, ))
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/incomplete/<int:request_id>', methods = ["GET", "PUT", "DELETE", "POST"])
#@exception_detector
@login_required
def client_incompleted_item_control(request_id):
    if request.method == "GET":
        cursor = g.db.cursor()
        user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM CICERON.V_REQUESTS WHERE status_id IN (-1,0,1) AND client_user_id = %s AND request_id = %s "
        else:
            query = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id IN (-1,0,1) AND client_user_id = %s AND request_id = %s AND 
            ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) ) """
        if 'since' in request.args.keys():
            query += "AND registered_time < to_timestamp(%s) " % request.args.get('since')
        query += " ORDER BY registered_time DESC LIMIT 20"
        if 'page' in request.args.keys():
            page = request.args.get('page')
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (user_id, request_id))
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "PUT":
        # Only update due_time and price

        # It can be used in:
        #    1) Non-selected request
        #    2) Give more chance to the trusted translator

        cursor = g.db.cursor()
        parameters = parse_request(request)

        # Addional time: unit is second, counted from NOW
        additional_time_in_sec = int(parameters['user_additionalTime'])
        additional_price = 0
        if parameters.get('user_additionalPrice') != None:
            additional_price = float(parameters['user_additionalPrice'])

        # Notification
        query = "SELECT ongoing_worker_id, client_user_id FROM CICERON.F_REQUESTS WHERE id = %s"
        cursor.execute(query, (request_id, ))
        rs = cursor.fetchall()
        if rs[0][0] is not None:
            send_noti_lite(g.db, rs[0][0], 4, rs[0][1], request_id,
                optional_info={"hero": rs[0][1]})

        user_id = get_user_id(g.db, session['useremail'])
        # Change due date w/o addtional money
        if additional_price == 0:
            cursor.execute("UPDATE CICERON.F_REQUESTS SET due_time = CURRENT_TIMESTAMP + interval '+%s seconds', status_id = 0, registered_time = CURRENT_TIMESTAMP WHERE id = %s AND status_id = -1 AND client_user_id = %s AND ongoing_worker_id is null", (additional_time_in_sec, request_id, user_id))
            cursor.execute("UPDATE CICERON.F_REQUESTS SET due_time = CURRENT_TIMESTAMP + interval '+%s seconds', status_id = 1, registered_time = CURRENT_TIMESTAMP WHERE id = %s AND status_id = -1 AND client_user_id = %s AND ongoing_worker_id is not null", (additional_time_in_sec, request_id, user_id))
            g.db.commit()

            cursor.execute("SELECT registered_time, due_time, points FROM CICERON.F_REQUESTS WHERE id = %s", (request_id, ))
            rs = cursor.fetchone()
            request_registeredTime = rs[0]
            request_dueTime = rs[1]
            request_points = rs[2]

            return make_response(json.jsonify(
                message="Request #%d is renewed" % request_id,
                api=None,
                request_id=request_id,
                request_registeredTime=request_registeredTime,
                request_dueTime=request_dueTime,
                request_points=request_points), 200)

        # Change due date w/additional money
        else:
            cursor.execute("UPDATE CICERON.F_REQUESTS SET due_time = CURRENT_TIMESTAMP + interval '+%s seconds', status_id = 0, is_paid = false, points = points + %s WHERE id = %s AND status_id = -1 AND client_user_id = %s AND ongoing_worker_id is null", (additional_time_in_sec, additional_price, request_id, user_id))
            cursor.execute("UPDATE CICERON.F_REQUESTS SET due_time = CURRENT_TIMESTAMP + interval '+%s seconds', status_id = 1, is_paid = true, points = points + %s WHERE id = %s AND status_id = -1 AND client_user_id = %s AND ongoing_worker_id is not null", (additional_time_in_sec, additional_price, request_id, user_id))
            g.db.commit()

            cursor.execute("SELECT registered_time, due_time, points FROM CICERON.F_REQUESTS WHERE id = %s", (request_id, ))
            rs = cursor.fetchone()
            request_registeredTime = rs[0]
            request_dueTime = rs[1]
            request_points = rs[2]

            return make_response(json.jsonify(
                message="Request #%d is renewed. Please execute the API provided with POST method" % request_id,
                api="/api/user/requests/%d/payment/start"%request_id,
                additional_price=additional_price,
                request_id=request_id,
                request_registeredTime=request_registeredTime,
                request_dueTime=request_dueTime,
                request_points=request_points), 200)

    elif request.method == "POST":
        # It can be used in:
        #    1) Say goodbye to translator, back to stoa

        cursor = g.db.cursor()
        parameters = parse_request(request)

        # Addional time: unit is second, counted from NOW
        additional_time_in_sec = int(parameters['user_additionalTime'])
        additional_price = 0
        if parameters.get('user_additionalPrice') != None:
            additional_price = float(parameters['user_additionalPrice'])

        user_id = get_user_id(g.db, session['useremail'])
        # Change due date w/o addtional money
        if additional_price == 0:
            cursor.execute("UPDATE CICERON.F_REQUESTS SET due_time = CURRENT_TIMESTAMP + interval '+%s seconds', status_id = 0, ongoing_worker_id = null, registered_time = CURRENT_TIMESTAMP WHERE id = %s AND status_id = -1 AND client_user_id = %s", (additional_time_in_sec, request_id, user_id) )
            g.db.commit()

            cursor.execute("SELECT registered_time, due_time, points FROM CICERON.F_REQUESTS WHERE id = %s", (request_id, ))
            rs = cursor.fetchone()
            request_registeredTime = rs[0]
            request_dueTime = rs[1]
            request_points = rs[2]

            return make_response(json.jsonify(
                message="Request #%d is posted back to stoa." % request_id,
                request_id=request_id,
                api=None,
                request_registeredTime=request_registeredTime,
                request_dueTime=request_dueTime,
                request_points=request_points), 200) 

        # Change due date w/additional money
        else:
            cursor.execute("UPDATE CICERON.F_REQUESTS SET due_time = CURRENT_TIMESTAMP + interval '+%s seconds', status_id = 0, is_paid = false, points = points + %s, ongoing_worker_id = null, registered_time = CURRENT_TIMESTAMP WHERE id = %s AND status_id = -1 AND client_user_id = %s ", (additional_time_in_sec, additional_price, request_id, user_id))
            g.db.commit()

            cursor.execute("SELECT registered_time, due_time, points FROM CICERON.F_REQUESTS WHERE id = %s", (request_id, ))
            rs = cursor.fetchone()
            request_registeredTime = rs[0]
            request_dueTime = rs[1]
            request_points = rs[2]

            return make_response(json.jsonify(
                message="Request #%d is renewed. Please execute the API provided with POST methid" % request_id,
                request_id=request_id,
                additional_price=additional_price,
                api="/api/user/requests/%d/payment/start"%request_id,
                request_registeredTime=request_registeredTime,
                request_dueTime=request_dueTime,
                request_points=request_points), 200)

    elif request.method == "DELETE":
        # It can be used in:
        #    1) Say goodbye to translator. And he/she don't want to leave his/her request
        cursor = g.db.cursor()
        user_id = get_user_id(g.db, session['useremail'])

        cursor.execute("SELECT points FROM CICERON.F_REQUESTS WHERE id = %s AND status_id IN (-1,0) AND client_user_id = %s AND is_paid = true ", (request_id, user_id))
        ret = cursor.fetchone()
        points = None
        if ret is None or len(ret) == 0:
            #return make_response(json.jsonify(
            #    message="The point has already refunded about this request.",
            #    request_id=request_id), 402)
            points = 0.0
            
        else:
            points = float(ret[0])

        cursor.execute("UPDATE CICERON.REVENUE SET amount = amount + %s WHERE id = %s", (points, user_id))

        cursor.execute("UPDATE CICERON.F_REQUESTS SET is_paid = false, status_id = -2 WHERE id = %s AND status_id IN (-1,0) AND client_user_id = %s ", (request_id, user_id))

        g.db.commit()

        # Notification
        query = "SELECT ongoing_worker_id, client_user_id FROM CICERON.F_REQUESTS WHERE id = %s"
        cursor.execute(query, (request_id, ))
        rs = cursor.fetchall()
        if rs[0][0] != None and rs[0][1] != None:
            send_noti_lite(g.db, rs[0][0], 3, rs[0][1], request_id)
            update_user_record(g.db, translator_id=rs[0][1])

        update_user_record(g.db, client_id=rs[0][0])

        g.db.commit()

        return make_response(json.jsonify(
            message="Your request #%d is deleted. Your points USD %.2f is backed in your account" % (request_id, points),
            points=points,
            request_id=request_id), 200)

@app.route('/api/user/requests/<int:request_id>/payment/checkPromoCode', methods = ["POST"])
#@exception_detector
@login_required
def check_promotionCode(request_id):
    user_id = get_user_id(g.db, session['useremail'])
    parameters = parse_request(request)

    code = parameters['promoCode'].upper()

    isCommonCode, commonPoint, commonMessage = commonPromotionCodeChecker(g.db, user_id, code)
    isIndivCode, indivPoint, indivMessage = individualPromotionCodeChecker(g.db, user_id, code)
    if isCommonCode in [1, 2]:
        return make_response(json.jsonify(
            promoType=None, message=commonMessage, code=isCommonCode, point=0), 402)
    elif isIndivCode in [1, 2]:
        return make_response(json.jsonify(
            promoType=None, message=indivMessage, code=isIndivCode, point=0), 402)

    elif isCommonCode == 0:
        return make_response(json.jsonify(
            promoType='common', message=commonMessage, code=0, point=commonPoint), 200)
    elif isIndivCode == 0:
        return make_response(json.jsonify(
            promoType='indiv', message=indivMessage, code=0, point=indivPoint), 200)

    else:
        return make_response(json.jsonify(
            promoType=None, message="There is no promo code matched,", code=3, point=0), 405)
        
@app.route('/api/user/requests/<int:request_id>/payment/start', methods = ["POST"])
#@exception_detector
@login_required
def pay_for_request(request_id):
    parameters = parse_request(request)

    pay_by = parameters.get('pay_by')
    pay_via = parameters.get('pay_via')
    total_amount = float(parameters['pay_amount'])
    use_point = float(parameters.get('use_point', 0))

    promo_type = parameters.get('promo_type', 'null')
    promo_code = parameters.get('promo_code', 'null')

    # Check whether the price exceeds the client's money purse.
    amount = None
    user_id = get_user_id(g.db, session['useremail'])

    host_ip = os.environ.get('HOST', app.config['HOST'])
    
    payload = None
    if pay_via == 'iamport':
        payload = {}

        payload['card_number'] = parameters['card_number']
        payload['expiry'] = parameters['expiry']
        payload['birth'] = parameters['birth']
        payload['pwd_2digit'] = parameters['pwd_2digit']

    status_code, provided_link, current_point = payment_start(g.db, pay_by, pay_via, request_id, total_amount, user_id, host_ip, use_point=use_point, promo_type=promo_type, promo_code=promo_code, payload=payload)

    if status_code == 'point_exceeded_than_you_have':
        return make_response(json.jsonify(
            message="You requested to use your points more than what you have. Price: %.2f, Your purse: %.2f" % (use_point, current_point)), 402)

    elif status_code == 'paypal_error':
        return make_response(json.jsonify(
            message="Something wrong in paypal"), 400)

    elif status_code == 'paypal_success':
        return make_response(json.jsonify(
            message="Redirect link is provided!",
            link=provided_link), 200)

    elif status_code == 'alipay_success':
        return make_response(json.jsonify(
            message="Link to Alipay is provided.",
            link=provided_link), 200)

    elif status_code == 'iamport_error':
        return make_response(json.jsonify(
            message="Something wrong in iamport"), 400)

    elif status_code == 'iamport_success':
        return make_response(json.jsonify(message="Iamport success",
            link="%s%s" % (HOST, '/stoa')), 200)

    elif status_code == 'point_success':
        return make_response(json.jsonify(message="Point success",
            link="%s%s" % (HOST, '/stoa')), 200)

@app.route('/api/user/requests/<int:request_id>/payment/postprocess', methods = ["GET"])
#@exception_detector
def pay_for_request_process(request_id):
    cursor = g.db.cursor()
    user = request.args['user_id']
    user_id = get_user_id(g.db, user)
    pay_via = request.args['pay_via']
    pay_by = request.args['pay_by']
    is_success = True if request.args['status'] == "success" else False
    amount = float(request.args.get('pay_amt'))
    use_point = float(request.args.get('use_point', 0))

    promo_type = request.args.get('promo_type', 'null')
    promo_code = request.args.get('promo_code', 'null')

    is_additional = request.args.get('is_additional', 'false')

    status_code = payment_postprocess(g.db, pay_by, pay_via, request_id, user_id, is_success, amount,
            use_point=use_point, promo_type=promo_type, promo_code=promo_code, is_additional=is_additional)

    if status_code == 'no_record':
        return redirect(HOST, code=302)

    if pay_by == "web":
        return redirect("%s%s" % (HOST, '/stoa'), code=302)
        #return make_response("OK", 200)
    elif pay_by == "mobile":
        return redirect("%s%s" % (HOST, '/stoa'), code=302)

@app.route('/api/user/translations/<int:request_id>', methods=["GET"])
@login_required
#@exception_detector
@translator_checker
def getOneTicketOfHero(request_id):
    if request.method == "GET":
        # Request method: GET
        # Parameters
        #     since(optional): Timestamp, take recent 20 post before the timestamp.
        #                  If this parameter is not provided, recent 20 posts from now are returned
        cursor = g.db.cursor()
        query = """SELECT status_id FROM CICERON.V_REQUESTS WHERE request_id = %s"""
        cursor.execute(query, (request_id, ) )
        rs = cursor.fetchone()

        if rs is None or len(rs) == 0:
            return make_response(json.jsonify(
                message="Invalid request"), 404)
        status_id = rs[0]

        if status_id in [0, -1]:
            return redirect(url_for('translation_incompleted_items_each', request_id=request_id))
        elif status_id == 1:
            return redirect(url_for('working_translate_item', request_id=request_id))
        elif status_id == 2:
            return redirect(url_for('translation_completed_items_detail', request_id=request_id))
        else:
            return make_response(json.jsonify(
                message="Invalid request"), 404)

@app.route('/api/user/requests/<int:request_id>', methods=["GET"])
#@exception_detector
def getOneTicketOfClient(request_id):
    if request.method == "GET":
        # Request method: GET
        # Parameters
        #     since(optional): Timestamp, take recent 20 post before the timestamp.
        #                  If this parameter is not provided, recent 20 posts from now are returned
        cursor = g.db.cursor()
        query = """SELECT status_id FROM CICERON.V_REQUESTS WHERE request_id = %s"""
        cursor.execute(query, (request_id, ) )
        rs = cursor.fetchone()

        if rs is None or len(rs) == 0:
            return make_response(json.jsonify(
                message="Invalid request"), 404)
        status_id = rs[0]

        if status_id in [0, -1]:
            return redirect(url_for('client_incompleted_item_control', request_id=request_id))
        elif status_id == 1:
            return redirect(url_for('show_ongoing_item_client', request_id=request_id))
        elif status_id == 2:
            return redirect(url_for('client_completed_items_detail', request_id=request_id))
        else:
            return make_response(json.jsonify(
                message="Invalid request"), 404)

@app.route('/api/user/requests/ongoing/i18n/<int:request_id>', methods=["GET"])
#@exception_detector
@login_required
def i18n_getData_ongoing(request_id):
    cursor = g.db.cursor()
    user_id = get_user_id(g.db, session['useremail'])

    is_user_request = clientAuthChecker(g.db, user_id, request_id, 1)
    if is_user_request == False:
        return make_response(json.jsonify(
            message="Not your request"), 406)

    if session['useremail'] in super_user:
        query = "SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 1 AND client_user_id = %s AND request_id = %s "
    else:
        query = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 1 AND client_user_id = %s AND request_id = %s AND
         ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) )  """
    if 'since' in request.args.keys():
        query += "AND submitted_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += " ORDER BY submitted_time DESC LIMIT 20"
    if 'page' in request.args.keys():
        page = request.args.get('page')
        query += " OFFSET %d " % (( int(page)-1 ) * 20)

    cursor.execute(query, (user_id, request_id, ))
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")

    i18nObj = I18nHandler(g.db)

    return make_response(json.jsonify(
        data=result,
        realData=i18nObj.jsonResponse(request_id, is_restricted=True)
        ), 200)

@app.route('/api/user/requests/complete/i18n/<int:request_id>', methods=["GET"])
#@exception_detector
@login_required
def i18n_getData_complete(request_id):
    cursor = g.db.cursor()
    user_id = get_user_id(g.db, session['useremail'])

    is_user_request = clientAuthChecker(g.db, user_id, request_id, 2)
    if is_user_request == False:
        return make_response(json.jsonify(
            message="Not your request"), 406)

    if session['useremail'] in super_user:
        query = "SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 2 AND client_user_id = %s AND request_id = %s "
    else:
        query = """SELECT * FROM CICERON.V_REQUESTS WHERE status_id = 2 AND client_user_id = %s AND request_id = %s AND
         ( (is_paid = true AND is_need_additional_points = false) OR (is_paid = true AND is_need_additional_points = true AND is_additional_points_paid = true) )  """
    if 'since' in request.args.keys():
        query += "AND submitted_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += " ORDER BY submitted_time DESC LIMIT 20"
    if 'page' in request.args.keys():
        page = request.args.get('page')
        query += " OFFSET %d " % (( int(page)-1 ) * 20)

    cursor.execute(query, (user_id, request_id, ))
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")

    i18nObj = I18nHandler(g.db)

    return make_response(json.jsonify(
        data=result,
        realData=i18nObj.jsonResponse(request_id, is_restricted=False)
        ), 200)

@app.route('/api/user/requests/complete/i18n/<int:request_id>/download', methods=["GET"])
#@exception_detector
@login_required
def i18n_download(request_id):
    user_id = get_user_id(g.db, session['useremail'])
    is_user_request = clientAuthChecker(g.db, user_id, request_id, 2)
    if is_user_request == False:
        return make_response(json.jsonify(
            message="Not your request"), 406)

    i18nObj = I18nHandler(g.db)
    download_format = request.args.get('format', 'json')
    download_binary = None

    if   download_format == 'android':
        filename, download_binary = i18nObj.exportAndroid(request_id)
    elif download_format == 'iOS':
        filename, download_binary = i18nObj.exportIOs(request_id)
    elif download_format == 'unity':
        filename, download_binary = i18nObj.exportUnity(request_id)
    elif download_format == 'json':
        filename, download_binary = i18nObj.exportJson(request_id)
    elif download_format == 'xamarin':
        filename, download_binary = i18nObj.exportXamarin(request_id)

    return send_file(io.BytesIO(download_binary), attachment_filename=filename)

@app.route('/api/user/device', methods = ["POST"])
#@exception_detector
@login_required
def register_or_update_register_id():
    cursor = g.db.cursor()
    parameters = parse_request(request)

    device_os = parameters['user_deviceOS']
    reg_key = parameters['user_regKey']
    user_id = get_user_id(g.db, session['useremail'])

    record_id = get_new_id(g.db, "D_MACHINES")
    cursor.execute("SELECT count(*) FROM CICERON.D_MACHINES WHERE os_id = (SELECT id FROM CICERON.D_MACHINE_OSS WHERE text = %s) AND user_id = %s",
            (device_os, user_id))
    num = cursor.fetchall()[0][0]

    if num == 0:
        cursor.execute("INSERT INTO CICERON.D_MACHINES VALUES (%s, %s, (SELECT id FROM CICERON.D_MACHINE_OSS WHERE text = %s), %s, %s)",
            (record_id, user_id, device_os, True, reg_key))
    else:
        cursor.execute("UPDATE CICERON.D_MACHINES SET reg_key = %s WHERE os_id = (SELECT id FROM CICERON.D_MACHINE_OSS WHERE text = %s) AND user_id = %s",
            (reg_key, device_os, user_id))

    g.db.commit()

    return make_response(json.jsonify(message="Succefully updated/inserted"), 200)

@app.route('/api/access_file/profile_pic/<user_id>/<fake_filename>')
@login_required
def access_profile_pic(user_id, fake_filename):
    cursor = g.db.cursor()
    query_getPic = "SELECT bin FROM CICERON.F_USER_PROFILE_PIC WHERE user_id = %s"
    cursor.execute(query_getPic, (user_id, ))
    profile_pic = cursor.fetchone()
    if profile_pic is None:
        return make_response(json.jsonify(message="No profile pic"), 404)
    else:
        return send_file(io.BytesIO(profile_pic[0]), attachment_filename=fake_filename)

@app.route('/api/access_file/request_pic/<photo_id>/<fake_filename>')
@login_required
def access_request_pic(photo_id, fake_filename):
    cursor = g.db.cursor()
    user_id = get_user_id(g.db, session['useremail'])
    query_checkAuth = """
        SELECT photo_id FROM CICERON.F_REQUESTS
        WHERE (client_user_id = %s OR ongoing_worker_id = %s) AND photo_id = %s
        """
    cursor.execute(query_checkAuth, (user_id, user_id, photo_id))
    checkAuth = cursor.fetchone()
    if checkAuth is None:
        return make_response(json.jsonify(message="Only requester or translator can see the file"), 401)

    query_getPic = "SELECT bin FROM CICERON.D_REQUEST_PHOTOS  WHERE id = %s"
    cursor.execute(query_getPic, (photo_id, ))
    request_pic = cursor.fetchone()
    if request_pic is None:
        return make_response(json.jsonify(message="No request pic"), 404)
    else:
        return send_file(io.BytesIO(request_pic[0]), attachment_filename=fake_filename)

@app.route('/api/access_file/request_sounds/<sound_id>/<fake_filename>')
@login_required
def access_request_sound(sound_id, fake_filename):
    cursor = g.db.cursor()
    user_id = get_user_id(g.db, session['useremail'])
    query_checkAuth = """
        SELECT photo_id FROM CICERON.F_REQUESTS
        WHERE (client_user_id = %s OR ongoing_worker_id = %s) AND sound_id = %s
        """
    cursor.execute(query_checkAuth, (user_id, user_id, sound_id))
    checkAuth = cursor.fetchone()
    if checkAuth is None:
        return make_response(json.jsonify(message="Only requester or translator can see the file"), 401)

    query_getSound = "SELECT bin FROM CICERON.D_REQUEST_SOUNDS  WHERE id = %s"
    cursor.execute(query_getSound, (sound_id, ))
    request_sound = cursor.fetchone()
    if request_sound is None:
        return make_response(json.jsonify(message="No request sound"), 404)
    else:
        return send_file(io.BytesIO(request_sound[0]), attachment_filename=fake_filename)

@app.route('/api/access_file/request_doc/<doc_id>/<fake_filename>')
@login_required
def access_request_file(doc_id, fake_filename):
    cursor = g.db.cursor()
    user_id = get_user_id(g.db, session['useremail'])
    query_checkAuth = """
        SELECT photo_id FROM CICERON.F_REQUESTS
        WHERE (client_user_id = %s OR ongoing_worker_id = %s) AND file_id = %s
        """
    cursor.execute(query_checkAuth, (user_id, user_id, doc_id))
    checkAuth = cursor.fetchone()
    if checkAuth is None:
        return make_response(json.jsonify(message="Only requester or translator can see the file"), 401)

    query_getFile = "SELECT bin FROM CICERON.D_REQUEST_FILES  WHERE id = %s"
    cursor.execute(query_getFile, (doc_id, ))
    request_file = cursor.fetchone()
    if request_file is None:
        return make_response(json.jsonify(message="No request file"), 404)
    else:
        return send_file(io.BytesIO(request_file[0]), attachment_filename=fake_filename)

@app.route('/api/access_file/img/<filename>')
def mail_img(filename):
    return send_from_directory('img', filename)

@app.route('/api/action_record', methods = ["POST"])
@login_required
#@exception_detector
def record_user_location():
    cursor = g.db.cursor()
    parameters = parse_request(request)
    
    user_id = get_user_id(g.db, session['useremail'])
    lati = parameters.get('lat')
    longi = parameters.get('long')
    method = parameters.get('method')
    api = parameters.get('api')
    request_id = parameters.get('request_id')
    cursor.execute("INSERT INTO CICERON.USER_ACTIONS VALUES (%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)", 
            (user_id, lati, longi, method, api, request_id))
    g.db.commit()
    return make_response(json.jsonnify(
        message="Logged successfully"), 200)

@app.route('/api/notification', methods = ["GET"])
@login_required
#@exception_detector
def get_notification():
    cursor = g.db.cursor()
    user_id = get_user_id(g.db, session['useremail'])

    # Count whole unread noti
    query_noti = """SELECT count(*) FROM CICERON.V_NOTIFICATION WHERE user_id = %s and is_read = false """
    cursor.execute(query_noti, (user_id, ))
    numberOfNoti = cursor.fetchall()[0][0]

    query = """SELECT noti.user_name,
                      noti.user_profile_pic_path,
                      noti.noti_type_id,
                      noti.request_id,
                      noti.target_user_name,
                      noti.ts,
                      noti.is_read,
                      noti.target_profile_pic_path,
                      CASE WHEN noti.expected_time is not null THEN (noti.expected_time - CURRENT_TIMESTAMP) ELSE null END as expectedDue,
                      noti.context,
                      noti.status_id,
                      CASE WHEN noti.expected_time is null THEN false ELSE true END as expectedDue_replied,
                      noti.id
            FROM CICERON.V_NOTIFICATION noti LEFT OUTER JOIN CICERON.F_REQUESTS req ON noti.request_id = req.id
            WHERE noti.user_id = %s AND req.status_id != -2 """
    if 'since' in request.args.keys():
        query += "AND ts < to_timestamp(%s) " % request.args.get('since')
    query += "ORDER BY ts DESC LIMIT 10 "

    if 'page' in request.args.keys():
        page = int(request.args.get('page', 1))
        query += " OFFSET %d" % ((page-1) * 10)
    cursor.execute(query, (user_id, ))
    rs = cursor.fetchall()

    result = []
    for item in rs:
        row = {}

        isAlert, alertType, link = getRoutingAddressAndAlertType(g.db, user_id, item[3], item[2])

        row['username'] = item[0]
        row['profilePic'] = item[1]
        row['noti_typeId'] = item[2]
        row['request_id'] = item[3]
        row['target_username'] = item[4]
        row['target_userProfilePic'] = item[7]
        row['ts'] = int(item[5].strftime("%s")) * 1000
        row['is_read'] = parameter_to_bool(item[6])
        row['link'] = link
        row['isAlert'] = isAlert
        row['alertType'] = alertType
        row['abstract'] = item[9]
        row['request_status'] = item[10]

        #row['expectedDue'] = (string2Date(item[8])-datetime.now()).total_seconds() if item[8] != None else None
        row['expectedDue'] = item[8].total_seconds() * 1000 if item[8] != None else None
        row['expectedDue_replied'] = item[11]
        row['noti_id'] = item[12]

        result.append(row)

    return make_response(json.jsonify(
        numberOfNoti=numberOfNoti,
        message="Notifications",
        data=result), 200)

@app.route('/api/notification/read', methods = ["GET"])
@login_required
#@exception_detector
def read_notification():
    cursor = g.db.cursor()
    user_id = get_user_id(g.db, session['useremail']) 
    if 'noti_id' in request.args.keys():
        query = """UPDATE CICERON.F_NOTIFICATION SET is_read = true WHERE id = %s """
        noti_id = request.args.get('noti_id')
        cursor.execute(query, (noti_id, ))

    #else:
    #    query = """UPDATE CICERON.F_NOTIFICATION SET is_read = true WHERE id IN (SELECT id FROM CICERON.F_NOTIFICATION WHERE user_id = %s ORDER BY ts DESC) """
    #    cursor.execute(query, (user_id, ))

    g.db.commit()

    return make_response(json.jsonify(
        message="Notis are marked as read"), 200)

@app.route('/api/user/payback', methods = ["GET", "POST"])
@login_required
#@exception_detector
def register_payback():
    if request.method == "GET":
        # GET payback list
        cursor = g.db.cursor()
        user_id = get_user_id(g.db, session['useremail'])
        cursor.execute("""SELECT id, order_no, bank_name, account_no, request_time, amount, is_returned
            FROM CICERON.RETURN_MONEY_BANK_ACCOUNT
            WHERE user_id = %s
            ORDER BY id DESC""", (user_id, ))

        rs = cursor.fetchall()
        result = []
        for item in rs:
            item = {
                    'id': item[0],
                    'orderNo': item[1],
                    'bankName': item[2],
                    'accountNo': item[3],
                    'requestTime': item[4],
                    'amount': item[5],
                    'isReturned': item[6]
                    }
            result.append(item)

        return make_response(json.jsonify(
            data=result), 200)

    elif request.method == "POST":
        # POST new payback request
        cursor = g.db.cursor()
        parameters = parse_request(request)

        user_id = get_user_id(g.db, session['useremail'])
        bank_name = parameters['bankName']
        account_no = parameters['accountNo']
        amount = float(parameters['amount'])

        # Test whether requested amount is exceeded the money in user's account
        cursor.execute("SELECT amount FROM CICERON.REVENUE WHERE id = %s",  (user_id, ))
        revenue_amount = cursor.fetchall()[0][0]

        if revenue_amount < amount:
            return make_response(json.jsonify(
                message="User cannot request paid back. Revenue: %f, Requested amount: %f" % (revenue_amount, amount)), 402)

        new_id = get_new_id(g.db, "RETURN_MONEY_BANK_ACCOUNT")
        order_no = datetime.strftime(datetime.now(), "%Y%m%d") + random_string_gen(size=4)
        cursor.execute("INSERT INTO CICERON.RETURN_MONEY_BANK_ACCOUNT VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP,%s,false,null)",
                (new_id, order_no, user_id, bank_name, account_no, amount))
        g.db.commit()

        return make_response(json.jsonify(
            message="Payback request is successfully received"), 200)
        
@app.route('/api/user/point_detail', methods = ["GET"])
@login_required
#@exception_detector
def point_detail():
    cursor = g.db.cursor()
    user_id = get_user_id(g.db, session['useremail'])

    query = """
    SELECT * FROM (
    SELECT 2 as message_id, request_time, -1 * amount as points, is_returned, return_time FROM CICERON.RETURN_MONEY_BANK_ACCOUNT WHERE user_id = %s
    UNION
    SELECT 1 as message_id, registered_time as request_time, points, null as is_returned, null as return_time
    FROM CICERON.F_REQUESTS WHERE status_id = 2 AND is_paid = true AND ongoing_worker_id = %s AND points > 0
    UNION
    SELECT 0 as message_id, registered_time as request_time, points, null as is_returned, null as return_time
    FROM CICERON.F_REQUESTS WHERE status_id = -2 AND is_paid = false AND client_user_id = %s) total
    order by request_time desc LIMIT 20 """

    if 'page' in request.args.keys():
        page = request.args.get('page')
        query += " OFFSET %d " % (( int(page)-1 ) * 20)

    cursor.execute(query, (user_id, user_id, user_id, ))
    rs = cursor.fetchall()

    result = []
    for message_id, requested_time, points, is_returned, return_time in rs:
        item = {
            'message_id': message_id,
            'requested_time': requested_time,
            'points': points,
            'is_returned': is_returned,
            'return_time': return_time
        }
        result.append(item)

    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/payback_email', methods = ["GET"])
@login_required
#@exception_detector
def register_paybacki_email():
    cursor = g.db.cursor()
    mail_to = session['useremail']
    user_id = get_user_id(g.db, mail_to)
    cursor.execute("SELECT name FROM CICERON.D_USERS WHERE id = %s", (user_id, ))
    name = cursor.fetchone()[0]

    subject = 'Please reply for your refund request'

    doc_no = random_string_gen(size=12)
    message="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(name)s,</h1></span><br>
                 <br>
                 Thank you for being with Ciceron!<br>
                 Is it fun to work with us? We wish that it had been, and would be good time!<br>
                 If there is any problem with our system, don'y hesitate to contact us by <a href="mailto:contact@ciceron.me">this mail!</a><br>
                 <br>
                 For your refund request, please fill out the information below and reply to us!<br>
                 <br>
                 <b>Name of the bank</b>:<br>
                 <b>Account no.</b>:<br>
                 <b>Amount</b>:<br>
                 <br>
                 Have a wonderful day! :)<br>
                 We are looking for your reply!<br>
                 <br>
                 Best regards,<br>
                 Ciceron team<br>
                 <br>
                 <br>
                 ##### PLEASE DO NOT DELETE THE TEXT BELOW #####<br>
                 %(doc_no)s<br>
                 ##### PLEASE DO NOT DELETE THE TEXT ABOVE #####""" % {'doc_no': doc_no, 'name': name, 'host': HOST}

    send_mail(mail_to, subject, message, mail_from='contact@ciceron.me')

    return make_response(json.jsonify(
        message='Request mail is sent!'), 200)
                
@app.route('/api/user/payback/<str_id>/<order_no>', methods = ["PUT", "DELETE"])
@login_required
#@exception_detector
def revise_payback(str_id, order_no):
    if request.method == "PUT":
        cursor = g.db.cursor()
        user_id = get_user_id(g.db, session['useremail'])
        parameters = parse_request(request)

        bank_name = parameters.get('bankName')
        account_no = parameters.get('accountNo')
        amount = float(parameters.get('amount')) if parameters.get('amount') != None else None

        if bank_name != None:
            cursor.execute("UPDATE CICERON.RETURN_MONEY_BANK_ACCOUNT SET bank_name = %s WHERE id = %s AND order_no = %s AND user_id = %s", (bank_name, int(str_id), order_no, user_id))
        if account_no != None:
            cursor.execute("UPDATE CICERON.RETURN_MONEY_BANK_ACCOUNT SET account_no = %s WHERE id = %s AND order_no = %s AND user_id = %s", (account_no, int(str_id), order_no, user_id))
        if amount != None:
            # Test whether requested amount is exceeded the money in user's account
            cursor.execute("SELECT amount FROM CICERON.REVENUE WHERE id = %s",  (user_id, ))
            revenue_amount = cursor.fetchall()[0][0]

            if revenue_amount < amount:
                return make_response(json.jsonify(
                    message="User cannot paid back. Revenue: %f, Requested amount: %f" % (revenue_amount, amount)), 402)

            cursor.execute("UPDATE CICERON.RETURN_MONEY_BANK_ACCOUNT SET amount = %s WHERE id = %s AND order_no = %s AND user_id = %s", (amount, int(str_id), order_no, user_id) )
            
        g.db.commit()

        return make_response(json.jsonify(
            message="Payback request is updated"), 200)

    elif request.method == "DELETE":
        cursor = g.db.cursor()
        user_id = get_user_id(g.db, session['useremail'])
        cursor.execute("DELETE FROM CICERON.RETURN_MONEY_BANK_ACCOUNT WHERE id = %s AND order_no = %s ", (int(str_id), order_no))
        g.db.commit()

        return make_response(json.jsonify(
            message="Payback request has just been deleted."), 200)

@app.route('/api/user/be_hero', methods=['POST'])
@login_required
#@exception_detector
def be_hero():
    cursor = g.db.cursor()
    parameters = parse_request(request)
    email = parameters['email']

    name = parameters['name']
    school = parameters.get('school', "")
    major = parameters.get('major', "")
    language = parameters['language']
    residence = parameters.get('residence', "")
    score = parameters.get('score', "")

    doc_no = random_string_gen(size=12)

    subject = "Welcome to Ciceron, hero candidate %s!" % name
    message="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(name)s,</h1></span><br>
                 <br>
                 Thank you for applying to the hero!<br>
                 <br>
                 Please reply this mail with the form below and supporting documents.<br>
                 <b>Name</b>: %(name)s<br>
                 <b><u>(Supporting document needed)</u> Education and school(or occupation)</b>: %(school)s<br>
                 <b><u>(Supporting document needed)</u> Major</b>: %(major)s<br>
                 <b>Applying language</b>: %(language)s<br>
                 <b>Residence</b>: %(residence)s<br>
                 <b><u>(Supporting document needed)</u> Qualifications, score, or supporting experience(optional)</b>: %(score)s<br>
                 <br>
                 Have a wonderful day! :)<br>
                 We are looking for your reply!<br>
                 <br>
                 Best regards,<br>
                 Ciceron team<br>
                 <br>
                 <br>
                 ##### PLEASE DO NOT DELETE THE TEXT BELOW #####<br>
                 %(doc_no)s<br>
                 ##### PLEASE DO NOT DELETE THE TEXT ABOVE #####""" % {
                         'name': name,
                         'school': school,
                         'major': major,
                         'language': language,
                         'residence': residence,
                         'score': score,
                         'doc_no': doc_no,
                         "host": HOST + ':5000'
                         }

    send_mail(email, subject, message, mail_from='hero@ciceron.me')

    user_id = get_user_id(g.db, session['useremail'])
    cursor.execute("UPDATE CICERON.D_USERS SET trans_request_state = 1 WHERE id = %s", (user_id, ) )
    g.db.commit()

    return make_response(json.jsonify(
        message="Application mail has just sent to %s!" % email), 200)

################################################################################
#########                        ADMIN TOOL                            #########
################################################################################

@app.route('/api/admin/language_assigner', methods = ["POST"])
#@exception_detector
@admin_required
def language_assigner():
    cursor = g.db.cursor()
    parameters = parse_request(request)

    user_email = parameters['email']
    language_id = int(parameters['language_id'])
    user_id = get_user_id(g.db, user_email)
    new_translation_list_id = get_new_id(g.db, "D_TRANSLATABLE_LANGUAGES")

    cursor.execute("UPDATE CICERON.D_USERS SET is_translator = true, trans_request_state = 2 WHERE id = %s ", (user_id, ))
    cursor.execute("SELECT language_id FROM CICERON.D_TRANSLATABLE_LANGUAGES WHERE user_id = %s and language_id = %s ", (user_id, language_id))
    rs = cursor.fetchall()
    if len(rs) == 0:
        cursor.execute("INSERT INTO CICERON.D_TRANSLATABLE_LANGUAGES VALUES (%s,%s,%s)", (new_translation_list_id, user_id, language_id))
    g.db.commit()
    return make_response(json.jsonify(message="Language added successfully"), 200)

@app.route('/api/admin/language_rejector', methods = ["POST"])
#@exception_detector
@admin_required
def language_rejector():
    cursor = g.db.cursor()
    parameters = parse_request(request)

    user_email = parameters['email']
    user_id = get_user_id(g.db, user_email)

    cursor.execute("UPDATE CICERON.D_USERS SET trans_request_state = CASE WHEN is_translator = false THEN 0 WHEN is_translator = true THEN 2 END WHERE id = %s", (user_id, ))
    g.db.commit()
    return make_response(json.jsonify(message="Language added successfully"), 200)

@app.route('/api/admin/payback_list', methods=["GET", "POST"])
#@exception_detector
@admin_required
def return_money():
    if request.method == "POST":
        # We've not prepared for card payback.

        #parameters = parse_request(request)
        #user_id = get_user_id(session['useremail'])
        #where_to_return = parameters['user_whereToReturn']
        #payment_id = parameters['user_PaymentId']
        #money_amount = parameters['user_revenue']

        ## Logic flow
        ##   1) Check how much money in user's revenue
        ##     - If request amount is exceeded user's revenue, reject refund request.
        ##   2) Send via paypal

        ## SANDBOX
        #API_ID = "APP-80W284485P519543T"
        #API_USER = "contact-facilitator_api1.ciceron.me"
        #API_PASS = 'R8H3MF9EQYTNHD22'
        #API_SIGNATURE = 'ABMADzBsLmPPJmWRmjvj6KuGeZ4MAoDQ7X0sCtehblA93Yolgrjto1tO'

        ## Live
        ## API_ID = 'Should be issued later'
        ## API_USERNAME = 'contact_api1.ciceron.me'
        ## API_PASS = 'GJ5JNF596R3VNBK4'
        ## API_SIGNATURE = 'AiPC9BjkCyDFQXbSkoZcgqH3hpacAqbVr1jqSkiaKlwohFFSWhFvOxwI'

        ## END POINT = https://svcs.sandbox.paypal.com/AdaptivePayments/Pay
        ## POST
        ## Input header:
        ## X-PAYPAL-APPLICATION-ID = API_ID
        ## X-PAYPAL-SECURITY-USERID = API_USER
        ## X-PAYPAL-SECURITY-PASSWORD = API_PASS
        ## X-PAYPAL-SECURITY-SIGNATURE = API_SIGNATURE
        ## X-PAYPAL-DEVICE-IPADDRESS = IP_ADDRESS
        ## X-PAYPAL-REQUEST-DATA-FORMAT = 'JSON'
        ## X-PAYPAL-RESPONSE-DATA-FORMAT = 'JSON'

        #body = {"returnUrl":"http://example.com/returnURL.htm",
        #        "requestEnvelope":
        #           {"errorLanguage":"en_KR"},
        #        "currencyCode":"USD",
        #        "receiverList":{
        #            "receiver":
        #            [{"email":"psy2848048@gmail.com","amount":"10.00",}]
        #            },
        #        "cancelUrl":"http://example.com/cancelURL.htm",
        #        "actionType":"PAY"}

        cursor = g.db.cursor()
        parameters = parse_request(request)
        id_order = parameters['id']
        order_no = parameters['orderNo']

        cursor.execute("SELECT user_id, amount FROM CICERON.RETURN_MONEY_BANK_ACCOUNT WHERE id = %s AND order_no = %s", (int(id_order), order_no))
        rs = cursor.fetchall()
        user_id = rs[0][0]
        amount = rs[0][1]

        cursor.execute("UPDATE CICERON.RETURN_MONEY_BANK_ACCOUNT SET is_returned = true, return_time = CURRENT_TIMESTAMP WHERE id = %s AND order_no = %s", (id_order, order_no))
        cursor.execute("UPDATE CICERON.REVENUE SET amount = amount - %s WHERE id = %s ", (amount, user_id))

        # Notification
        cursor.execute("SELECT user_id FROM CICERON.RETURN_MONEY_BANK_ACCOUNT WHERE id = %s AND order_no = %s ", (id_order, order_no))
        user_id_no = cursor.fetchall()[0][0]
        send_noti_lite(g.db, user_id_no, 15, None, None)

        g.db.commit()
        return make_response(json.jsonify(
            message="Payed back. Order no: %s" % order_no), 200)

    elif request.method == "GET":
        cursor = g.db.cursor()
        cursor.execute("""SELECT
            fact.id, fact.order_no, fact.user_id, usr.email, fact.bank_name, fact.account_no, fact.request_time, fact.amount, fact.is_returned, fact.return_time
            FROM CICERON.RETURN_MONEY_BANK_ACCOUNT fact
            LEFT OUTER JOIN CICERON.D_USERS usr ON fact.user_id = usr.id
            WHERE fact.is_returned = false
                ORDER BY fact.id DESC""")
        rs = cursor.fetchall()
        result = []
        for item in rs:
            item = {
                    'id': item[0],
                    'orderNo': str(item[1]),
                    'user_email': str(item[3]),
                    'bankName': str(item[4]),
                    'accountNo': str(item[5]),
                    'requestTime': item[6],
                    'amount': item[7]
                    }
            result.append(item)

        return make_response(json.jsonify(
            data=result), 200)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    
