# -*- coding: utf-8 -*-
from flask import Flask, session, redirect, escape, request, g, abort, json, flash, make_response, send_from_directory, url_for
from flask_pushjack import FlaskGCM
from contextlib import closing
from datetime import datetime, timedelta
import hashlib, sqlite3, os, time, requests, sys, paypalrestsdk, logging
from functools import wraps
from werkzeug import secure_filename
from decimal import Decimal
from ciceron_lib import *
from flask.ext.cors import CORS
from flask.ext.session import Session
from multiprocessing import Process
from flask.ext.cache import Cache
from flask_oauth import OAuth

DATABASE = '../db/ciceron.db'
VERSION = '1.0'
DEBUG = True
BASEPATH = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER_PROFILE_PIC = "profile_pic"
UPLOAD_FOLDER_REQUEST_PIC = "request_pic"
UPLOAD_FOLDER_REQUEST_SOUND = "request_sounds"
UPLOAD_FOLDER_REQUEST_DOC = "request_doc"
UPLOAD_FOLDER_REQUEST_TEXT =  "request_text"
UPLOAD_FOLDER_RESULT = "translate_result"
MAX_CONTENT_LENGTH = 4 * 1024 * 1024
GCM_API_KEY = 'AIzaSyC4wvRTQZY81dZustxiXLIATsuVKy5xwp8'
FACEBOOK_APP_ID = 256525961180911
FACEBOOK_APP_SECRET = 'e382ac48932308c15641803022feca13'

SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = "CiceronCookie"

ALLOWED_EXTENSIONS_PIC = set(['jpg', 'jpeg', 'png', 'tiff'])
ALLOWED_EXTENSIONS_DOC = set(['doc', 'hwp', 'docx', 'pdf', 'ppt', 'pptx', 'rtf'])
ALLOWED_EXTENSIONS_WAV = set(['wav', 'mp3', 'aac', 'ogg', 'oga', 'flac', '3gp', 'm4a'])
VERSION= "2014.12.28"

CELERY_BROKER_URL = 'redis://localhost'

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

# Flask-Pushjack
gcm_server = FlaskGCM()
gcm_server.init_app(app)

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
super_user = ["pjh0308@gmail.com", "happyhj@gmail.com", "admin@ciceron.me", "yysyhk@naver.com"]

def pic_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_PIC']

def doc_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_DOC']

def sound_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_WAV']

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

################################################################################
#########                        ASYNC TASKS                           #########
################################################################################

def parallel_send_email(user_name, user_email, noti_type, request_id, language_id, optional_info=None):
    import mail_template
    template = mail_template.mail_format()
    message = None

    if noti_type == 0:
        message = template.translator_new_ticket(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/stoa/%d') % request_id}

    elif noti_type == 1:
        message = template.translator_check_expected_time(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/translating/%d') % request_id,
             "expected": optional_info.get('expected')}
            # datetime.now() + timedelta(seconds=(due_time - start_translating_time)/3)

    elif noti_type == 2:
        message = template.translator_complete(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/activity/%d') % request_id}
            
    elif noti_type == 3:
        message = template.translator_exceeded_due(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/stoa/%d') % request_id}

    elif noti_type == 4:
        message = template.translator_extended_due(langauge_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/translating/%d') % request_id,
             "new_due": optional_info.get('new_due')}

    elif noti_type == 5:
        message = template.translator_no_answer_expected_time(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/stoa/%d') % request_id}

    elif noti_type == 6:
        message = template.client_take_ticket(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/processingrequests/%d') % request_id,
             'hero': optional_info.get('hero')}

    elif noti_type == 7:
        message = template.client_check_expected_time(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/processingrequests/%d') % request_id}

    elif noti_type == 8:
        message = template.client_giveup_ticket(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/stoa/%d') % request_id,
             "hero": optional_info.get('hero')}

    elif noti_type == 9:
        message = template.client_no_answer_expected_time_go_to_stoa(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/stoa/%d') % request_id}

    elif noti_type == 10:
        message = template.client_complete(language_id) %{"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/donerequests/%d') % request_id,
             "hero": optional_info.get('hero')}

    elif noti_type == 11:
        message = template.client_incomplete(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/processingrequests/%d') % request_id}

    elif noti_type == 12:
        message = template.client_no_hero(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/processingrequests/%d') % request_id}

    elif noti_type == 14:
        message = template.client_no_hero(language_id) % {"host": os.environ.get('HOST', app.config['HOST']),
             "user": user_name,
             "link": (HOST + '/stoa')}

    send_mail(user_email, "Here is your news, %s" % user_name, message)

################################################################################
#########                     MAIN APPLICATION                         #########
################################################################################

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
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
    if 'useremail' in session:
        client_os = request.args.get('client_os', None)

        #if client_os is not None and registration_id is not None:
        #    check_and_update_reg_key(g.db, client_os, registration_id)
        #    g.db.coomit()

        return make_response(json.jsonify(
            useremail=session['useremail'],
            isLoggedIn = True,
            message="User %s is logged in" % session['useremail'])
            , 200)
    else:
        return make_response(json.jsonify(
            useremail=None,
            isLoggedIn=False,
            message="No user is logged in")
            , 403)

@app.route('/api/login', methods=['POST', 'GET'])
#@exception_detector
def login():
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
        cursor = g.db.execute("SELECT hashed_pass FROM PASSWORDS where user_id = ?",
                [user_id])
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
            session['logged_in'] = True
            session['useremail'] = email
            session.pop('salt', None)
        
            #if client_os is not None and registration_id is not None:
            #    check_and_update_reg_key(g.db, client_os, registration_id)
        
            return make_response(json.jsonify(
                message='You\'re logged with user %s' % email)
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
            g.db.execute("INSERT INTO D_FACEBOOK_USERS VALUES (?,?,?) ",
                    [new_facebook_id, buffer(user_data['email'], user_id)])
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
    g.db.execute("INSERT INTO D_FACEBOOK_USERS VALUES (?,?,?) ",
            [new_facebook_id, buffer(email), user_id])
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
    # No parameter needed
    if session['logged_in'] == True:
        cache.clear()
        username_temp = session['useremail']
        session.pop('logged_in', None)
        session.pop('useremail', None)
        # Status code 200 (OK)
        # Logout success
        return make_response(json.jsonify(
                   message = "User %s is logged out" % username_temp
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
    # Request method: POST
    # Parameters
    #     email: String, email ID ex) psy2848048@gmail.com
    #     password: String, password
    #     name: String, this name will be used and appeared in Ciceron system
    #     mother_language_id: Enum integer, 1st language of user
    #     (not yet) client_os
    #     (not yet) registration_id

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
            return make_response(json.jsonify(message="Registration %s: successful" % email), 200)
        elif status == 412:
            return make_response(json.jsonify(message="Duplicate email: %s" % email), 412)
    
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
    # Method: GET
    # Parameter: String id
    parameters = parse_request(request)
    email = parameters['email']
    print "email_id: %s" % email
    cursor = g.db.execute("select id from D_USERS where email = ?", [buffer(email)])
    check_data = cursor.fetchall()
    if len(check_data) == 0:
        # Status code 200 (OK)
        # Description: Inputted e-mail ID is available
        return make_response(json.jsonify(
            message="You may use the ID %s" % email), 200)
    else:
        # Status code 400 (BAD)
        # Description: Inputted e-mail ID is duplicated with other's one
        return make_response(json.jsonify(
            message="Duplicated ID '%s'" % email), 400)

@app.route('/api/user/create_recovery_code', methods=['POST'])
#@exception_detector
def create_recovery_code():
    parameters = parse_request(request)
    email = parameters['email']

    user_id = get_user_id(g.db, email)
    if user_id == -1:
        return make_response(json.jsonify(
            message="No user exists: %s" % email), 400)

    cursor = g.db.execute("SELECT name FROM D_USERS WHERE id = ?", [user_id])
    user_name = cursor.fetchall()[0][0]

    recovery_code = random_string_gen(size=12)
    hashed_code = get_hashed_password(recovery_code)
    g.db.execute("REPLACE INTO EMERGENCY_CODE (user_id, code) VALUES (?,?)",
            [user_id, hashed_code])
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
                         'page': "http://ciceron.me",
                         "host": HOST + ':5000'
                         }

    send_mail(email, subject, message)

    return make_response(json.jsonify(
        message="Password recovery code is issued for %s" % email), 200)

@app.route('/api/user/recover_password', methods=['POST'])
#@exception_detector
def recover_password():
    parameters = parse_request(request)
    email = parameters['email']
    hashed_code = parameters['code']
    hashed_new_password = parameters['new_password']
    user_id = get_user_id(g.db, email)

    # Get hashed_password using user_id for comparing
    cursor = g.db.execute("SELECT code FROM EMERGENCY_CODE where user_id = ?",
            [user_id])
    rs = cursor.fetchall()

    if len(rs) > 1:
        # Status code 500 (ERROR)
        # Description: Same e-mail address tried to be inserted into DB
        return make_response (json.jsonify(message='Constraint violation error!'), 501)

    elif len(rs) == 1 and str(rs[0][0]) == hashed_code:
        g.db.execute("UPDATE PASSWORDS SET hashed_pass = ? WHERE user_id = ?", [hashed_new_password, user_id])
        g.db.execute("UPDATE EMERGENCY_CODE SET code = null WHERE user_id = ?", [user_id])
        g.db.commit()
        return make_response (json.jsonify(message='Password successfully changed for user %s' % email), 200)

    else:
        return make_response (json.jsonify(message='Security code incorrect!'), 403)

@app.route('/api/user/change_password', methods=['POST'])
@login_required
#@exception_detector
def change_password():
    parameters = parse_request(request)
    email = parameters['email']
    hashed_old_password = parameters['old_password']
    hashed_new_password = parameters['new_password']
    user_id = get_user_id(g.db, email)

    # Get hashed_password using user_id for comparing
    cursor = g.db.execute("SELECT hashed_pass FROM PASSWORDS where user_id = ?",
            [user_id])
    rs = cursor.fetchall()

    if len(rs) > 1:
        # Status code 500 (ERROR)
        # Description: Same e-mail address tried to be inserted into DB
        return make_response (json.jsonify(message='Constraint violation error!'), 501)

    elif len(rs) == 1 and str(rs[0][0]) == hashed_old_password:
        g.db.execute("UPDATE PASSWORDS SET hashed_pass = ? WHERE user_id = ?", [hashed_new_password, user_id])
        g.db.commit()
        return make_response (json.jsonify(message='Password successfully changed for user %s' % email), 200)

    else:
        return make_response (json.jsonify(message='Old password of user %s is incorrect!' % email), 403)

@app.route('/api/user/profile', methods = ['GET', 'POST'])
@login_required
#@exception_detector
def user_profile():
    if request.method == 'GET':
        # Method: GET
        # Parameters
        #     user_email: String, text
        # Get value
        email = request.args.get('user_email', session['useremail'])
        user_id = get_user_id(g.db, email)

        # Start logic
        cursor = g.db.execute("SELECT * FROM D_USERS WHERE id = ?", [user_id])
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
        if is_your_profile == True:
            cursor = g.db.execute("SELECT amount FROM REVENUE WHERE id = ?",  [user_id])
            profile['user_revenue'] = cursor.fetchall()[0][0]
        else:
            profile['user_revenue'] = -65535

        return make_response(json.jsonify(profile), 200)

    elif request.method == "POST":
        # Method: GET
        # Parameters
        #     user_email: String, text
        #     user_profilePic: binary

        # Get parameter value
        parameters = parse_request(request)

        profileText = parameters.get('user_profileText', None)
        if profileText != None:
            profileText = profileText.encode('utf-8')
        profile_pic = request.files.get('user_profilePic', None)

        # Start logic
        # Get user number
        email = session['useremail']

        # Profile text update
        if profileText != None:
            g.db.execute("UPDATE D_USERS SET profile_text = ? WHERE email = ?",
                    [buffer(profileText), buffer(email)])

        # Profile photo update
        filename = ""
        path = ""
        if profile_pic and pic_allowed_file(profile_pic.filename):
            extension = profile_pic.filename.split('.')[-1]
            filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + '.' + extension
            pic_path = os.path.join(app.config['UPLOAD_FOLDER_PROFILE_PIC'], filename)
            print pic_path
            profile_pic.save(pic_path)

            g.db.execute("UPDATE D_USERS SET profile_pic_path = ? WHERE email = ?", [buffer(pic_path), buffer(email)])

        #if is_translator:
        #    g.db.execute("UPDATE D_USERS SET is_translator = ? WHERE email = ?", [is_translator, buffer(session['useremail'])])

        g.db.commit()
        return make_response(json.jsonify(
            message="Your profile is susccessfully updated!"), 200)

@app.route('/api/user/profile/keywords/<keyword>', methods = ['GET', 'POST', 'DELETE'])
@login_required
#@exception_detector
def user_keywords_control(keyword):
    if request.method == "POST":
        if "%%2C" in keyword or ',' in keyword:
            return make_response(json.jsonify(
                message="No commna(',') in keyword"), 400)

        keyword_id = get_id_from_text(g.db, keyword, "D_KEYWORDS")
        if keyword_id == -1:
            keyword_id = get_new_id(g.db, "D_KEYWORDS")
            g.db.execute("INSERT INTO D_KEYWORDS VALUES (?,?)", [keyword_id, buffer(keyword)])

        user_id = get_user_id(g.db, session['useremail'])
        g.db.execute("INSERT INTO D_USER_KEYWORDS VALUES (?,?)", [user_id, keyword_id])
        g.db.commit()

        return make_response(json.jsonify(
            message="Keyword '%s' is inserted into user %s" % (keyword, session['useremail'])),
            200)

    elif request.method == "DELETE":
        user_id = get_user_id(g.db, session['useremail'])
        keyword_id = get_id_from_text(g.db, keyword, "D_KEYWORDS")
        g.db.execute("DELETE FROM D_USER_KEYWORDS WHERE user_id = ? AND keyword_id = ?", [user_id, keyword_id])
        g.db.commit()

        return make_response(json.jsonify(
            message="Keyword '%s' is deleted from user %s" % (keyword, session['useremail'])),
            200)

    elif request.method == "GET":
        print """SELECT text FROM D_KEYWORDS WHERE text like '%s%%' """ % keyword
        cursor = g.db.execute("""SELECT id, text FROM D_KEYWORDS WHERE text like '%s%%' """ % keyword)
        similar_keywords = [str(item[1]) for item in cursor.fetchall()]
        return make_response(json.jsonify(
            message="Similarity search results",
            result=similar_keywords), 200)

@app.route('/api/requests', methods=["GET", "POST"])
#@exception_detector
def requests():
    if request.method == "GET":
        # Request method: GET
        # Parameters
        #     since(optional): Timestamp, take recent 20 post before the timestamp.
        #                  If this parameter is not provided, recent 20 posts from now are returned

        query = None
        if session.get('useremail') in super_user:
            query = """SELECT * FROM V_REQUESTS WHERE
                (((ongoing_worker_id is null AND status_id = 0 AND isSos = 0) OR (isSos = 1))) AND due_time > CURRENT_TIMESTAMP """
        else:
            query = """SELECT * FROM V_REQUESTS WHERE
                (((ongoing_worker_id is null AND status_id = 0 AND isSos = 0 AND is_paid = 1) OR (isSos = 1))) AND due_time > CURRENT_TIMESTAMP """
        if 'since' in request.args.keys():
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query += " ORDER BY registered_time DESC LIMIT 20"

        cursor = g.db.execute(query)
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs)

        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        # Method: POST
        # Parameters -> Please check code
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

        if isSos == False:
            delta_from_due = int(parameters['request_deltaFromDue'])
        else:
            delta_from_due = 30 * 60

        point = float(parameters.get('request_points')) if isSos == False else 0

        if parameters.get('request_context') != None:
            context = parameters.get('request_context').encode('utf-8')
        else:
            context = None

        new_photo_id = None
        new_sound_id = None
        new_file_id = None
        new_text_id = None
        is_paid = True if isSos == True else False

        if isSos == False and (original_lang_id == 500 or target_lang_id == 500):
            return make_response(json.jsonify(
                message="The language you requested is not yet registered. SOS request only"
                ), 204)

        # Upload binaries into file and update each dimension table
        if (request.files.get('request_photo') != None):
            binary = request.files['request_photo']
            filename = ""
            path = ""
            if pic_allowed_file(binary.filename):
                extension = binary.filename.split('.')[-1]
                filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + '.' + extension
                path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_PIC'], filename)
                binary.save(path)

            new_photo_id = get_new_id(g.db, "D_REQUEST_PHOTOS")
            g.db.execute("INSERT INTO D_REQUEST_PHOTOS VALUES (?,?,?)",
                    [new_photo_id, request_id, buffer(path)])

        if (request.files.get('request_sound') != None):
            binary = request.files['request_sound']
            filename = ""
            path = ""
            if sound_allowed_file(binary.filename):
                extension = binary.filename.split('.')[-1]
                filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + '.' + extension
                path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_SOUND'], filename)
                binary.save(path)

            new_sound_id = get_new_id(g.db, "D_REQUEST_SOUNDS")
            g.db.execute("INSERT INTO D_REQUEST_SOUNDS VALUES (?,?)",
                    [new_sound_id, buffer(path)])
        
        if (request.files.get('request_file') != None):
            binary = request.files['request_file']
            filename = ""
            path = ""
            if doc_allowed_file(binary.filename):
                extension = binary.filename.split('.')[-1]
                filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + '.' + extension
                path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_DOC'], filename)
                binary.save(path)

            new_file_id = get_new_id(g.db, "D_REQUEST_FILES")
            g.db.execute("INSERT INTO D_REQUEST_FILES VALUES (?,?)",
                    [new_file_id, buffer(path)])

            ############ Documentfile 2 TEXT ##################

            if (binary.filename).endswith('.docx'):
                from docx import Document
                try:
                    doc = Document(path)
                    text_string = ('\n').join([ paragraph.text for paragraph in doc.paragraphs ])
                    print "DOCX file is converted into text."
                except Exception as e:
                    print "DOCX Error. Skip."
                    pass

            elif (binary.filename).endswith('.pdf'):
                import slate
                try:
                    f = open(path, 'rb')
                    doc = slate.PDF(f)
                    f.close()

                    text_string = ('\n\n').join(doc)
                    text_string = text_string.decode('utf-8')
                except Exception as e:
                    print "PDF Error. Skip"
                    pass

            ##################################################

        if text_string:
            filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + ".txt"
            path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_TEXT'], filename)
            f = open(path, 'wb')
            f.write(bytearray(text_string.encode('utf-8')))
            f.close()

            new_text_id = get_new_id(g.db, "D_REQUEST_TEXTS")
            g.db.execute("INSERT INTO D_REQUEST_TEXTS VALUES (?,?)",
                    [new_text_id, buffer(path)])

        # Input context text into dimension table
        new_context_id = get_new_id(g.db, "D_CONTEXTS")
        g.db.execute("INSERT INTO D_CONTEXTS VALUES (?,?)",
                [new_context_id, buffer(context)])

        g.db.execute("""INSERT INTO F_REQUESTS
            (id, client_user_id, original_lang_id, target_lang_id, isSOS, status_id, format_id, subject_id, queue_id, ongoing_worker_id, is_text, text_id, is_photo, photo_id, is_file, file_id, is_sound, sound_id, client_completed_group_id, translator_completed_group_id, client_title_id, translator_title_id, registered_time, due_time, points, context_id, comment_id, tone_id, translatedText_id, is_paid)
                VALUES
                (?,?,?,?,?,
                 ?,?,?,?,?,
                 ?,?,?,?,?,
                 ?,?,?,?,?,
                 ?,?, datetime('now'), datetime('now', '+%d seconds'), ?,
                 ?,?,?,?,?)""" % delta_from_due, 
            bool_value_converter([
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
                    #delta_from_due,       # due_time
                    point,                # points
                    new_context_id,       # context_id
                    None,                 # comment_id
                    None,                 # tone_id
                    None,                 # translatedText_id
                    is_paid]))               # is_paid

        g.db.commit()
        update_user_record(g.db, client_id=client_user_id)

        # Notification for SOS request
        if isSos == True:
            rs = pick_random_translator(g.db, 10, original_lang_id, target_lang_id)
            for item in rs:
                store_notiTable(g.db, item[0], 0, None, request_id)
                regKeys_oneuser = get_device_id(g.db, item[0])

                message_dict = get_noti_data(g.db, 10, item[0], request_id)
                if len(regKeys_oneuser) > 0:
                    gcm_noti = gcm_server.send(regKeys_oneuser, message_dict)

        g.db.commit()

        return make_response(json.jsonify(
            message="Request ID %d  has been posted by %s" % (request_id, parameters['request_clientId']),
            request_id=request_id), 200)

#@app.route('/api/requests/<str_request_id>', methods=["DELETE"])
#@login_required
##@exception_detector
#def delete_requests(str_request_id):
#    if request.method == "DELETE":
#        request_id = int(str_request_id)
#        user_id = get_user_id(g.db, session['useremail'])
#
#        # Check that somebody is translating this request.
#        # If yes, requester cannot delete this request
#        cursor = g.db.execute("SELECT count(id) FROM F_REQUESTS WHERE id = ? AND client_user_id = ? ",
#                [request_id, user_id])
#        is_my_request = cursor.fetchall()[0][0]
#        if is_my_request == 0:
#            return make_response(json.jsonify(
#                message="This request is not yours!"), 409)
#
#        cursor = g.db.execute("SELECT count(id) FROM F_REQUESTS WHERE id = ? AND client_user_id = ? AND ongoing_worker_id is null",
#                [request_id, user_id])
#
#        num_of_request = cursor.fetchall()[0][0]
#        if num_of_request == 0:
#            return make_response(json.jsonify(
#                message="If translator has taken the request, you cannot delete the request!"), 410)
#
#        g.db.execute("DELETE FROM F_REQUESTS WHERE id = ? AND client_user_id = ? AND ongoing_worker_id is null",
#                [request_id, user_id])
#        g.db.commit()
#        
#        # Using request_id and client_user_id, delete notification of the request
#
#        update_user_record(g.db, client_id=user_id)
#        g.db.commit()
#
#        return make_response(json.jsonify(
#            message="Request #%d is successfully deleted!" % request_id,
#            request_id=request_id), 200)

@app.route('/api/user/translations/pending', methods=["GET", "POST"])
@login_required
#@exception_detector
@translator_checker
def show_queue():
    if request.method == "GET":
        # Request method: GET
        # Parameters
        #     since(OPTIONAL): Timestamp integer, for paging

        my_user_id = get_user_id(g.db, session['useremail'])

        query_pending = None
        if session['useremail'] in super_user:
            query_pending = """SELECT * FROM V_REQUESTS 
                WHERE request_id IN (SELECT request_id FROM D_QUEUE_LISTS WHERE user_id = ?) """
        else:
            query_pending = """SELECT * FROM V_REQUESTS 
                WHERE request_id IN (SELECT request_id FROM D_QUEUE_LISTS WHERE user_id = ?) AND is_paid = 1 """

        if 'since' in request.args.keys():
            query_pending += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query_pending += "ORDER BY registered_time DESC LIMIT 20"

        cursor = g.db.execute(query_pending, [my_user_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs)

        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        # In POST, it should be changed into /user/translations/pending/<request_id>
        # But Error must be occurred because form data is not needed in the case of above.

        # Request method: POST
        # Parameters
        #     request_id: Integer

        # Translators in queue
        # Get request ID
        parameters = parse_request(request)

        request_id = int(parameters['request_id'])
        translator_email = parameters.get('translator_email', session['useremail']) # WILL USE FOR REQUESTING WITH TRANSLATOR SELECTING
        query = None
        if session['useremail'] in super_user:
            query = "SELECT queue_id, client_user_id FROM F_REQUESTS WHERE id = ? "
        else:
            query = "SELECT queue_id, client_user_id FROM F_REQUESTS WHERE id = ? AND is_paid = 1 "

        cursor = g.db.execute(query, [request_id])
        rs = cursor.fetchall()

        if len(rs) == 0: return make_response(json.jsonify(message = "There is no request ID %d" % request_id), 400)

        if translator_email == None: user_id = get_user_id(g.db, session['useremail'])
        else:                        user_id = get_user_id(g.db, translator_email)
        request_user_id = rs[0][1]

        if strict_translator_checker(g.db, user_id, request_id) == False:
            return make_response(
                json.jsonify(
                   message = "You have no translate permission of given language."
                   ), 401)

        if user_id == request_user_id:
            return make_response(json.jsonify(
                message = "You cannot translate your request. Request ID: %d" % request_id
                ), 406)

        queue_id = rs[0][0]
        cursor.execute("SELECT user_id FROM D_QUEUE_LISTS WHERE id = ? AND user_id = ?", [queue_id, user_id])
        rs = cursor.fetchall()
        if len(rs) != 0:
            return make_response(json.jsonify(
                message = "You've already stood in queue. Request ID: %d" % request_id
                ), 204)

        query="INSERT INTO D_QUEUE_LISTS VALUES (?,?,?)"

        if queue_id == None:
            queue_id = get_new_id(g.db, "D_QUEUE_LISTS")
            g.db.execute("UPDATE F_REQUESTS SET queue_id = ? WHERE id = ?", [queue_id, request_id])

        g.db.execute(query, [queue_id, request_id, user_id])
        g.db.commit()

        update_user_record(g.db, client_id=request_user_id, translator_id=user_id)
        g.db.commit()

        return make_response(json.jsonify(
            message = "You are in queue for translating request #%d" % request_id,
            request_id=request_id
            ), 200)

@app.route('/api/user/translations/pending/<str_request_id>', methods=["DELETE"])
@login_required
@translator_checker
#@exception_detector
def work_in_queue(str_request_id):
    if request.method == "DELETE":
        request_id = int(str_request_id)
        my_user_id = get_user_id(g.db, session['useremail'])
        cursor = g.db.execute("SELECT count(*) FROM D_QUEUE_LISTS WHERE request_id = ? AND user_id = ? ",
                [request_id, my_user_id])
        rs = cursor.fetchall()
        if len(rs) == 0 or rs[0][0] == 0:
            return make_response(json.jsonify
                       (message="You are not in the queue of request ID #%d" % request_id),
                   204)
            
        g.db.execute("DELETE FROM D_QUEUE_LISTS WHERE request_id = ? AND user_id = ? ", [request_id, my_user_id])
        update_user_record(g.db, translator_id=my_user_id)

        return make_response(json.jsonify(
            message="You've dequeued from request #%d" % request_id,
            request_id=request_id), 200)

@app.route('/api/user/translations/ongoing', methods=['GET', 'POST'])
@login_required
@translator_checker
#@exception_detector
def pick_request():
    if request.method == "POST":
        # Request method: POST
        # Parameters
        #    request_id: requested post id
        parameters = parse_request(request)

        request_id = int(parameters['request_id'])
        user_id = get_user_id(g.db, session['useremail'])

        cursor = g.db.execute("SELECT queue_id, client_user_id FROM F_REQUESTS WHERE id = ? AND status_id = 0", [request_id])
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

        g.db.execute("UPDATE F_REQUESTS SET status_id = 1, ongoing_worker_id = ? , start_translating_time = CURRENT_TIMESTAMP WHERE id = ? AND status_id = 0", [user_id, request_id])

        if strict_translator_checker(g.db, user_id, request_id) == False:
            return make_response(
                json.jsonify(
                   message = "You have no translate permission of given language."
                   ), 401)

        g.db.execute("DELETE FROM D_QUEUE_LISTS WHERE id = ? and request_id = ? and user_id = ?",
                [queue_id, request_id, user_id])
        g.db.commit()

        update_user_record(g.db, client_id=request_user_id, translator_id=user_id)

        # Notification
        send_noti_suite(gcm_server, g.db, request_user_id, 6, user_id, request_id,
                optional_info={"hero": user_id})

        g.db.commit()
        return make_response(json.jsonify(
            message = "You are now tranlator of request #%d" % request_id,
            request_id=request_id
            ), 200)

    elif request.method == "GET":
        # Request method: GET
        # Parameters
        #     since (optional): Timestamp integer

        query_ongoing = None
        if session['useremail'] in super_user:
            query_ongoing = """SELECT * FROM V_REQUESTS WHERE status_id = 1 AND ongoing_worker_id = ? """
        else:
            query_ongoing = """SELECT * FROM V_REQUESTS WHERE status_id = 1 AND ongoing_worker_id = ? AND is_paid = 1 """

        if 'since' in request.args.keys():
            query_ongoing += "AND start_translating_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query_ongoing += "ORDER BY start_translating_time DESC LIMIT 20"

        my_user_id = get_user_id(g.db, session['useremail'])
        cursor = g.db.execute(query_ongoing, [my_user_id])
        rs = cursor.fetchall()

        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator") # PLEASE REVISE
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/ongoing/<str_request_id>', methods=["GET", "PUT"])
#@exception_detector
@translator_checker
@login_required
def working_translate_item(str_request_id):
    if request.method == "GET":
        request_id = int(str_request_id)
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM V_REQUESTS WHERE status_id = 1 AND request_id = ? "
        else:
            query = "SELECT * FROM V_REQUESTS WHERE status_id = 1 AND request_id = ? AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND start_translating_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        cursor = g.db.execute(query, [request_id])

        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator")
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "PUT":
        parameters = parse_request(request)

        request_id = int(str_request_id)
        save_request(g.db, parameters, str_request_id, app.config['UPLOAD_FOLDER_RESULT'])
        return make_response(json.jsonify(
            message="Request id %d is auto saved." % request_id,
            request_id=request_id
            ), 200)

@app.route('/api/user/translations/ongoing/<str_request_id>/expected', methods=["GET", "POST", "DELETE"])
#@exception_detector
@translator_checker
@login_required
def expected_time(str_request_id):
    if request.method == "GET":
        request_id = int(str_request_id)
        query = None
        if session['useremail'] in super_user:
            query = "SELECT expected_time, due_time FROM F_REQUESTS WHERE status_id = 1 AND id = ? "
        else:
            query = "SELECT expected_time, due_time FROM F_REQUESTS WHERE status_id = 1 AND id = ? AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND start_translating_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        cursor = g.db.execute(query, [request_id])
        rs = cursor.fetchall()
        if len(rs) > 0:
            return make_response(json.jsonify(currentExpectedTime=rs[0][0], currentDueTime=rs[0][1]), 200)
        else:
            return make_response(json.jsonify(message="Outscoped (Completed, canceled, etc)"), 400)

    elif request.method == "POST":
        parameters = parse_request(request)

        request_id = int(str_request_id)
        deltaFromRegTime = int(parameters['deltaFromNow'])
        g.db.execute("UPDATE F_REQUESTS SET expected_time = datetime('now', '+%d seconds') WHERE status_id = 1 AND id = ?" % deltaFromRegTime,
                [request_id])
        g.db.commit()

        # Notification
        query = "SELECT client_user_id, expected_time FROM F_REQUESTS WHERE id = ?"
        cursor= g.db.execute(query, [request_id])
        rs = cursor.fetchall()
        send_noti_suite(gcm_server, g.db, rs[0][0], 7, rs[0][1], request_id, optional_info={"expected": rs[0][1]})

        g.db.commit()
        return make_response(json.jsonify(
            message="Thank you for responding!",
            request_id=request_id), 200)

    elif request.method == "DELETE":
        request_id = int(str_request_id)
        g.db.execute("UPDATE F_REQUESTS SET ongoing_worker_id = null, status_id = 0 WHERE status_id = 1 AND id = ?",
                [request_id])
        g.db.commit()

        query = None
        if session['useremail'] in super_user:
            query = "SELECT due_time FROM F_REQUESTS WHERE status_id = 1 AND id = ? "
        else:
            query = "SELECT due_time FROM F_REQUESTS WHERE status_id = 1 AND id = ? AND is_paid = 1 "
        cursor = g.db.execute(query, [request_id])

        client_user_id = cursor.fetchall()[0][0]
        translator_user_id = get_user_id(g.db, session['useremail'])

        update_user_record(g.db, client_id=client_user_id, translator_id=translator_user_id)

        # Notification
        query = "SELECT client_user_id, ongoing_worker_id FROM F_REQUESTS WHERE id = ?"
        cursor.execute(query, [request_id])
        rs = cursor.fetchall()
        send_noti_suite(gcm_server, g.db, rs[0][0], 8, rs[0][1], request_id, optional_info={"hero": rs[0][1]})

        g.db.commit()
        return make_response(json.jsonify(
            message="Wish a better tomorrow!",
            request_id=request_id), 200)

@app.route('/api/user/translations/complete', methods=["POST"])
#@exception_detector
@login_required
@translator_checker
def post_translate_item():
    parameters = parse_request(request)

    request_id = int(parameters['request_id'])
    save_request(g.db, parameters, request_id, app.config['UPLOAD_FOLDER_RESULT'])

    # Assign default group to requester and translator
    query = None
    if session['useremail'] in super_user:
        query = "SELECT client_user_id, ongoing_worker_id FROM V_REQUESTS WHERE request_id = ? AND status_id = 1 "
    else:
        query = "SELECT client_user_id, ongoing_worker_id FROM V_REQUESTS WHERE request_id = ? AND is_paid = 1 AND status_id = 1 "
    query += "ORDER BY submitted_time DESC LIMIT 20"

    cursor = g.db.execute(query, [request_id])
    rs = cursor.fetchall()
    if len(rs) == 0:
        return make_response(
            json.jsonify(
                message="Already completed request %d" % request_id,
                request_id=request_id), 410)

    requester_id = rs[0][0]
    translator_id = rs[0][1]

    requester_default_group_id = get_group_id_from_user_and_text(g.db, requester_id, "Documents", "D_CLIENT_COMPLETED_GROUPS")
    translator_default_group_id =  get_group_id_from_user_and_text(g.db, translator_id, "Documents", "D_TRANSLATOR_COMPLETED_GROUPS")

    # No default group. Insert new default group entry for user
    if requester_default_group_id == -1:
        requester_default_group_id = get_new_id(g.db, "D_CLIENT_COMPLETED_GROUPS")
        g.db.execute("INSERT INTO D_CLIENT_COMPLETED_GROUPS VALUES (?,?,?)",
            [requester_default_group_id, requester_id, buffer("Documents")])
    if translator_default_group_id == -1:
        translator_default_group_id = get_new_id(g.db, "D_TRANSLATOR_COMPLETED_GROUPS")
        g.db.execute("INSERT INTO D_TRANSLATOR_COMPLETED_GROUPS VALUES (?,?,?)",
            [translator_default_group_id, translator_id, buffer("Documents")])

    # Change the state of the request
    g.db.execute("UPDATE F_REQUESTS SET status_id = 2, client_completed_group_id=?, translator_completed_group_id=?, submitted_time=datetime('now') WHERE id = ?", [requester_default_group_id, translator_default_group_id, request_id])
    g.db.commit()

    update_user_record(g.db, client_id=requester_id, translator_id=translator_id)

    # Delete users in queue
    g.db.execute("DELETE FROM D_QUEUE_LISTS WHERE request_id = ?", [request_id])

    # Notification
    query = "SELECT client_user_id, ongoing_worker_id FROM F_REQUESTS WHERE id = ?"
    cursor.execute(query, [request_id])
    rs = cursor.fetchall()
    send_noti_suite(gcm_server, g.db, rs[0][0], 10, rs[0][1], request_id, optional_info={"hero": rs[0][1]})

    g.db.commit()

    return make_response(json.jsonify(
        message="Request id %d is submitted." % request_id,
        request_id=request_id
        ), 200)

@app.route('/api/user/translations/complete/<str_request_id>', methods = ["GET"])
#@exception_detector
@login_required
@translator_checker
def translation_completed_items_detail(str_request_id):
    request_id = int(str_request_id)
    user_id = get_user_id(g.db, session['useremail'])
    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM V_REQUESTS WHERE status_id = 2 AND request_id = ? AND ongoing_worker_id = ? "
    else:
        query = "SELECT * FROM V_REQUESTS WHERE status_id = 2 AND request_id = ? AND ongoing_worker_id = ? AND is_paid = 1 "
    if 'since' in request.args.keys():
        query += "AND submitted_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += "ORDER BY submitted_time DESC LIMIT 20"
    cursor = g.db.execute(query, [request_id, user_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_translator")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/complete', methods = ["GET"])
#@exception_detector
@login_required
@translator_checker
def translation_completed_items_all():
    since = request.args.get('since', None)
    user_id = get_user_id(g.db, session['useremail'])

    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM V_REQUESTS WHERE status_id = 2 AND ongoing_worker_id = ? "
    else:
        query = "SELECT * FROM V_REQUESTS WHERE status_id = 2 AND ongoing_worker_id = ? AND is_paid = 1 "
    if 'since' in request.args.keys():
        query += "AND submitted_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += " ORDER BY submitted_time DESC LIMIT 20"

    cursor = g.db.execute(query, [user_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_translator")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/complete/<str_request_id>/title', methods = ["POST"])
#@exception_detector
@login_required
@translator_checker
def set_title_translator(str_request_id):
    if request.method == "POST":
        parameters = parse_request(request)

        request_id = int(str_request_id)
        title_text = (parameters['title_text']).encode('utf-8')

        my_user_id = get_user_id(g.db, session['useremail'])
        default_group_id = get_group_id_from_user_and_text(g.db, my_user_id, "Documents", "D_TRANSLATOR_COMPLETED_GROUPS")

        # No default group. Insert new default group entry for user
        new_title_id = get_new_id(g.db, "D_TRANSLATOR_COMPLETED_REQUEST_TITLES")
        g.db.execute("INSERT INTO D_TRANSLATOR_COMPLETED_REQUEST_TITLES VALUES (?,?)",
                [new_title_id, buffer(title_text)])

        g.db.execute("UPDATE F_REQUESTS SET translator_title_id = ? WHERE id = ?", 
            [new_title_id, request_id])

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

@app.route('/api/user/translations/complete/groups', methods = ["GET", "POST", "PUT", "DELETE"])
#@exception_detector
@translator_checker
@login_required
def translators_complete_groups():
    if request.method == "GET":
        since = None
        if 'since' in request.args.keys():
            since = request.args['since']
        result = complete_groups(g.db, None, "D_TRANSLATOR_COMPLETED_GROUPS", "GET", since=since)
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        parameters = parse_request(request)
        group_name = complete_groups(g.db, parameters, "D_TRANSLATOR_COMPLETED_GROUPS", "POST")
        if group_name == -1:
            return make_response(json.jsonify(message="'Document' is reserved name"), 401)
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
            return make_response(json.jsonify(message="Group 'Document' is default. You cannot delete it!"), 401)
        else:
            return make_response(json.jsonify(message="Group %d is deleted. Requests are moved into default group" % group_id), 200)
    elif request.method == "PUT":
        parameters = parse_request(request)
        group_name = complete_groups(g.db, parameters, "D_TRANSLATOR_COMPLETED_GROUPS", "PUT")
        if group_name == -1:
            return make_response(json.jsonify(message="You cannot change the name of the group to 'Document'. It is default group name" % group_name), 401)
        else:
            return make_response(json.jsonify(message="Group name is changed to %s" % group_name), 200)

@app.route('/api/user/translations/complete/groups/<str_group_id>', methods = ["POST", "GET"])
#@exception_detector
@translator_checker
@login_required
def translation_completed_items_in_group(str_group_id):
    if request.method == "POST":
        parameters = parse_request(request)

        group_id = int(str_group_id)
        request_id = int(parameters['request_id'])
        g.db.execute("UPDATE F_REQUESTS SET translator_completed_group_id = ? WHERE id = ?", [group_id, request_id])
        group_name = get_text_from_id(g.db, group_id, "D_TRANSLATOR_COMPLETED_GROUPS")
        g.db.commit()
        return make_response(
                json.jsonify(message="Request #%d has been moved to the group '%s'" % (request_id, group_name)), 200)

    elif request.method == "GET":
        group_id = int(str_group_id)
        my_user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM V_REQUESTS WHERE ongoing_worker_id = ? AND translator_completed_group_id = ? "
        else:
            query = "SELECT * FROM V_REQUESTS WHERE ongoing_worker_id = ? AND translator_completed_group_id = ? AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND submitted_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query += " ORDER BY submitted_time DESC LIMIT 20"
        cursor = g.db.execute(query, [my_user_id, group_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="complete_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/incomplete', methods = ["GET"])
#@exception_detector
@login_required
@translator_checker
def translation_incompleted_items_all():
    since = request.args.get('since', None)
    user_id = get_user_id(g.db, session['useremail'])

    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM V_REQUESTS WHERE ((status_id IN (-1,1) AND ongoing_worker_id = ?) OR (request_id IN (SELECT request_id FROM D_QUEUE_LISTS WHERE user_id = ?))) "
    else:
        query = "SELECT * FROM V_REQUESTS WHERE ((status_id IN (-1,1) AND ongoing_worker_id = ? AND is_paid = 1) OR (request_id IN (SELECT request_id FROM D_QUEUE_LISTS WHERE user_id = ?) AND is_paid = 1)) "
    if 'since' in request.args.keys():
        query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += " ORDER BY request_id DESC LIMIT 20"

    cursor = g.db.execute(query, [user_id, user_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="pending_translator")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/incomplete/<str_request_id>', methods = ["GET"])
#@exception_detector
@login_required
@translator_checker
def translation_incompleted_items_each(str_request_id):
    if request.method == "GET":
        request_id = int(str_request_id)
        user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM V_REQUESTS WHERE status_id IN (-1,1) AND ongoing_worker_id = ? AND request_id = ? "
        else:
            query = "SELECT * FROM V_REQUESTS WHERE status_id IN (-1,1) AND ongoing_worker_id = ? AND request_id = ? AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query += " ORDER BY registered_time DESC LIMIT 20"
        cursor = g.db.execute(query, [user_id, request_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="pending_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/pending', methods=["GET"])
#@exception_detector
@login_required
def show_pending_list_client():
    if request.method == "GET":
        user_id = get_user_id(g.db, session['useremail'])
        if session['useremail'] in super_user:
            query = "SELECT * FROM V_REQUESTS WHERE client_user_id = ? AND status_id = 0 "
        else:
            query = "SELECT * FROM V_REQUESTS WHERE client_user_id = ? AND status_id = 0 AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')

        query += " ORDER BY registered_time DESC LIMIT 20"
        cursor = g.db.execute(query, [user_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/pending/<str_request_id>', methods=["GET"])
#@exception_detector
@login_required
def show_pending_item_client(str_request_id):
    if request.method == "GET":
        user_id = get_user_id(g.db, session['useremail'])
        request_id = int(str_request_id)
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM V_REQUESTS WHERE request_id = ? AND client_user_id = ? AND status_id = 0 "
        else:
            query = "SELECT * FROM V_REQUESTS WHERE request_id = ? AND client_user_id = ? AND status_id = 0 AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        cursor = g.db.execute(query, [request_id, user_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/pending/<str_request_id>', methods=["DELETE"])
#@exception_detector
@login_required
def delete_item_client(str_request_id):
    if request.method == "DELETE":
        user_id = get_user_id(g.db, session['useremail'])
        request_id = int(str_request_id)
        query = None
        if session['useremail'] in super_user:
            query = "SELECT points FROM V_REQUESTS WHERE request_id = ? AND client_user_id = ? AND status_id = 0 "
        else:
            query = "SELECT points FROM V_REQUESTS WHERE request_id = ? AND client_user_id = ? AND status_id = 0 AND is_paid = 1 "
        cursor = g.db.execute(query, [request_id, user_id])
        points = cursor.fetchall()[0][0]
        g.db.execute("UPDATE REVENUE SET amount = amount + ? WHERE id = ?",
                [points, user_id])
        g.db.execute("DELETE FROM F_REQUESTS WHERE request_id = ? AND client_user_id = ? AND status_id = 0",
                [request_id, user_id])
        g.db.commit()
        return make_response(json.jsonify(
            message="Request #%d is deleted. USD %.2f is returned as requester's points" % (request_id, points), request_id=request_id), 200)

@app.route('/api/user/requests/ongoing', methods=["GET"])
#@exception_detector
@login_required
def show_ongoing_list_client():
    if request.method == "GET":
        user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM V_REQUESTS WHERE client_user_id = ? AND status_id = 1 "
        else:
            query = "SELECT * FROM V_REQUESTS WHERE client_user_id = ? AND status_id = 1 AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND start_translating_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query += " ORDER BY start_translating_time DESC LIMIT 20"
        cursor = g.db.execute(query, [user_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/ongoing/<str_request_id>', methods=["GET"])
#@exception_detector
@login_required
def show_ongoing_item_client(str_request_id):
    if request.method == "GET":
        user_id = get_user_id(g.db, session['useremail'])
        request_id = int(str_request_id)
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM V_REQUESTS WHERE request_id = ? AND client_user_id = ? AND status_id = 1 "
        else:
            query = "SELECT * FROM V_REQUESTS WHERE request_id = ? AND client_user_id = ? AND status_id = 1 AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND start_translating_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query += " ORDER BY start_translating_time DESC LIMIT 20"
        cursor = g.db.execute(query, [request_id, user_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/complete', methods = ["GET"])
#@exception_detector
@login_required
def client_completed_items():
    user_id = get_user_id(g.db, session['useremail'])
    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM V_REQUESTS WHERE status_id = 2 AND client_user_id = ? "
    else:
        query = "SELECT * FROM V_REQUESTS WHERE status_id = 2 AND client_user_id = ? AND is_paid = 1 "
    if 'since' in request.args.keys():
        query += "AND submitted_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += " ORDER BY submitted_time DESC LIMIT 20"
    cursor = g.db.execute(query, [user_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/complete/<str_request_id>', methods = ["GET"])
#@exception_detector
@login_required
def client_completed_items_detail(str_request_id):
    request_id = int(str_request_id)
    user_id = get_user_id(g.db, session['useremail'])
    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM V_REQUESTS WHERE status_id = 2 AND client_user_id = ? AND request_id = ? "
    else:
        query = "SELECT * FROM V_REQUESTS WHERE status_id = 2 AND client_user_id = ? AND request_id = ? AND is_paid = 1 "
    if 'since' in request.args.keys():
        query += "AND submitted_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += " ORDER BY submitted_time DESC LIMIT 20"
    cursor = g.db.execute(query, [user_id, request_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/complete/<str_request_id>/rate', methods=["POST"])
#@exception_detector
@login_required
def client_rate_request(str_request_id):
    parameters = parse_request(request)
    request_id = int(str_request_id)
    feedback_score = int(parameters['request_feedbackScore'])

    # Pay back part
    if session['useremail'] in super_user:
        query_getTranslator = "SELECT ongoing_worker_id, points, feedback_score FROM F_REQUESTS WHERE id = ? "
    else:
        query_getTranslator = "SELECT ongoing_worker_id, points, feedback_score FROM F_REQUESTS WHERE id = ? AND is_paid = 1"

    cursor = g.db.execute(query_getTranslator, [request_id])
    rs = cursor.fetchall()
    formal_feedback_score = rs[0][2]

    # If the request is rated, another rate should be blocked
    if formal_feedback_score != None:
        return make_response(json.jsonify(
            message="The request is already rated!",
            request_id=request_id),
            403)

    translator_id = rs[0][0]
    pay_amount = rs[0][1]

    # Input feedback score
    g.db.execute("UPDATE F_REQUESTS SET feedback_score = ? WHERE id = ?", [feedback_score, request_id])

    #######################################################################
    #  IF RETURN RATE EXISTS, THE BLOCKED CODE BELOW WILL BE IMPLEMENTED  #
    #######################################################################

    #query_getCounts = None
    #if session['useremail'] in super_user:
    #    query_getCounts = "SELECT count(*) FROM F_REQUESTS WHERE ongoing_worker_id = ? AND status_id = 2 AND submitted_time BETWEEN date('now', '-1 month')      AND date('now')"
    #else:
    #    query_getCounts = "SELECT count(*) FROM F_REQUESTS WHERE ongoing_worker_id = ? AND status_id = 2 AND is_paid = 1 AND submitted_time BETWEEN date('now', '-1 month')      AND date('now')"
    #cursor = g.db.execute(query_getCounts, [translator_id])
    #rs = cursor.fetchall()
    #translator_performance = rs[0][0]

    ## Back rate
    #back_rate = 0.0
    #if translator_performance >= 80:
    #    back_rate = 0.7
    #elif translator_performance >= 60:
    #    back_rate = 0.6
    #elif translator_performance >= 45:
    #    back_rate = 0.65
    #elif translator_performance >= 30:
    #    back_rate = 0.6
    #else:
    #    back_rate = 0.50

    # Currently fixed rate
    return_rate = 0.7

    # Record payment record
    g.db.execute("UPDATE PAYMENT_INFO SET translator_id=?, is_payed_back=?, back_amount=? WHERE request_id = ?",
            [translator_id, 0, return_rate * pay_amount, request_id])

    # Update the translator's purse
    g.db.execute("UPDATE REVENUE SET amount = amount + ? * ? WHERE id = ?",
            [return_rate, pay_amount, translator_id])

    # Notification
    query = "SELECT ongoing_worker_id, client_user_id FROM F_REQUESTS WHERE id = ?"
    cursor = g.db.execute(query, [request_id])
    rs = cursor.fetchall()
    send_noti_suite(gcm_server, g.db, rs[0][0], 2, rs[0][1], request_id)

    g.db.commit()

    return make_response(json.jsonify(
        message="The requester rated to request #%d as %d points (in 0~2). And translator has been earned USD %.2f" % (request_id, feedback_score, pay_amount*return_rate),
        request_id=request_id),
        200)

@app.route('/api/user/requests/complete/<str_request_id>/title', methods=["POST"])
#@exception_detector
@login_required
def set_title_client(str_request_id):
    if request.method == "POST":
        parameters = parse_request(request)

        request_id = int(str_request_id)
        title_text = (parameters['title_text']).encode('utf-8')

        my_user_id = get_user_id(g.db, session['useremail'])
        default_group_id = get_group_id_from_user_and_text(g.db, my_user_id, "Documents", "D_CLIENT_COMPLETED_GROUPS")

        # No default group. Insert new default group entry for user
        new_title_id = get_new_id(g.db, "D_CLIENT_COMPLETED_REQUEST_TITLES")
        g.db.execute("INSERT INTO D_CLIENT_COMPLETED_REQUEST_TITLES VALUES (?,?)",
                [new_title_id, buffer(title_text)])

        g.db.execute("UPDATE F_REQUESTS SET client_title_id = ? WHERE id = ?", [new_title_id, request_id])
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
        result = complete_groups(g.db, None, "D_CLIENT_COMPLETED_GROUPS", "GET", since=since)
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        parameters = parse_request(request)

        group_name = complete_groups(g.db, parameters, "D_CLIENT_COMPLETED_GROUPS", "POST")
        if group_name != -1:
            return make_response(json.jsonify(message="New group %s has been created" % group_name), 200)
        else:
            return make_response(json.jsonify(message="'Documents' is default group name"), 401)

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
            return make_response(json.jsonify(message="'Documents' is default group name"), 401)

    elif request.method == "DELETE":
        group_id = complete_groups(g.db, None, "D_CLIENT_COMPLETED_GROUPS", "DELETE", url_group_id=str_group_id)
        if group_id == -1:
            return make_response(json.jsonify(message="You cannot delete 'Documents' group"), 401)

        elif group_id == -2:
            return make_response(json.jsonify(message="Already deleted group"), 401)

        else:
            return make_response(json.jsonify(message="Group %d is deleted." % group_id), 200)

@app.route('/api/user/requests/complete/groups/<str_group_id>', methods = ["POST", "GET"])
#@exception_detector
@login_required
def client_completed_items_in_group(str_group_id):
    if request.method == "POST":
        parameters = parse_request(request)
        group_id = int(str_group_id)
        request_id = int(parameters['request_id'])
        g.db.execute("UPDATE F_REQUESTS SET client_completed_group_id = ? WHERE id = ?", [group_id, request_id])
        group_name = get_text_from_id(g.db, group_id, "D_CLIENT_COMPLETED_GROUPS")
        g.db.commit()
        return make_response(
                json.jsonify(message="Request #%d has moved to the group '%s'" % (request_id, group_name)), 200)

    elif request.method == "GET":
        group_id = int(str_group_id)
        my_user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM V_REQUESTS WHERE client_user_id = ? AND client_completed_group_id = ? "
        else:
            query = "SELECT * FROM V_REQUESTS WHERE client_user_id = ? AND client_completed_group_id = ? AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND submitted_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query += "ORDER BY submitted_time DESC"
        cursor = g.db.execute(query, [my_user_id, group_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/incomplete', methods = ["GET"])
#@exception_detector
@login_required
def client_incompleted_items():
    user_id = get_user_id(g.db, session['useremail'])
    query = None
    if session['useremail'] in super_user:
        query = "SELECT * FROM V_REQUESTS WHERE status_id IN (-1,0,1) AND client_user_id = ? "
    else:
        query = "SELECT * FROM V_REQUESTS WHERE status_id IN (-1,0,1) AND client_user_id = ? AND is_paid = 1 "
    if 'since' in request.args.keys():
        query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += " ORDER BY registered_time DESC LIMIT 20"
    cursor = g.db.execute(query, [user_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/incomplete/<str_request_id>', methods = ["GET", "PUT", "DELETE", "POST"])
#@exception_detector
@login_required
def client_incompleted_item_control(str_request_id):
    if request.method == "GET":
        request_id = int(str_request_id)
        user_id = get_user_id(g.db, session['useremail'])
        query = None
        if session['useremail'] in super_user:
            query = "SELECT * FROM V_REQUESTS WHERE status_id IN (-1,0,1) AND client_user_id = ? AND request_id = ? "
        else:
            query = "SELECT * FROM V_REQUESTS WHERE status_id IN (-1,0,1) AND client_user_id = ? AND request_id = ? AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query += " ORDER BY registered_time DESC LIMIT 20"
        cursor = g.db.execute(query, [user_id, request_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "PUT":
        # Only update due_time and price

        # It can be used in:
        #    1) Non-selected request
        #    2) Give more chance to the trusted translator

        request_id = int(str_request_id)
        parameters = parse_request(request)

        # Addional time: unit is second, counted from NOW
        additional_time_in_sec = int(parameters['user_additionalTime'])
        additional_price = 0
        if parameters.get('user_additionalPrice') != None:
            additional_price = float(parameters['user_additionalPrice'])

        # Notification
        query = "SELECT ongoing_worker_id, client_user_id FROM F_REQUESTS WHERE id = ?"
        cursor = g.db.execute(query, [request_id])
        rs = cursor.fetchall()
        if rs[0][0] is not None:
            send_noti_suite(gcm_server, g.db, rs[0][0], 4, rs[0][1], request_id,
                optional_info={"hero": rs[0][1]})

        user_id = get_user_id(g.db, session['useremail'])
        # Change due date w/o addtional money
        if additional_price == 0:
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 0 WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is null" % additional_time_in_sec, [request_id, user_id])
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 1 WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is not null" % additional_time_in_sec, [request_id, user_id])
            g.db.commit()

            return make_response(json.jsonify(
                message="Request #%d is renewed" % request_id,
                api=None,
                request_id=request_id), 200)

        # Change due date w/additional money
        else:
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 0, is_paid = 0, points = points + ? WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is null" % additional_time_in_sec, [additional_price, request_id, user_id])
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 1, is_paid = 0, points = points + ? WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is not null" % additional_time_in_sec, [additional_price, request_id, user_id])
            g.db.commit()

            return make_response(json.jsonify(
                message="Request #%d is renewed. Please execute the API provided with POST method" % request_id,
                api="/api/user/requests/%d/payment/start"%request_id,
                additional_price=additional_price,
                request_id=request_id), 200)

    elif request.method == "POST":
        # It can be used in:
        #    1) Say goodbye to translator, back to stoa

        request_id = int(str_request_id)
        parameters = parse_request(request)

        # Addional time: unit is second, counted from NOW
        additional_time_in_sec = int(parameters['user_additionalTime'])
        additional_price = 0
        if parameters.get('user_additionalPrice') != None:
            additional_price = float(parameters['user_additionalPrice'])

        user_id = get_user_id(g.db, session['useremail'])
        # Change due date w/o addtional money
        if additional_price == 0:
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 0, ongoing_worker_id = null WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is not null" % additional_time_in_sec, [request_id, user_id])
            g.db.commit()

            return make_response(json.jsonify(
                message="Request #%d is posted back to stoa." % request_id,
                request_id=request_id,
                api=None), 200)

        # Change due date w/additional money
        else:
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 0, is_paid = 0, points = points + ?, ongoing_worker_id = null WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is not null" % additional_time_in_sec, [additional_price, request_id, user_id])
            g.db.commit()

            return make_response(json.jsonify(
                message="Request #%d is renewed. Please execute the API provided with POST methid" % request_id,
                request_id=request_id,
                additional_price=additional_price,
                api="/api/user/requests/%d/payment/start"%request_id), 200)

    elif request.method == "DELETE":
        # It can be used in:
        #    1) Say goodbye to translator. And he/she don't want to leave his/her request
        request_id = int(str_request_id)
        user_id = get_user_id(g.db, session['useremail'])

        cursor = g.db.execute("SELECT points FROM F_REQUESTS WHERE id = ? AND status_id IN (-1,0) AND client_user_id = ?", [request_id, user_id])
        ret = cursor.fetchone()[0]
        points = None
        if ret is not None:
            points = float(ret)
        else:
            return make_response(json.jsonify(
                message="The point has already refunded about this request.",
                request_id=request_id), 402)
            
        g.db.execute("UPDATE REVENUE SET amount = amount + ? WHERE id = ?", [points, user_id])

        g.db.execute("UPDATE F_REQUESTS SET is_paid = 0, status_id = -2 WHERE id = ? AND status_id IN (-1,0) AND client_user_id = ? ", [request_id, user_id])

        g.db.commit()

        # Notification
        query = "SELECT ongoing_worker_id, client_user_id FROM F_REQUESTS WHERE id = ?"
        cursor.execute(query, [request_id])
        rs = cursor.fetchall()
        if rs[0][0] != None and rs[0][1] != None:
            send_noti_suite(gcm_server, g.db, rs[0][0], 3, rs[0][1], request_id)
            update_user_record(g.db, translator_id=rs[0][1])

        update_user_record(g.db, client_id=rs[0][0])

        g.db.commit()

        return make_response(json.jsonify(
            message="Your request #%d is deleted. Your points USD %.2f is backed in your account" % (request_id, points),
            request_id=request_id), 200)

@app.route('/api/user/requests/<str_request_id>/payment/checkPromoCode', methods = ["POST"])
#@exception_detector
@login_required
def check_promotionCode(str_request_id):
    user_id = get_user_id(g.db, session['useremail'])
    parameters = parse_request(request)

    code = parameters['promotionCode'].upper()

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
            promoType=None, message="There is no promo code matched,", code=3, point=0), 402)
        
@app.route('/api/user/requests/<str_request_id>/payment/start', methods = ["POST"])
#@exception_detector
@login_required
def pay_for_request(str_request_id):
    parameters = parse_request(request)

    pay_by = parameters.get('pay_by')
    pay_via = parameters.get('pay_via')
    request_id = int(str_request_id)
    total_amount = float(parameters['pay_amount'])
    use_point = float(parameters.get('use_point', 0))

    promo_type = parameters.get('promo_type', 'null')
    promo_code = parameters.get('promo_code', 'null')

    # Check whether the price exceeds the client's money purse.
    amount = None
    user_id = get_user_id(g.db, session['useremail'])

    host_ip = os.environ.get('HOST', app.config['HOST'])

    # Point deduction
    if use_point > 0:
        # Check whether use_point exceeds or not
        cursor = g.db.execute("SELECT amount FROM REVENUE WHERE id = ?", [user_id])
        current_point = float(cursor.fetchall()[0][0])
        print "Current_point: %f" % current_point
        print "Use_point: %f" % use_point
        print "Diff: %f" % (use_point - current_point)

        if current_point - use_point < -0.00001:
            return make_response(json.jsonify(
                message="You requested to use your points more than what you have. Price: %.2f, Your purse: %.2f" % (use_point, current_point)), 402)
        else:
            amount = total_amount - use_point
    else:
        amount = total_amount

    # Promo code deduction
    if promo_type != 'null':
        isCommonCode, commonPoint, commonMessage = commonPromotionCodeChecker(g.db, user_id, promo_code)
        isIndivCode, indivPoint, indivMessage = individualPromotionCodeChecker(g.db, user_id, promo_code)
        if isCommonCode == 0:
            amount = amount - commonPoint
        elif isIndivCode == 0:
            amount = amount - indivPoint

    if pay_via == 'paypal':
        # SANDBOX
        paypalrestsdk.configure(
                mode="sandbox",
                client_id="AQX4nD2IQ4xQ03Rm775wQ0SptsSe6-WBdMLldyktgJG0LPhdGwBf90C7swX2ymaSJ-PuxYKicVXg12GT",
                client_secret="EHUxNGZPZNGe_pPDrofV80ZKkSMbApS2koofwDYRZR6efArirYcJazG2ao8eFqqd8sX-8fUd2im9GzBG"
        )

        # LIVE
        #paypalrestsdk.set_config(
        #        mode="live",
        #        client_id="AevAg0UyjlRVArPOUN6jjsRVQrlasLZVyqJrioOlnF271796_2taD1HOZFry9TjkAYSTZExpyFyJV5Tl",
        #        client_secret="EJjp8RzEmFRH_qpwzOyJU7ftf9GxZM__vl5w2pqERkXrt3aI6nsVBj2MnbkfLsDzcZzX3KW8rgqTdSIR"
        #        )

        logging.basicConfig(level=logging.INFO)
        logging.basicConfig(level=logging.ERROR)

        payment = paypalrestsdk.Payment({
          "intent": "sale",
          "payer": {
            "payment_method": "paypal"},
          "redirect_urls":{
            "return_url": "%s:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=success&user_id=%s&pay_amt=%.2f&pay_by=%s&use_point=%.2f&promo_type=%s&promo_code=%s" % (HOST, request_id, session['useremail'], amount, pay_by, use_point, promo_type, promo_code),
            "cancel_url": "%s:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=fail&user_id=%s&pay_amt=%.2f&pay_by=%s&use_point=%.2f&promo_type=%s&promo_code=%s" % (HOST, request_id, session['useremail'], amount, pay_by, use_point, promo_type, promo_code)},
          "transactions": [{
            "amount": {
                "total": "%.2f" % amount,
                "currency": "USD",
            },
          "description": "Ciceron translation request fee USD: %f" % amount }]})
        rs = payment.create()  # return True or False
        paypal_link = None
        for item in payment.links:
            if item['method'] == 'REDIRECT':
                paypal_link = item['href']
                break

        red_link = "%s:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=success&user_id=%s&pay_amt=%.2f&pay_by=%s&use_point=%.2f&promo_type=%s&promo_code=%s" % (host_ip, request_id, session['useremail'], amount, pay_by, use_point, promo_type, promo_code)
        if bool(rs) is True:
            return make_response(json.jsonify(message="Redirect link is provided!", link=paypal_link, redirect_url=red_link), 200)
        else:
            return make_response(json.jsonify(message="Something wrong in paypal"), 400)

    elif pay_via == 'alipay':
        from alipay import Alipay
        alipay_obj = Alipay(pid='2088021580332493', key='lksk5gkmbsj0w7ejmhziqmoq2gdda3jo', seller_email='contact@ciceron.me')
        params = {
            'subject': '是写论翻译'.decode('utf-8'),
            'out_trade_no': 12345,
            #'subject': 'TEST',
            'total_fee': '%.2f' % amount,
            'currency': 'USD',
            'quantity': '1',
            'return_url': "%s:5000/api/user/requests/%d/payment/postprocess?pay_via=alipay&status=success&user_id=%s&pay_amt=%.2f&pay_by=%s&use_point=%.2f&promo_type=%s&promo_code=%s" % (HOST, request_id, session['useremail'], amount, pay_by, use_point, promo_type, promo_code)
            }

        provided_link = None
        if pay_by == 'web':
            provided_link = alipay_obj.create_forex_trade_url(**params)
        elif pay_by == 'mobile':
            provided_link = alipay_obj.create_forex_trade_wap_url(**params)

        return make_response(json.jsonify(
            message="Link to Alipay is provided.",
            link=provided_link), 200)

    elif pay_via == "point_only":
        g.db.execute("UPDATE REVENUE SET amount = amount - ? WHERE id = ?", [use_point, user_id])
        g.db.execute("UPDATE F_REQUESTS SET is_paid = ? WHERE id = ?", [True, request_id])
        g.db.commit()

        if pay_by == "web":
            return redirect(HOST, code=302)
        elif pay_by == "mobile":
            return redirect(HOST, code=302)
            #return """
            #    <!DOCTYPE html>
            #    <html>
            #    <head></head>
            #    <body>
            #    <script type='text/javascript'>
            #        window.close();
            #    </script>
            #    </body></html>"""

@app.route('/api/user/requests/<str_request_id>/payment/postprocess', methods = ["GET"])
#@exception_detector
#@login_required
def pay_for_request_process(str_request_id):
    request_id = int(str_request_id)
    user = request.args['user_id']
    user_id = get_user_id(g.db, user)
    pay_via = request.args['pay_via']
    pay_by = request.args['pay_by']
    is_success = True if request.args['status'] == "success" else False
    amount = float(request.args.get('pay_amt'))
    use_point = float(request.args.get('use_point', 0))

    promo_type = request.args.get('promo_type', 'null')
    promo_code = request.args.get('promo_code', 'null')

    # Point deduction
    if use_point > 0:
        g.db.execute("UPDATE REVENUE SET amount = amount - ? WHERE id = ?", [use_point, user_id])

    if pay_via == 'paypal':
        payment_id = request.args['paymentId']
        payer_id = request.args['PayerID']
        if is_success:
            payment_info_id = get_new_id(g.db, "PAYMENT_INFO")
            # Paypal payment exeuction
            payment = paypalrestsdk.Payment.find(payment_id)
            payment.execute({"payer_id": payer_id})

            g.db.execute("UPDATE F_REQUESTS SET is_paid = ? WHERE id = ?", [True, request_id])

            # Payment information update
            g.db.execute("INSERT INTO PAYMENT_INFO (id, request_id, client_id, payed_via, order_no, pay_amount, payed_time) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)",
                    [payment_info_id, request_id, buffer(user), buffer("paypal"), buffer(payment_id), amount])

            g.db.commit()
            #return redirect("success")

    elif pay_via == "alipay":
        if is_success:
            # Get & store order ID and price
            payment_info_id = get_new_id(g.db, "PAYMENT_INFO")

            g.db.execute("UPDATE F_REQUESTS SET is_paid = ? WHERE id = ?", [True, request_id])

            # Payment information update
            g.db.execute("INSERT INTO PAYMENT_INFO (id, request_id, client_id, payed_via, order_no, pay_amount, payed_time) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)",
                    #[payment_info_id, request_id, buffer(user), buffer("alipay"), buffer(payment_id), amount])
                    [payment_info_id, request_id, buffer(user), buffer("alipay"), None, amount])

            g.db.commit()

    if promo_type == 'common':
        commonPromotionCodeExecutor(g.db, user_id, promo_code)
    elif promo_type == 'indiv':
        individualPromotionCodeExecutor(g.db, user_id, promo_code)

    # Notification for normal request
    cursor = g.db.execute("SELECT original_lang_id, target_lang_id FROM F_REQUESTS WHERE id = ?", [request_id])
    record = cursor.fetchall()
    try:
        onerecord = record[0]
    except Exception as e:
        print "No record for this request. Request ID: %d" % request_id
        return redirect(HOST, code=302)

    original_lang_id = onerecord[0]
    target_lang_id = onerecord[1]

    rs = pick_random_translator(g.db, 10, original_lang_id, target_lang_id)
    for item in rs:
        store_notiTable(g.db, item[0], 0, None, request_id)
        regKeys_oneuser = get_device_id(g.db, item[0])

        message_dict = get_noti_data(g.db, 0, item[0], request_id)
        if len(regKeys_oneuser) > 0:
            gcm_noti = gcm_server.send(regKeys_oneuser, message_dict)

    if pay_by == "web":
        return redirect(HOST, code=302)
    elif pay_by == "mobile":
        return redirect(HOST, code=302)
        #return """
        #    <!DOCTYPE html>
        #    <html>
        #    <head></head>
        #    <body>
        #    <script type='text/javascript'>
        #        window.close();
        #    </script>
        #    </body></html>"""

@app.route('/api/user/device', methods = ["POST"])
#@exception_detector
@login_required
def register_or_update_register_id():
    parameters = parse_request(request)

    device_os = parameters['user_deviceOS']
    reg_key = parameters['user_regKey']
    user_id = get_user_id(g.db, session['useremail'])

    record_id = get_new_id(g.db, "D_MACHINES")
    cursor = g.db.execute("SELECT count(*) FROM D_MACHINES WHERE os_id = (SELECT id FROM D_MACHINE_OSS WHERE text = ?) AND user_id = ?",
            [device_os, user_id])
    num = cursor.fetchall()[0][0]

    if num == 0:
        g.db.execute("INSERT INTO D_MACHINES VALUES (?, ?, (SELECT id FROM D_MACHINE_OSS WHERE text = ?), ?, ?)",
            [record_id, user_id, device_os, buffer(reg_key), 1])
    else:
        g.db.execute("UPDATE D_MACHINES SET reg_key = ? WHERE os_id = (SELECT id FROM D_MACHINE_OSS WHERE text = ?) AND user_id = ?",
            [buffer(reg_key), device_os, user_id])

    g.db.commit()

    return make_response(json.jsonify(message="Succefully updated/inserted"), 200)

@app.route('/api/access_file/<directory>/<filename>')
@login_required
def access_file(directory, filename):
    print request.remote_addr
    return send_from_directory(directory, filename)

@app.route('/api/mail_img/<directory>/<filename>')
def mail_img(directory, filename):
    return send_from_directory('img', filename)

@app.route('/api/action_record', methods = ["POST"])
@login_required
#@exception_detector
def record_user_location():
    parameters = parse_request(request)
    
    user_id = get_user_id(g.db, session['useremail'])
    lati = parameters.get('lat')
    longi = parameters.get('long')
    method = parameters.get('method')
    api = parameters.get('api')
    request_id = parameters.get('request_id')
    g.db.execute("INSERT INTO USER_ACTIONS VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)", 
            [user_id, lati, longi, method, api, request_id])
    g.db.commit()
    return make_response(json.jsonnify(
        message="Logged successfully"), 200)

@app.route('/api/notification', methods = ["GET"])
@login_required
#@exception_detector
def get_notification():
    user_id = get_user_id(g.db, session['useremail'])

    # Count whole unread noti
    query_noti = """SELECT count(*) FROM V_NOTIFICATION WHERE user_id = ? and is_read = 0 """
    cursor = g.db.execute(query_noti, [user_id])
    numberOfNoti = cursor.fetchall()[0][0]

    query = """SELECT user_name, user_profile_pic_path, noti_type_id, request_id, target_user_name, ts, is_read, target_profile_pic_path, (julianday(expected_time) - julianday(CURRENT_TIMESTAMP))*24*60*60 as expectedDue, context, status_id
        FROM V_NOTIFICATION WHERE user_id = ? """
    if 'since' in request.args.keys():
        query += "AND ts < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += "ORDER BY ts DESC LIMIT 10 "
    cursor = g.db.execute(query, [user_id])
    rs = cursor.fetchall()

    result = []
    for item in rs:
        row = {}

        isAlert, alertType, link = getRoutingAddressAndAlertType(g.db, user_id, item[3], item[2])

        row['username'] = str(item[0])
        row['profilePic'] = str(item[1]) if item[1] != None else None
        row['noti_typeId'] = item[2]
        row['request_id'] = item[3]
        row['target_username'] = str(item[4]) if item[4] != None else None
        row['target_userProfilePic'] = str(item[7]) if item[7] != None else None
        row['ts'] = str(item[5])
        row['is_read'] = parameter_to_bool(item[6])
        row['link'] = link
        row['isAlert'] = isAlert
        row['alertType'] = alertType
        row['abstract'] = str(item[9]) if item[9] != None else None
        row['request_status'] = item[10]

        #row['expectedDue'] = (string2Date(item[8])-datetime.now()).total_seconds() if item[8] != None else None
        row['expectedDue'] = item[8] if item[8] != None else None
        row['expectedDue_replied'] = True if item[8] != None else False

        result.append(row)

    return make_response(json.jsonify(
        numberOfNoti=numberOfNoti,
        message="Notifications",
        data=result), 200)

@app.route('/api/notification/read', methods = ["GET"])
@login_required
#@exception_detector
def read_notification():
    user_id = get_user_id(g.db, session['useremail'])
    query = """UPDATE F_NOTIFICATION SET is_read = 1 WHERE rowid IN (SELECT rowid FROM F_NOTIFICATION WHERE ts < datetime(%s, 'unixepoch') AND user_id = ? ORDER BY ts DESC LIMIT 10) """ % request.args.get('since')
    print query
    user_id = get_user_id(g.db, session['useremail'])
    g.db.execute(query, [user_id])
    g.db.commit()

    return make_response(json.jsonify(
        message="10 notis are marked as read"), 200)

@app.route('/api/user/payback', methods = ["GET", "POST"])
@login_required
#@exception_detector
def register_payback():
    if request.method == "GET":
        # GET payback list
        user_id = get_user_id(g.db, session['useremail'])
        cursor = g.db.execute("""SELECT id, order_no, bank_name, account_no, request_time, amount, is_returned
            FROM RETURN_MONEY_BANK_ACCOUNT
            WHERE user_id=?
            ORDER BY id DESC""", [user_id])

        rs = cursor.fetchall()
        result = []
        for item in rs:
            item = {
                    'id': item[0],
                    'orderNo': str(item[1]),
                    'bankName': str(item[2]),
                    'accountNo': item[3],
                    'requestTime': item[4],
                    'amount': item[5],
                    'isReturned': True if item[6] == 1 else False
                    }
            result.append(item)

        return make_response(json.jsonify(
            data=result), 200)

    elif request.method == "POST":
        # POST new payback request
        parameters = parse_request(request)

        user_id = get_user_id(g.db, session['useremail'])
        bank_name = parameters['bankName']
        account_no = parameters['accountNo']
        amount = float(parameters['amount'])

        # Test whether requested amount is exceeded the money in user's account
        cursor = g.db.execute("SELECT amount FROM REVENUE WHERE id = ?",  [user_id])
        revenue_amount = cursor.fetchall()[0][0]

        if revenue_amount < amount:
            return make_response(json.jsonify(
                message="User cannot request paid back. Revenue: %f, Requested amount: %f" % (revenue_amount, amount)), 402)

        new_id = get_new_id(g.db, "RETURN_MONEY_BANK_ACCOUNT")
        order_no = datetime.strftime(datetime.now(), "%Y%m%d") + random_string_gen(size=4)
        g.db.execute("INSERT INTO RETURN_MONEY_BANK_ACCOUNT VALUES (?,?,?,?,?,CURRENT_TIMESTAMP,?,0,null)",
                [new_id, order_no, user_id, bank_name, account_no, amount])
        g.db.commit()

        return make_response(json.jsonify(
            message="Payback request is successfully received"), 200)
        
@app.route('/api/user/payback_email', methods = ["GET"])
@login_required
#@exception_detector
def register_paybacki_email():
    mail_to = session['useremail']
    user_id = get_user_id(g.db, mail_to)
    cursor = g.db.execute("SELECT name FROM D_USERS WHERE id = ?", [user_id])
    name = cursor.fetchone()[0]

    subject = 'Please reply for your refund request'

    doc_no = random_string_gen(size=12)
    message="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
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
        user_id = get_user_id(g.db, session['useremail'])
        parameters = parse_request(request)

        bank_name = parameters.get('bankName')
        account_no = parameters.get('accountNo')
        amount = float(parameters.get('amount')) if parameters.get('amount') != None else None

        if bank_name != None:
            g.db.execute("UPDATE RETURN_MONEY_BANK_ACCOUNT SET bank_name = ? WHERE id = ? AND order_no = ? AND user_id = ?", [buffer(bank_name), int(str_id), order_no, user_id])
        if account_no != None:
            g.db.execute("UPDATE RETURN_MONEY_BANK_ACCOUNT SET account_no = ? WHERE id = ? AND order_no = ? AND user_id = ?", [account_no, int(str_id), order_no, user_id])
        if amount != None:
            # Test whether requested amount is exceeded the money in user's account
            cursor = g.db.execute("SELECT amount FROM REVENUE WHERE id = ?",  [user_id])
            revenue_amount = cursor.fetchall()[0][0]

            if revenue_amount < amount:
                return make_response(json.jsonify(
                    message="User cannot paid back. Revenue: %f, Requested amount: %f" % (revenue_amount, amount)), 402)

            g.db.execute("UPDATE RETURN_MONEY_BANK_ACCOUNT SET amount = ? WHERE id = ? AND order_no = ? AND user_id = ?", [amount, int(str_id), order_no, user_id])
            
        g.db.commit()

        return make_response(json.jsonify(
            message="Payback request is updated"), 200)

    elif request.method == "DELETE":
        user_id = get_user_id(g.db, session['useremail'])
        g.db.execute("DELETE FROM RETURN_MONEY_BANK_ACCOUNT WHERE id=? AND order_no=?", [int(str_id), order_no])
        g.db.commit()

        return make_response(json.jsonify(
            message="Payback request has just been deleted."), 200)

@app.route('/api/user/be_hero', methods=['POST'])
@login_required
#@exception_detector
def be_hero():
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
    message="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
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
    g.db.execute("UPDATE D_USERS SET trans_request_state=1 WHERE id = ?", [user_id])
    g.db.commit()

    return make_response(json.jsonify(
        message="Application mail has just sent to %s!" % email), 200)

################################################################################
#########                      SCHEDULER API                           #########
################################################################################

@app.route('/api/scheduler/expired_request_checker', methods = ["GET"])
#@exception_detector
def publicize():
    # No Expected time
    translator_list = []
    client_list = []

    query_no_expected_time = """SELECT ongoing_worker_id, client_user_id, id
        FROM F_REQUESTS
        WHERE (isSos= 0 AND status_id = 1 AND expected_time is null AND (julianday(CURRENT_TIMESTAMP) - julianday(start_translating_time)) > ((julianday(due_time) - julianday(start_translating_time))/2) AND datetime(start_translating_time, '+30 minutes') < due_time)
        OR    (isSos= 0 AND status_id = 1 AND expected_time is null AND (julianday(CURRENT_TIMESTAMP) - julianday(start_translating_time)) > ((julianday(due_time) - julianday(start_translating_time))/3) AND datetime(start_translating_time, '+30 minutes') > due_time) """
    cursor = g.db.execute(query_no_expected_time)
    rs = cursor.fetchall()
    for item in rs:
        send_noti_suite(gcm_server, g.db, item[0], 5, item[1], item[2])
        send_noti_suite(gcm_server, g.db, item[1], 9, item[0], item[2])
        translator_list.append(item[0])
        client_list.append(item[1])

    # Expired deadline
    query_expired_deadline = """SELECT ongoing_worker_id, client_user_id, id
        FROM F_REQUESTS
        WHERE isSos = 0 AND status_id = 1 AND CURRENT_TIMESTAMP > due_time """
    cursor = g.db.execute(query_expired_deadline)
    rs = cursor.fetchall()
    for item in rs:
        send_noti_suite(gcm_server, g.db, item[1], 11, item[0], item[2])
        send_noti_suite(gcm_server, g.db, item[0],  3, item[1], item[2])
        translator_list.append(item[0])
        client_list.append(item[1])

    # No translators
    query_no_translators = """SELECT client_user_id, id
        FROM F_REQUESTS
        WHERE isSos = 0 AND status_id = 0 AND CURRENT_TIMESTAMP > due_time """
    cursor = g.db.execute(query_no_translators)
    rs = cursor.fetchall()
    for item in rs:
        send_noti_suite(gcm_server, g.db, item[0], 12, None, item[1])
        client_list.append(item[0])

    g.db.execute("""UPDATE F_REQUESTS SET status_id = -1
        WHERE isSos = 0 AND status_id IN (0,1) AND CURRENT_TIMESTAMP > due_time """)
    g.db.execute("""UPDATE F_REQUESTS SET status_id = 0, ongoing_worker_id = null, start_translating_time = null
        WHERE (isSos= 0 AND status_id = 1 AND expected_time is null AND (julianday(CURRENT_TIMESTAMP) - julianday(start_translating_time)) > ((julianday(due_time) - julianday(start_translating_time))/2) AND datetime(start_translating_time, '+30 minutes') < due_time)
        OR    (isSos= 0 AND status_id = 1 AND expected_time is null AND (julianday(CURRENT_TIMESTAMP) - julianday(start_translating_time)) > ((julianday(due_time) - julianday(start_translating_time))/3) AND datetime(start_translating_time, '+30 minutes') > due_time) """)
    g.db.commit()

    for user_id in translator_list: update_user_record(g.db, translator_id=user_id)
    for user_id in client_list:     update_user_record(g.db, client_id=user_id)

    return make_response(json.jsonify(message="Expired requests are publicized"), 200)

@app.route('/api/scheduler/ask_expected_time', methods = ["GET"])
#@exception_detector
def ask_expected_time():
    # Future implementation: Join with noti table
    # Add client_user_id and update after commit
    query = """SELECT fact.ongoing_worker_id, fact.id, fact.client_user_id FROM F_REQUESTS fact
        LEFT OUTER JOIN V_NOTIFICATION noti ON fact.id = noti.request_id AND noti.noti_type_id = 1
        WHERE fact.isSos= 0 AND fact.status_id = 1 AND fact.expected_time is null AND noti.is_read is null
        AND (
          (CURRENT_TIMESTAMP > datetime(fact.start_translating_time, '+30 minutes') AND fact.due_time > datetime(CURRENT_TIMESTAMP, '+30 minutes'))
        OR 
          ((julianday(CURRENT_TIMESTAMP) - julianday(fact.start_translating_time)) > ((julianday(fact.due_time) - julianday(fact.start_translating_time))/3) AND fact.due_time < datetime(CURRENT_TIMESTAMP, '+30 minutes')) 
        )"""
    cursor = g.db.execute(query) 
    rs = cursor.fetchall()
    for item in rs:
        send_noti_suite(gcm_server, g.db, item[0], 1, item[2], item[1])

    g.db.commit()
    return make_response(json.jsonify(
        message="Noti are added for asking expected time. Scheduler will trigger to ask it."), 200)

@app.route('/api/scheduler/delete_sos', methods = ["GET"])
#@exception_detector
def delete_sos():
    # Expired deadline
    # Using ongoing_worker_id and client_user_id, and update statistics after commit
    translator_list = []
    client_list = []

    query_expired_deadline = """SELECT ongoing_worker_id, client_user_id, id
        FROM F_REQUESTS
        WHERE isSos = 1 AND status_id = 1 and ongoing_worker_id is not null AND CURRENT_TIMESTAMP > due_time """
    cursor = g.db.execute(query_expired_deadline)
    rs = cursor.fetchall()
    for item in rs:
        send_noti_suite(gcm_server, g.db, item[1], 11, item[0], item[2])
        send_noti_suite(gcm_server, g.db, item[0],  3, item[1], item[2])
        translator_list.append(item[0])
        client_list.append(item[1])

    # No translators
    query_no_translators = """SELECT client_user_id, id
        FROM F_REQUESTS
        WHERE isSos = 1 AND status_id = 0 AND CURRENT_TIMESTAMP > due_time """
    cursor = g.db.execute(query_no_translators)
    rs = cursor.fetchall()
    for item in rs:
        send_noti_suite(gcm_server, g.db, item[0], 12, None, item[1])
        client_list.append(item[0])

    g.db.execute("""UPDATE F_REQUESTS SET is_paid=0, status_id = -1
                     WHERE status_id in (0,1) AND isSos = 1 AND CURRENT_TIMESTAMP >= datetime(registered_time, '+30 minutes')""")
    g.db.commit()

    for user_id in translator_list: update_user_record(g.db, translator_id=user_id)
    for user_id in client_list:     update_user_record(g.db, client_id=user_id)

    return make_response(json.jsonify(message="Cleaned"), 200)

@app.route('/api/scheduler/mail_alarm', methods = ["GET"])
#@exception_detector
def mail_alarm():
    query = "SELECT * FROM V_NOTIFICATION WHERE is_read=0 AND CURRENT_TIMESTAMP > datetime(ts, '+3 minutes') ORDER BY ts"
    cursor = g.db.execute(query)
    rs = cursor.fetchall()
    process_pool = []

    for idx, item in enumerate(rs):
        user_id = item[0]
        query_mother_lang = "SELECT mother_language_id FROM D_USERS WHERE id = ?"
        cursor = g.db.execute(query_mother_lang, [user_id])
        mother_lang_id = cursor.fetchall()[0][0]

        proc = Process(target=parallel_send_email,
                       args=(item[2], item[1], item[3], item[5], mother_lang_id),
                       kwargs={"optional_info": {
                                   "expected": string2Date(item[10]) + (string2Date(item[11]) - string2Date(item[10]))/3 if item[10] != None and item[11] != None else None,
                                   "new_due": string2Date(item[11]) if item[11] != None else None,
                                   "hero": str(item[15]) if item[15] != None else None
                                  }
                              }
                       )

        process_pool.append(proc)

        #parallel_send_email(item[2], item[1], item[3], item[5], mother_lang_id,
        #               optional_info={
        #                           "expected": string2Date(item[10]) + (string2Date(item[11]) - string2Date(item[10]))/3 if item[10] != None and item[11] != None else None,
        #                           "new_due": string2Date(item[11]) if item[11] != None else None,
        #                           "hero": str(item[15]) if item[15] != None else None
        #                          }
        #               )

        if idx % 5 == 4 or idx == len(rs)-1:
            for i in process_pool:
                i.start()
            for i in process_pool:
                i.join()
            process_pool = []

    query = "UPDATE F_NOTIFICATION SET is_read=1 WHERE is_read=0 AND CURRENT_TIMESTAMP > datetime(ts, '+3 minutes')"
    g.db.execute(query)
    g.db.commit()

    return make_response(json.jsonify(
        message="Mail alarm sent"), 200)

################################################################################
#########                        ADMIN TOOL                            #########
################################################################################

@app.route('/api/admin/language_assigner', methods = ["POST"])
#@exception_detector
@admin_required
def language_assigner():
    parameters = parse_request(request)

    user_email = parameters['email']
    language_id = int(parameters['language_id'])
    user_id = get_user_id(g.db, user_email)
    new_translation_list_id = get_new_id(g.db, "D_TRANSLATABLE_LANGUAGES")

    g.db.execute("UPDATE D_USERS SET is_translator = 1, trans_request_state=2 WHERE id = ?", [user_id])
    cursor = g.db.execute("SELECT language_id FROM D_TRANSLATABLE_LANGUAGES WHERE user_id = ? and language_id = ?",
            [user_id, language_id])
    rs = cursor.fetchall()
    if len(rs) == 0:
        g.db.execute("INSERT INTO D_TRANSLATABLE_LANGUAGES VALUES (?,?,?)",
            [new_translation_list_id, user_id, language_id])
    g.db.commit()
    return make_response(json.jsonify(message="Language added successfully"), 200)

@app.route('/api/admin/language_rejector', methods = ["POST"])
#@exception_detector
@admin_required
def language_rejector():
    parameters = parse_request(request)

    user_email = parameters['email']
    user_id = get_user_id(g.db, user_email)

    g.db.execute("UPDATE D_USERS SET trans_request_state= CASE WHEN is_translator=0 THEN 0 WHEN is_translator=1 THEN 2 END WHERE id = ?", [user_id])
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

        parameters = parse_request(request)
        id_order = parameters['id']
        order_no = parameters['orderNo']

        cursor = g.db.execute("SELECT user_id, amount FROM RETURN_MONEY_BANK_ACCOUNT WHERE id = ? AND order_no = ?", [int(id_order), order_no])
        rs = cursor.fetchall()
        user_id = rs[0][0]
        amount = rs[0][1]

        g.db.execute("UPDATE RETURN_MONEY_BANK_ACCOUNT SET is_returned=1, return_time=CURRENT_TIMESTAMP WHERE id=? AND order_no=?", [id_order, order_no])
        g.db.execute("UPDATE REVENUE SET amount = amount - ? WHERE id = ?", [amount, user_id])

        # Notification
        cursor = g.db.execute("SELECT user_id FROM RETURN_MONEY_BANK_ACCOUNT WHERE  id=? AND order_no=?", [id_order, order_no])
        user_id_no = cursor.fetchall()[0][0]
        send_noti_suite(gcm_server, g.db, user_id_no, 14, None, None)

        g.db.commit()
        return make_response(json.jsonify(
            message="Payed back. Order no: %s" % order_no), 200)

    elif request.method == "GET":
        cursor = g.db.execute("""SELECT
            fact.id, fact.order_no, fact.user_id, user.email, fact.bank_name, fact.account_no, fact.request_time, fact.amount, fact.is_returned, fact.return_time
            FROM RETURN_MONEY_BANK_ACCOUNT fact
            LEFT OUTER JOIN D_USERS user ON fact.user_id = user.id
            WHERE fact.is_returned=0
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
    
