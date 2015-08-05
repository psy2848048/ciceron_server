# -*- coding: utf-8 -*-
from flask import Flask, session, redirect, escape, request, g, abort, json, flash, make_response, send_from_directory
from flask_pushjack import FlaskGCM
from contextlib import closing
from datetime import datetime, timedelta
import hashlib, sqlite3, os, time, requests, sys, paypalrestsdk, logging
from functools import wraps
from werkzeug import secure_filename
from decimal import Decimal
from gcm import GCM
from ciceron_lib import *
from flask.ext.cors import CORS
from flask.ext.session import Session
from celery import Celery

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
GCM_API_KEY = 'AIzaSyDsuwrNC0owqpm6eznw6mUexFt18rBcq88'

SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = "CiceronCookie"

ALLOWED_EXTENSIONS_PIC = set(['jpg', 'jpeg', 'gif', 'png', 'tiff'])
ALLOWED_EXTENSIONS_DOC = set(['doc', 'hwp', 'docx', 'pdf', 'ppt', 'pptx', 'rtf'])
ALLOWED_EXTENSIONS_WAV = set(['wav', 'mp3', 'aac', 'ogg', 'oga', 'flac', '3gp', 'm4a'])
VERSION= "2014.12.28"

CELERY_BROKER_URL = 'redis://localhost'

# APP setting
app = Flask(__name__)
app.secret_key = 'Yh1onQnWOJuc3OBQHhLFf5dZgogGlAnEJ83FacFv'
app.config.from_object(__name__)
app.project_number = 1021873337108

# CORS
cors = CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": "true"}})

# Flask-Session
Session(app)

# Flask-Pushjack
gcm_server = FlaskGCM()
gcm_server.init_app(app)

# Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

date_format = "%Y-%m-%d %H:%M:%S.%f"
super_user = ["pjh0308@gmail.com", "happyhj@gmail.com", "admin@ciceron.me"]

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

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/api', methods=['GET'])
#@exception_detector
def loginCheck():
    if 'useremail' in session:
        client_os = request.args.get('client_os', None)
        registration_id = request.args.get('registration_id', None)

        #if client_os is not None and registration_id is not None:
        #    check_and_update_reg_key(g.db, client_os, registration_id)
        #    g.db.coomit()

        return make_response(json.jsonify(
            useremail=session['useremail'],
            isLoggedIn = True,
            message="User %s is logged in" % session['useremail'],
            token=session.get('token'))
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

@app.route('/api/logout', methods=["GET"])
#@exception_detector
def logout():
    # No parameter needed
    if session['logged_in'] == True:
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
        facebook_id = parameters.get('facebook_id', None)
        name = (parameters['name']).encode('utf-8')
        mother_language_id = int(parameters['mother_language_id'])

        # Duplicate check
        cursor = g.db.execute("select id from D_USERS where email = ?", [buffer(email)])
        check_data = cursor.fetchall()
        if len(check_data) > 0:
            # Status code 400 (BAD REQUEST)
            # Description: Duplicate ID
            return make_response(json.jsonify(
                message="ID %s is duplicated. Please check the email." % email), 412)

        # Insert values to D_USERS
        user_id = get_new_id(g.db, "D_USERS")

        print "New user id: %d" % user_id
        g.db.execute("INSERT INTO D_USERS VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [user_id,
                 buffer(email),
                 buffer(name),
                 mother_language_id,
                 0,
                 None,
                 None,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 None,
                 buffer("nothing")])

        g.db.execute("INSERT INTO PASSWORDS VALUES (?,?)",
            [user_id, buffer(hashed_password)])
        g.db.execute("INSERT INTO REVENUE VALUES (?,?)",
            [user_id, 0])

        g.db.commit() 

        # Status code 200 (OK)
        # Description: Signed up successfully
        return make_response(json.jsonify(message="Registration %s: successful" % email), 200)
    
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

        # Start logic
        cursor = g.db.execute("SELECT * FROM D_USERS WHERE email = ?", [buffer(email)])
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

        # Gather IDs of list form information
        user_id = userinfo[0][0]
        badgeList_id = userinfo[0][13]

        # Get list: other languages translatable
        cursor = g.db.execute("SELECT language_id FROM D_TRANSLATABLE_LANGUAGES WHERE user_id = ?", [user_id])
        other_language_list = (',').join( [ str(item[0]) for item in cursor.fetchall() ] )

        # Get list: badges list
        cursor = g.db.execute("SELECT badge_id FROM D_AWARDED_BADGES WHERE id = ?",
                [badgeList_id])
        badgeList = (',').join([ str(item[0]) for item in cursor.fetchall() ])

        # GET list: user's keywords
        cursor = g.db.execute("SELECT key.text FROM D_USER_KEYWORDS ids JOIN D_KEYWORDS key ON ids.keyword_id = key.id WHERE ids.user_id = ?", [user_id])
        keywords = (',').join([ str(item[0]) for item in cursor.fetchall() ])

        profile = dict(
            user_email=                     email,
            user_name=                      str(userinfo[0][2]),
            user_motherLang=                userinfo[0][3],
            user_profilePicPath=            str(userinfo[0][6]) if userinfo[0][6] is not None else None,
            user_translatableLang=          other_language_list,
            user_numOfRequestsPending=       userinfo[0][7],
            user_numOfRequestsOngoing=       userinfo[0][8],
            user_numOfRequestsCompleted=     userinfo[0][9],
            user_numOfTranslationsPending=   userinfo[0][10],
            user_numOfTranslationsOngoing=   userinfo[0][11],
            user_numOfTranslationsCompleted= userinfo[0][12],
            user_badgeList=                 badgeList,
            user_isTranslator=              True if userinfo[0][4] == 1 else False,
            user_profileText=               str(userinfo[0][14]),
            user_keywords=                  keywords
            )

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
            pic_path = os.path.join(app.config['UPLOAD_FOLDER_PROFILE_PIC'], secure_filename(profile_pic.filename))
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

        point = parameters.get('request_points') if isSos == False else 0

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
                path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_PIC'], secure_filename(binary.filename))
                binary.save(path)

            new_photo_id = get_new_id(g.db, "D_REQUEST_PHOTOS")
            g.db.execute("INSERT INTO D_REQUEST_PHOTOS VALUES (?,?,?)",
                    [new_photo_id, request_id, buffer(path)])

        if (request.files.get('request_sound') != None):
            binary = request.files['request_sound']
            filename = ""
            path = ""
            if sound_allowed_file(binary.filename):
                path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_SOUND'], secure_filename(binary.filename))
                binary.save(path)

            new_sound_id = get_new_id(g.db, "D_REQUEST_SOUNDS")
            g.db.execute("INSERT INTO D_REQUEST_SOUNDS VALUES (?,?)",
                    [new_sound_id, buffer(path)])
        
        if (request.files.get('request_file') != None):
            binary = request.files['request_file']
            filename = ""
            path = ""
            if doc_allowed_file(binary.filename):
                path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_DOC'], secure_filename(binary.filename))
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

        update_user_record(g.db, client_id=client_user_id)
        g.db.commit()

        return make_response(json.jsonify(
            message="Request ID %d  has been posted by %s" % (request_id, parameters['request_clientId'])
            ), 200)

@app.route('/api/requests/<str_request_id>', methods=["DELETE"])
@login_required
#@exception_detector
def delete_requests(str_request_id):
    if request.method == "DELETE":
        request_id = int(str_request_id)
        user_id = get_user_id(g.db, session['useremail'])

        # Check that somebody is translating this request.
        # If yes, requester cannot delete this request
        cursor = g.db.execute("SELECT count(id) FROM F_REQUESTS WHERE id = ? AND client_user_id = ? ",
                [request_id, user_id])
        is_my_request = cursor.fetchall()[0][0]
        if is_my_request == 0:
            return make_response(json.jsonify(
                message="This request is not yours!"), 409)

        cursor = g.db.execute("SELECT count(id) FROM F_REQUESTS WHERE id = ? AND client_user_id = ? AND ongoing_worker_id is null",
                [request_id, user_id])

        num_of_request = cursor.fetchall()[0][0]
        if num_of_request == 0:
            return make_response(json.jsonify(
                message="If translator has taken the request, you cannot delete the request!"), 410)

        g.db.execute("DELETE FROM F_REQUESTS WHERE id = ? AND client_user_id = ? AND ongoing_worker_id is null",
                [request_id, user_id])
        update_user_record(g.db, client_id=user_id)

        # INSERT REFUND PART!!!

        g.db.commit()

        return make_response(json.jsonify(
            message="Request #%d is successfully deleted!" % request_id), 200)

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

        update_user_record(g.db, client_id=request_user_id, translator_id=user_id)
        g.db.commit()

        return make_response(json.jsonify(
            message = "You are in queue for translating request #%d" % request_id
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

        return make_response(json.jsonify(message="You've dequeued from request #%d" % request_id), 200)

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

        g.db.execute("UPDATE F_REQUESTS SET status_id = 1, ongoing_worker_id = ? , start_translating_time = datetime('now') WHERE id = ? AND status_id = 0", [user_id, request_id])

        if strict_translator_checker(g.db, user_id, request_id) == False:
            return make_response(
                json.jsonify(
                   message = "You have no translate permission of given language."
                   ), 401)

        g.db.execute("DELETE FROM D_QUEUE_LISTS WHERE id = ? and request_id = ? and user_id = ?",
                [queue_id, request_id, user_id])

        update_user_record(g.db, client_id=request_user_id, translator_id=user_id)
        g.db.commit()

        return make_response(json.jsonify(
            message = "You are now tranlator of request #%d" % request_id
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
            query_ongoing += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query_ongoing += "ORDER BY registered_time DESC LIMIT 20"

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
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        cursor = g.db.execute(query, [request_id])

        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator")
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "PUT":
        parameters = parse_request(request)

        request_id = int(str_request_id)
        save_request(g.db, parameters, str_request_id, app.config['UPLOAD_FOLDER_RESULT'])
        return make_response(json.jsonify(
            message="Request id %d is auto saved." % request_id
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
            query = "SELECT due_time FROM F_REQUESTS WHERE status_id = 1 AND id = ? "
        else:
            query = "SELECT due_time FROM F_REQUESTS WHERE status_id = 1 AND id = ? AND is_paid = 1 "
        if 'since' in request.args.keys():
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        cursor = g.db.execute(query, [request_id])
        rs = cursor.fetchall()
        return make_response(json.jsonify(default_dueTime=rs[0][0]), 200)

    elif request.method == "POST":
        parameters = parse_request(request)

        request_id = int(str_request_id)
        expected_time = parameters['expectedTime']
        g.db.execute("UPDATE F_REQUESTS SET expected_time = datetime('%%s', ?) WHERE status_id = 1 AND id = ?",
                [expected_time, request_id])
        g.db.commit()
        return make_response(json.jsonify(message="Thank you for responding!"), 200)

    elif request.method == "DELETE":
        request_id = int(str_request_id)
        g.db.execute("UPDATE F_REQUESTS SET ongoing_worker_id = null, status_id = 0 WHERE status_id = 1 AND id = ?",
                [request_id])

        query = None
        if session['useremail'] in super_user:
            query = "SELECT due_time FROM F_REQUESTS WHERE status_id = 1 AND id = ? "
        else:
            query = "SELECT due_time FROM F_REQUESTS WHERE status_id = 1 AND id = ? AND is_paid = 1 "
        cursor = g.db.execute(query, [request_id])

        client_user_id = cursor.fetchall()[0][0]
        translator_user_id = get_user_id(g.db, session['useremail'])
        update_user_record(g.db, client_id=client_user_id, translator_id=translator_user_id)
        g.db.commit()
        return make_response(json.jsonify(message="Wish a better tomorrow!"), 200)

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
                message="Already completed request %d" % request_id), 410)

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
    update_user_record(g.db, client_id=requester_id, translator_id=translator_id)
    g.db.commit()

    return make_response(json.jsonify(
        message="Request id %d is submitted." % request_id
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
        query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
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
        query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
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
            message="The title is set as '%s' to the request #%d" % (title_text, request_id)),
            200)

    else:
        return make_response(json.jsonify(
                message="Inappropriate method of this request. POST only"),
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
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
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
        query = "SELECT * FROM V_REQUESTS WHERE ((status_id = 1 AND ongoing_worker_id = ?) OR (request_id IN (SELECT request_id FROM D_QUEUE_LISTS WHERE user_id = ?))) "
    else:
        query = "SELECT * FROM V_REQUESTS WHERE ((status_id = 1 AND ongoing_worker_id = ? AND is_paid = 1) OR (request_id IN (SELECT request_id FROM D_QUEUE_LISTS WHERE user_id = ?) AND is_paid = 1)) "
    if 'since' in request.args.keys():
        query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += " ORDER BY request_id DESC LIMIT 20"

    cursor = g.db.execute(query, [user_id, user_id])
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
            message="Request #%d is deleted. USD %.2f is returned as requester's points" % (request_id, points)), 200)

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
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query += " ORDER BY submitted_time DESC LIMIT 20"
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
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query += " ORDER BY registered_time DESC LIMIT 20"
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
        query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
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
        query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
    query += " ORDER BY registered_time DESC LIMIT 20"
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
    # Input feedback score
    g.db.execute("UPDATE F_REQUESTS SET feedback_score = ? WHERE id = ?", [feedback_score, request_id])

    # Pay back part
    #query_getTranslator = "SELECT ongoing_worker_id, points FROM F_REQUESTS WHERE id = ? AND is_paid = 1 "
    query_getTranslator = "SELECT ongoing_worker_id, points FROM F_REQUESTS WHERE id = ? "

    cursor = g.db.execute(query_getTranslator, [request_id])
    rs = cursor.fetchall()
    translator_id = rs[0][0]
    pay_amount = rs[0][1]

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
    g.db.commit()

    return make_response(json.jsonify(
        message="The requester rated to request #%d as %d points (in 0~2). And translator has been earned USD %.2f" % (request_id, feedback_score, pay_amount*return_rate)),
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
        if group_id != -1:
            return make_response(json.jsonify(message="Group %d is deleted." % group_id), 200)
        else:
            return make_response(json.jsonify(message="You cannot delete 'Documents' group"), 401)

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
            query += "AND registered_time < datetime(%s, 'unixepoch') " % request.args.get('since')
        query += "ORDER BY request_id DESC"
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
    query += " ORDER BY request_id DESC LIMIT 20"
    cursor = g.db.execute(query, [user_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/incomplete/<str_request_id>', methods = ["PUT", "DELETE", "POST"])
#@exception_detector
@login_required
def client_incompleted_item_control(str_request_id):
    if request.method == "PUT":
        # Only update due_time and price

        # It can be used in:
        #    1) Non-selected request
        #    2) Give more chance to the trusted translator

        request_id = int(request_id)
        parameters = parse_request(request)

        # Addional time: unit is second, counted from NOW
        additional_time_in_sec = parameters['user_additionalTime']
        additional_price = 0
        if parameters.get('user_additionalPrice') != None:
            additional_price = float(parameters['user_additionalPrice'])

        user_id = get_user_id(g.db, session['useremail'])
        # Change due date w/o addtional money
        if additional_price == 0:
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 0 WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is null", [request_id, user_id])
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 1 WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is not null", [request_id, user_id])
            g.db.commit()

            return make_response(json.jsonify(
                message="Request #%d is renewed" % request_id,
                api=None), 200)

        # Change due date w/additional money
        else:
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 0, is_paid = 0, points = points + ? WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is null", [additional_price, request_id, user_id])
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 1, is_paid = 0, points = points + ? WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is not null", [additional_price, request_id, user_id])
            g.db.commit()

            return make_response(json.jsonify(
                message="Request #%d is renewed. Please execute the API provided with POST methid" % request_id,
                api="/api/user/requests/%d/payment/start"%request_id), 200)

    elif request.method == "POST":
        # It can be used in:
        #    1) Say goodbye to translator, back to stoa

        request_id = int(request_id)
        parameters = parse_request(request)

        # Addional time: unit is second, counted from NOW
        additional_time_in_sec = parameters['user_additionalTime']
        additional_price = 0
        if parameters.get('user_additionalPrice') != None:
            additional_price = float(parameters['user_additionalPrice'])

        user_id = get_user_id(g.db, session['useremail'])
        # Change due date w/o addtional money
        if additional_price == 0:
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 0, ongoing_worker_id = null WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is not null", [request_id, user_id])
            g.db.commit()

            return make_response(json.jsonify(
                message="Request #%d is posted back to stoa." % request_id,
                api=None), 200)

        # Change due date w/additional money
        else:
            g.db.execute("UPDATE F_REQUESTS SET due_time = datetime('now', '+%d seconds'), status_id = 0, is_paid = 0, points = points + ?, ongoing_worker_id = null WHERE id = ? AND status_id = -1 AND client_user_id = ? AND ongoing_worker_id is not null", [additional_price, request_id, user_id])
            g.db.commit()

            return make_response(json.jsonify(
                message="Request #%d is renewed. Please execute the API provided with POST methid" % request_id,
                api="/api/user/requests/%d/payment/start"%request_id), 200)

    elif request.method == "DELETE":
        # It can be used in:
        #    1) Say goodbye to translator. And he/she don't want to leave his/her request
        request_id = int(request_id)
        user_id = get_user_id(g.db, session['useremail'])

        g.db.execute("UPDATE F_REQUESTS SET is_paid = 0 WHERE id = ? AND status_id = -1 AND client_user_id = ? ", [request_id, user_id])

        cursor = g.db.execute("SELECT points FROM F_REQUESTS WHERE id = ? AND status_id = -1 AND client_user_id = ?", [request_id, user_id])
        points = float(cursor.fetchall()[0][0])
        g.db.execute("UPDATE REVENUE SET amount = amount + ? WHERE id = ?", [points, user_id])
        g.db.commit()

        return make_response(json.jsonify(
            message="Your request #%d is deleted. Your points USD %.2f is backed in your account" % [request_id, points]), 200)

@app.route('/api/user/requests/<str_request_id>/payment/start', methods = ["POST"])
#@exception_detector
@login_required
def pay_for_request(str_request_id):
    parameters = parse_request(request)

    pay_via = parameters.get('pay_via')
    request_id = int(str_request_id)
    amount = float(parameters['pay_amount'])

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
            "return_url": "http://52.11.126.237:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=success&user_id=%s&pay_amt=%.2f" % (request_id, session['useremail'], amount),
            "cancel_url": "http://52.11.126.237:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=fail&user_id=%s&pay_amt=%.2f" % (request_id, session['useremail'], amount)},
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

        red_link = "http://52.11.126.237:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=success&user_id=%s&pay_amt=%.2f" % (request_id, session['useremail'], amount)
        if bool(rs) is True:
            return make_response(json.jsonify(message="Redirect link is provided!", link=paypal_link, redirect_url=red_link), 200)
        else:
            return make_response(json.jsonify(message="Something wrong in paypal"), 400)

    elif pay_via == 'alipay':
        from alipay import Alipay
        alipay_obj = Alipay(pid='my_pid', key='my_key', seller_email='my_email')
        params = {
            'subject': '是写论翻译'.encode('utf-8'),
            'total_fee': '%.2f' % amount,
            'currency': 'USD',
            'quantity': '1',
            'notify_url': "http://52.11.126.237:5000/api/user/requests/%d/payment/postprocess?pay_via=alipay&status=success&user_id=%s&pay_amt=%.2f" % (request_id, session['useremail'], amount)
            }
        provided_link = alipay_obj.create_direct_pay_by_user_url(**params)

        return make_response(json.jsonify(
            message="Link to Alipay is provided.",
            link=provided_link), 200)

@app.route('/api/user/requests/<str_request_id>/payment/postprocess', methods = ["GET"])
#@exception_detector
#@login_required
def pay_for_request_process(str_request_id):
    request_id = int(str_request_id)
    user = request.args['user_id']
    pay_via = request.args['pay_via']
    is_success = True if request.args['status'] == "success" else False
    payment_id = request.args['paymentId']
    payer_id = request.args['PayerID']
    amount = float(request.args.get('pay_amt'))

    if pay_via == 'paypal':
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
            return make_response("success", 200)

        elif token == session.get('token') and request_id == session.get('pending_reqeust') and not is_success:
            # REDIRECT TO FAIL PAGE
            # PAYMENT FAIL
            return redirect("page_provided_with /user/requests/%d/payment" % request_id)

    elif pay_via == "alipay":
        if is_success:
            # Get & store order ID and price

            ##############
            ## Complete payment
            ##############

            g.db.execute("UPDATE F_REQUESTS SET is_paid = ? WHERE id = ?", [True, request_id])

            # Payment information update
            g.db.execute("INSERT INTO PAYMENT_INFO (id, request_id, client_id, payed_via, order_no, pay_amount, payed_time) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)",
                    [payment_info_id, request_id, buffer(user), buffer("alipay"), buffer(payment_id), amount])

            g.db.commit()

@app.route('/api/user/device', methods = ["POST"])
#@exception_detector
@login_required
def register_or_update_register_id():
    parameters = parse_request(request)

    device_os = parameters['user_deviceOS']
    reg_key = parameters['user_regKey']
    user_id = get_user_id(g.db, session['useremail'])

    record_id = get_new_id(g.db, "D_MACHINES")
    cursor = g.db.execute("SELECT count(*) FROM D_MACHINES WHERE os_id = (SELECT id FROM D_MACHINE_OSS WHERE text = ?) AND user_id = ?"
            [buffer(device_os), user_id])
    num = cursor.fetchall()[0][0]

    if num == 0:
        g.db.execute("INSERT INTO D_MACHINES VALUES (?, ?, (SELECT id FROM D_MACHINE_OSS WHERE text = ?), ?, ?)",
            [record_id, user_id, buffer(device_os), buffer(reg_key), 1])
    else:
        g.db.execute("UPDATE D_MACHINES SET reg_key = ? WHERE os_id = (SELECT id FROM D_MACHINE_OSS WHERE text = ?) AND user_id = ?",
            [buffer(reg_key), buffer(device_os), user_id])

    return make_response(json.jsonify(message="Succefully updated/inserted"), 200)

@app.route('/api/access_file/<directory>/<filename>')
@login_required
def access_file(directory, filename):
    print directory
    print filename
    return send_from_directory(directory, filename)

@app.route('/api/admin/delete_sos', methods = ["GET"])
#@exception_detector
def delete_sos():
    g.db.execute("""UPDATE F_REQUESTS SET is_paid=0
                     WHERE status_id = 1 AND isSos=1 AND CURRENT_TIMESTAMP >= datetime(registered_time, '+30 minutes')""")
    g.db.commit()
    return make_response(json.jsonify(message="Cleaned"), 200)

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

################################################################################
#########                        ADMIN TOOL                            #########
################################################################################

@app.route('/api/admin/expired_request_checker', methods = ["GET"])
#@exception_detector
@admin_required
def publicize():
    g.db.execute("""UPDATE F_REQUESTS SET status_id = -1
                     WHERE (status_id = 1 AND expected_time is null AND submitted_time is null AND (CURRENT_TIMESTAMP-start_translating_time) > ((due_time-start_translating_time)/3) AND due_time > datetime(start_translating_time, '+6 hours') )
                     OR (status_id = 1 AND expected_time is not null and submitted_time is null AND CURRENT_TIMESTAMP > due_time) 
                     OR (status_id = 0 AND CURRENT_TIMESTAMP > due_time) """)
    g.db.commit()
    return make_response(json.jsonify(message="Expired requests are publicized"), 200)

@app.route('/api/admin/language_assigner', methods = ["POST"])
#@exception_detector
@admin_required
def language_assigner():
    parameters = parse_request(request)

    user_email = parameters['email']
    language_id = int(parameters['language_id'])
    user_id = get_user_id(g.db, user_email)
    new_translation_list_id = get_new_id(g.db, "D_TRANSLATABLE_LANGUAGES")

    g.db.execute("UPDATE D_USERS SET is_translator = 1 WHERE id = ?", [user_id])
    cursor = g.db.execute("SELECT language_id FROM D_TRANSLATABLE_LANGUAGES WHERE user_id = ? and language_id = ?",
            [user_id, language_id])
    rs = cursor.fetchall()
    if len(rs) == 0:
        g.db.execute("INSERT INTO D_TRANSLATABLE_LANGUAGES VALUES (?,?,?)",
            [new_translation_list_id, user_id, language_id])
    g.db.commit()
    return make_response(json.jsonify(message="Language added successfully"), 200)

@app.route('/api/admin/return_money', methods = ["GET", "POST"])
#@exception_detector
@admin_required
def return_money():
    if request.method == "POST":
        parameters = parse_request(request)
        user_id = get_user_id(session['useremail'])
        where_to_return = parameters['user_whereToReturn']
        payment_id = parameters['user_PaymentId']
        money_amount = parameters['user_revenue']

        # Logic flow
        #   1) Check how much money in user's revenue
        #     - If request amount is exceeded user's revenue, reject refund request.
        #   2) Send via paypal

        # SANDBOX
        API_ID = "APP-80W284485P519543T"
        API_USER = "contact-facilitator_api1.ciceron.me"
        API_PASS = 'R8H3MF9EQYTNHD22'
        API_SIGNATURE = 'ABMADzBsLmPPJmWRmjvj6KuGeZ4MAoDQ7X0sCtehblA93Yolgrjto1tO'

        # Live
        # API_ID = 'Should be issued later'
        # API_USERNAME = 'contact_api1.ciceron.me'
        # API_PASS = 'GJ5JNF596R3VNBK4'
        # API_SIGNATURE = 'AiPC9BjkCyDFQXbSkoZcgqH3hpacAqbVr1jqSkiaKlwohFFSWhFvOxwI'

        # END POINT = https://svcs.sandbox.paypal.com/AdaptivePayments/Pay
        # POST
        # Input header:
        # X-PAYPAL-APPLICATION-ID = API_ID
        # X-PAYPAL-SECURITY-USERID = API_USER
        # X-PAYPAL-SECURITY-PASSWORD = API_PASS
        # X-PAYPAL-SECURITY-SIGNATURE = API_SIGNATURE
        # X-PAYPAL-DEVICE-IPADDRESS = IP_ADDRESS
        # X-PAYPAL-REQUEST-DATA-FORMAT = 'JSON'
        # X-PAYPAL-RESPONSE-DATA-FORMAT = 'JSON'

        body = {"returnUrl":"http://example.com/returnURL.htm",
                "requestEnvelope":
                   {"errorLanguage":"en_KR"},
                "currencyCode":"USD",
                "receiverList":{
                    "receiver":
                    [{"email":"psy2848048@gmail.com","amount":"10.00",}]
                    },
                "cancelUrl":"http://example.com/cancelURL.htm",
                "actionType":"PAY"}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    
