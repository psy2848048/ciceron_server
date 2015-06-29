# -*- coding: utf-8 -*-
from flask import Flask, session, redirect, escape, request, g, abort, json, flash, make_response
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

DATABASE = '../db/ciceron.db'
VERSION = '1.0'
DEBUG = True
BASEPATH = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER_PROFILE_PIC = "profile_pic"
UPLOAD_FOLDER_REQUEST_PIC = "request_pic"
UPLOAD_FOLDER_REQUEST_SOUND = "sounds"
UPLOAD_FOLDER_REQUEST_DOC = "request_doc"
UPLOAD_FOLDER_REQUEST_TEXT =  "request_text"
SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = "CiceronCookie"

UPLOAD_FOLDER_RESULT = "translate_result"

ALLOWED_EXTENSIONS_PIC = set(['jpg', 'jpeg', 'gif', 'png', 'tiff'])
ALLOWED_EXTENSIONS_DOC = set(['doc', 'hwp', 'docx', 'pdf', 'ppt', 'pptx', 'rtf'])
ALLOWED_EXTENSIONS_WAV = set(['wav', 'mp3', 'aac', 'ogg', 'oga', 'flac', '3gp', 'm4a'])
VERSION= "2014.12.28"

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": "true"}})
app.secret_key = 'Yh1onQnWOJuc3OBQHhLFf5dZgogGlAnEJ83FacFv'
app.config.from_object(__name__)
app.project_number = 1021873337108
Session(app)

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

def pic_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_PIC']

def doc_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_DOC']

@app.route('/api', methods=['GET'])
@exception_detector
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
            message="User %s is logged in" % session['useremail'])
            , 200)
    else:
        return make_response(json.jsonify(
            useremail=None,
            isLoggedIn=False,
            message="No user is logged in")
            , 403)

@app.route('/api/login', methods=['POST', 'GET'])
@exception_detector
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
        return make_response(json.jsonify(identifier=salt, session_id=session.sid), 200)

@app.route('/api/logout', methods=["GET"])
@exception_detector
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
@exception_detector
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
@exception_detector
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
@exception_detector
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
        other_language_list_id = userinfo[0][5]
        badgeList_id = userinfo[0][13]

        # Get list: other languages translatable
        cursor = g.db.execute("SELECT language_id FROM D_TRANSLATABLE_LANGUAGES WHERE id = ?",
                [other_language_list_id])
        other_language_list = [ item[0] for item in cursor.fetchall() ]

        # Get list: badges list
        cursor = g.db.execute("SELECT badge_id FROM D_AWARDED_BADGES WHERE id = ?",
                [badgeList_id])
        badgeList = [ item[0] for item in cursor.fetchall() ]

        profile = dict(
            user_email=                     email,
            user_name=                      str(userinfo[0][2]),
            user_motherLang=                userinfo[0][3],
            user_profilePicPath=            str(userinfo[0][5]) if userinfo[0][5] is not None else None,
            user_translatableLang=          other_language_list,
            user_numOfRequestPending=       userinfo[0][7],
            user_numOfRequestOngoing=       userinfo[0][8],
            user_numOfRequestCompleted=     userinfo[0][9],
            user_numOfTranslationPending=   userinfo[0][10],
            user_numOfTranslationOngoing=   userinfo[0][11],
            user_numOfTranslationCompleted= userinfo[0][12],
            user_badgeList=                 badgeList,
            user_isTranslator=              True if userinfo[0][4] == 1 else False,
            user_profileText=               str(userinfo[0][14])
            )

        if is_your_profile == True:
            cursor = g.db.execute("SELECT amount FROM REVENUE WHERE id = ?",  [user_id])
            profile['user_revenue'] = cursor.fetchall()[0][0]

        return make_response(json.jsonify(profile), 200)

    elif request.method == "POST":
        # Method: GET
        # Parameters
        #     user_email: String, text
        #     user_profilePic: binary

        # Get parameter value
        parameters = parse_request(request)

        profileText = (parameters.get('user_profileText', None)).encode('utf-8')
        profile_pic = request.files.get('photo', None)

        # Start logic
        # Get user number
        email = session['useremail']

        # Profile pic update
        if profileText is not None:
            g.db.execute("UPDATE D_USERS SET profile_text = ? WHERE email = ?",
                    [buffer(profileText), buffer(email)])

        # Profile photo update
        filename = ""
        path = ""
        if profile_pic and pic_allowed_file(profile_pic.filename):
            pic_path = os.path.join(app.config['UPLOAD_FOLDER_PROFILE_PIC'], secure_filename(profile_pic.filename))
            profile_pic.save(pic_path)

            g.db.execute("UPDATE D_USERS SET profile_pic_path = ? WHERE email = ?", [buffer(pic_path), buffer(session['useremail'])])

        #if is_translator:
        #    g.db.execute("UPDATE D_USERS SET is_translator = ? WHERE email = ?", [is_translator, buffer(session['useremail'])])

        g.db.commit()
        return make_response(json.jsonify(
            message="Your profile is susccessfully updated!"), 200)

@app.route('/user/profile/photo', methods=["POST", "GET"])
@exception_detector
@login_required
def user_profile_photo():
    if request.method == "POST":
        try:
            print "Only supports multipart/form-data"
            profile_pic = request.files['photo']
            filename = ""
            path = ""
            if profile_pic and pic_allowed_file(profile_pic.filename):
                pic_path = os.path.join(app.config['UPLOAD_FOLDER_PROFILE_PIC'], secure_filename(profile_pic.filename))
                profile_pic.save(pic_path)

            g.db.execute("UPDATE D_USERS SET profile_pic_path = ? WHERE email = ?", [buffer(pic_path), buffer(session['useremail'])])
            g.db.commit()

            return make_response(json.jsonify(
                    message="Upload complete",
                    path=pic_path),
                200)

        except KeyError as e:
            return make_response(json.jsonify(
                message="Photo upload only supports multipart/form-data. And it takes data from the parameter named 'photo'. Please check your configuration.",
                ), 400)

    else:
        return '''
            <!doctype html>
            <title>Upload test / Profile pic</title>
            <h1>Upload new File</h1>
            <form action="" method=post enctype=multipart/form-data>
              <p><input type=file name=file>
                 <input type=submit value=Upload>
            </form>
            '''

@app.route('/api/requests', methods=["GET", "POST"])
@exception_detector
def requests():
    if request.method == "GET":
        # Request method: GET
        # Parameters
        #     since(optional): Timestamp, take recent 20 post before the timestamp.
        #                  If this parameter is not provided, recent 20 posts from now are returned
        
        query = """SELECT * FROM V_REQUESTS WHERE
            (ongoing_worker_id is null AND status_id = 0 AND isSos = 0 AND is_paid = 1) OR (isSos = 1) """
        if 'since' in request.args.keys():
            query += "AND registered_time < datetime(%f) " % Decimal(request.args['since'])
        query += " ORDER BY registered_time DESC LIMIT 20"

        cursor = g.db.execute(query)
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs)

        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        # Method: POST
        # Parameters -> Please check code

        request_id = get_new_id(g.db, "F_REQUESTS")
        client_user_id = get_user_id(g.db, request.form['request_clientId'])
        original_lang_id = request.form['request_originalLang']
        target_lang_id = request.form['request_targetLang']
        isSos = parameter_to_bool(parameters['request_isSos'])
        format_id = request.form.get('parametersat')
        subject_id = request.form.get('request_subject')
        registered_time = request.form['request_registeredTime']
        is_text = parameter_to_bool(request.form.get('request_isText', False))
        text_string = (request.form.get('request_text')).encode('utf-8')
        is_photo = parameter_to_bool(request.form.get('request_isPhoto', False))
        #photo_binary
        is_sound = parameter_to_bool(request.form.get('request_isSound', False))
        #sound_binary
        is_file = parameter_to_bool(request.form.get('request_isFile', False))
        #file_binary
        words = request.form.get('reqeust_words', 0)
        due_time = request.form['request_dueTime']
        point = request.form.get('request_points')
        context = (request.form.get('request_context')).encode('utf-8')

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
        if (request.files.get('request_photo') is not None):
            binary = request.files['request_photo']
            filename = ""
            path = ""
            if pic_allowed_file(binary.filename):
                path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_PIC'], secure_filename(binary.filename))
                binary.save(path)

            new_photo_id = get_new_id(g.db, "D_REQUEST_PHOTOS")
            g.db.execute("INSERT INTO D_REQUEST_PHOTOS VALUES (?,?,?)",
                    [new_photo_id, request_id, buffer(path)])

        if (request.files.get('request_sound') is not None):
            binary = request.files['request_sound']
            filename = ""
            path = ""
            if sound_allowed_file(binary.filename):
                path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_SOUND'], secure_filename(binary.filename))
                binary.save(path)

            new_sound_id = get_new_id(g.db, "D_REQUEST_SOUNDS")
            g.db.execute("INSERT INTO D_REQUEST_SOUNDS VALUES (?,?)",
                    [new_sound_id, buffer(path)])
        
        if (request.files.get('request_file') is not None):
            binary = request.files['request_file']
            filename = ""
            path = ""
            if doc_allowed_file(binary.filename):
                path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_DOC'], secure_filename(binary.filename))
                binary.save(path)

            new_file_id = get_new_id(g.db, "D_REQUEST_FILES")
            g.db.execute("INSERT INTO D_REQUEST_FILES VALUES (?,?)",
                    [new_file_id, buffer(path)])

        if text_string:
            filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + ".txt"
            path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_TEXT'], filename)
            import codecs
            f = codecs.open(path, 'w', "utf-8")
            f.write(text_string)
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
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
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
                    registered_time,      # registered_time
                    due_time,             # due_time
                    point,                # points
                    new_context_id,       # context_id
                    None,                 # comment_id
                    None,                 # tone_id
                    None,                 # translatedText_id
                    is_paid]))               # is_paid

        update_user_record(g.db, client_id=client_user_id)
        g.db.commit()

        # Marking for payment
        session['pending_reqeust'] = request_id
        session['token'] = random_string_gen()

        return make_response(json.jsonify(
            message="Request ID %d  has been posted by %s" % (request_id, parameters['request_clientId'])
            ), 200)

@app.route('/api/requests/<str_request_id>', methods=["DELETE"])
@login_required
@exception_detector
def delete_requests(str_request_id):
    if request.method == "DELETE":
        request_id = int(str_request_id)
        user_id = get_user_id(g.db, session['useremail'])

        # Check that somebody is translating this request.
        # If yes, requester cannot delete this request
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
@exception_detector
@translator_checker
def show_queue():
    if request.method == "GET":
        # Request method: GET
        # Parameters
        #     since(OPTIONAL): Timestamp integer, for paging

        my_user_id = get_user_id(g.db, session['useremail'])
        query_pending = """SELECT * FROM V_REQUESTS 
            WHERE request_id IN (SELECT request_id FROM D_QUEUE_LISTS WHERE user_id = ?) AND is_paid = 1 """
        if 'since' in request.args.keys():
            query_pending += "AND registered_time < datetime(%f) " % Decimal(request.args['since'])
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
        cursor = g.db.execute("SELECT queue_id, client_user_id FROM F_REQUESTS WHERE id = ? AND is_paid = 1 ", [request_id])
        rs = cursor.fetchall()

        if len(rs) == 0: return make_response(json.jsonify(message = "There is no request ID %d" % request_id), 400)

        if translator_email is None: user_id = get_user_id(g.db, session['useremail'])
        else:                        user_id = get_user_id(g.db, translator_email)
        request_user_id = rs[0][1]

        if strict_translator_checker(g.db, user_id, request_id) == False:
            return make_response(
                json.jsonify(
                   message = "You have no translate permission of given language."
                   ), 401)

        cursor = g.db.execute("SELECT is_translator FROM D_USERS WHERE id = ?", [user_id])
        rs = cursor.fetchall()
        if len(rs) == 0 or rs[0][0] == 0: return make_response(json.jsonify( message = "This user is not a translator."), 403)

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

        if queue_id is None:
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
@exception_detector
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
@exception_detector
def pick_request():
    if request.method == "POST":
        # Request method: POST
        # Parameters
        #    request_id: requested post id
        parameters = parse_request(request)

        request_id = int(parameters['request_id'])
        my_user_id = get_user_id(g.db, session['useremail'])

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

        g.db.execute("UPDATE F_REQUESTS SET status_id = 1, ongoing_worker_id = ? WHERE id = ? AND status_id = 0", [my_user_id, request_id])

        user_id = get_user_id(g.db, session['useremail'])

        if strict_translator_checker(g.db, my_user_id, request_id) == False:
            return make_response(
                json.jsonify(
                   message = "You have no translate permission of given language."
                   ), 401)

        g.db.execute("DELETE FROM D_QUEUE_LISTS WHERE id = ? and request_id = ? and user_id = ?",
                [queue_id, request_id, my_user_id])

        update_user_record(g.db, client_id=request_user_id, translator_id=my_user_id)
        g.db.commit()

        return make_response(json.jsonify(
            message = "You are now tranlator of request #%d" % request_id
            ), 200)

    elif request.method == "GET":
        # Request method: GET
        # Parameters
        #     since (optional): Timestamp integer

        query_ongoing = """SELECT * FROM V_REQUESTS WHERE ongoing_worker_id = ? AND is_paid = 1 """
        if 'since' in request.args.keys():
            query_ongoing += "AND registered_time < datetime(%f) " % Decimal(request.args['since'])
        query_ongoing += "ORDER BY registered_time DESC LIMIT 20"

        my_user_id = get_user_id(g.db, session['useremail'])
        cursor = g.db.execute(query_ongoing, [my_user_id])
        rs = cursor.fetchall()

        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator") # PLEASE REVISE
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/ongoing/<str_request_id>', methods=["GET", "PUT"])
@exception_detector
@translator_checker
@login_required
def working_translate_item(str_request_id):
    if request.method == "GET":
        request_id = int(str_request_id)
        cursor = g.db.execute("SELECT * FROM V_REQUESTS WHERE status_id = 1 AND request_id = ? AND is_paid = 1 ", [request_id])
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
@exception_detector
@translator_checker
@login_required
def expected_time(str_request_id):
    if request.method == "GET":
        request_id = int(str_request_id)
        cursor = g.db.execute("SELECT due_time FROM F_REQUESTS WHERE status_id = 1 AND id = ? AND is_paid = 1 ", [request_id])
        rs = cursor.fetchall()
        return make_response(json.jsonify(default_dueTime=rs[0][0]), 200)

    elif request.method == "POST":
        parameters = parse_request(request)

        request_id = int(str_request_id)
        expected_time = parameters['expectedTime']
        g.db.execute("UPDATE F_REQUESTS SET expected_time = ? WHERE status_id = 1 AND id = ?",
                [expected_time, request_id])
        g.db.commit()
        return make_response(json.jsonify(message="Thank you for responding!"), 200)

    elif request.method == "DELETE":
        request_id = int(str_request_id)
        g.db.execute("UPDATE F_REQUESTS SET ongoing_worker_id = null, status_id = 0 WHERE status_id = 1 AND id = ?",
                [request_id])

        cursor = g.db.execute("SELECT client_user_id FROM F_REQUESTS WHERE id = ? AND is_paid = 1 ", [request_id])
        client_user_id = cursor.fetchall()[0][0]
        translator_user_id = get_user_id(g.db, session['useremail'])
        update_user_record(g.db, client_id=client_user_id, translator_id=translator_user_id)
        g.db.commit()
        return make_response(json.jsonify(message="Wish a better tomorrow!"), 200)

@app.route('/api/user/translations/complete', methods=["POST"])
@exception_detector
@login_required
@translator_checker
def post_translate_item():
    parameters = parse_request(request)

    request_id = int(parameters['request_id'])
    save_request(g.db, parameters, str_request_id, app.config['UPLOAD_FOLDER_RESULT'])

    # Assign default group to requester and translator
    cursor = g.db.execute("SELECT client_user_id, ongoing_worker_id FROM V_REQUESTS WHERE request_id = ? AND is_paid = 1 AND status_id = 1 ", [request_id])
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
    g.db.execute("UPDATE F_REQUESTS SET status_id = 2, client_completed_group_id=?, translator_completed_group_id=?, submitted_time=? WHERE id = ?", [requester_default_group_id, translator_default_group_id, datetime.now(), request_id])
    update_user_record(g.db, client_id=requester_id, translator_id=translator_id)
    g.db.commit()

    return make_response(json.jsonify(
        message="Request id %d is submitted." % request_id
        ), 200)

@app.route('/api/user/translations/complete/<str_request_id>', methods = ["GET"])
@exception_detector
@login_required
@translator_checker
def translation_completed_items_detail(str_request_id):
    request_id = int(str_request_id)
    user_id = get_user_id(g.db, session['useremail'])
    cursor = g.db.execute("SELECT * FROM V_REQUESTS WHERE status_id = 2 AND request_id = ? AND ongoing_worker_id = ? AND is_paid = 1", [request_id, user_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_translator")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/complete', methods = ["GET"])
@exception_detector
@login_required
@translator_checker
def translation_completed_items_all():
    since = request.args.get('since', None)
    user_id = get_user_id(g.db, session['useremail'])

    query = "SELECT * FROM V_REQUESTS WHERE status_id = 2 AND ongoing_worker_id = ? AND is_paid = 1 "
    if since is not None: query += "AND registered_time < datetime(%f) " % Decimal(request.args['since'])
    query += " ORDER BY request_id LIMIT 20"

    cursor = g.db.execute(query, [user_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_translator")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/translations/complete/<str_request_id>/title', methods = ["POST"])
@exception_detector
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
@exception_detector
@translator_checker
@login_required
def translators_complete_groups():
    if request.method == "GET":
        result = complete_groups(g.db, "D_TRANSLATOR_COMPLETED_GROUPS", "GET")
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        parameters = parse_request(request)
        group_name = complete_groups(g.db, parameters, "D_TRANSLATOR_COMPLETED_GROUPS", "POST")
        if group_name == -1:
            return make_response(json.jsonify(message="'Document' is reserved name"), 401)
        else:
            return make_response(json.jsonify(message="New group %s has been created" % group_name), 200)

@app.route('/api/user/translations/complete/groups/<str_group_id>', methods = ["DELETE", "PUT"])
@exception_detector
@translator_checker
@login_required
def modify_translators_complete_groups(str_group_id):
    parameters = parse_request(request)

    if request.method == "DELETE":
        group_id = complete_groups(g.db, parameters, "D_TRANSLATOR_COMPLETED_GROUPS", "DELETE", url_group_id=str_group_id)
        if group_id == -1:
            return make_response(json.jsonify(message="Group 'Document' is default. You cannot delete it!"), 401)
        else:
            return make_response(json.jsonify(message="Group %d is deleted. Requests are moved into default group" % group_id), 200)
    elif request.method == "PUT":
        group_name = complete_groups(g.db, parameters, "D_TRANSLATOR_COMPLETED_GROUPS", "PUT")
        if group_name == -1:
            return make_response(json.jsonify(message="You cannot change the name of the group to 'Document'. It is default group name" % group_name), 401)
        else:
            return make_response(json.jsonify(message="Group name is changed to %s" % group_name), 200)

@app.route('/api/user/translations/complete/groups/<str_group_id>', methods = ["POST", "GET"])
@exception_detector
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
        cursor = g.db.execute("SELECT * FROM V_REQUESTS WHERE ongoing_worker_id = ? AND translator_completed_group_id = ? AND is_paid = 1 ",
            [my_user_id, group_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="complete_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/pending', methods=["GET"])
@exception_detector
@login_required
def show_pending_list_client():
    if request.method == "GET":
        user_id = get_user_id(g.db, session['useremail'])
        query = "SELECT * FROM V_REQUESTS WHERE client_user_id = ? AND status_id = 0"
        cursor = g.db.execute(query, [user_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/pending/<str_request_id>', methods=["GET"])
@exception_detector
@login_required
def show_pending_item_client(str_request_id):
    if request.method == "GET":
        user_id = get_user_id(g.db, session['useremail'])
        request_id = int(str_request_id)
        query = "SELECT * FROM V_REQUESTS WHERE request_id = ? AND client_user_id = ? AND status_id = 0 AND is_paid = 1 "
        cursor = g.db.execute(query, [request_id, user_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="pending_client")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/ongoing', methods=["GET"])
@exception_detector
@login_required
def show_ongoing_list_client():
    if request.method == "GET":
        user_id = get_user_id(g.db, session['useremail'])
        query = "SELECT * FROM V_REQUESTS WHERE client_user_id = ? AND status_id = 1 is_paid = 1 "
        cursor = g.db.execute(query, [user_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/ongoing/<str_request_id>', methods=["GET"])
@exception_detector
@login_required
def show_ongoing_item_client(str_request_id):
    if request.method == "GET":
        user_id = get_user_id(g.db, session['useremail'])
        request_id = int(str_request_id)
        query = "SELECT * FROM V_REQUESTS WHERE request_id = ? AND client_user_id = ? AND status_id = 1 AND is_paid = 1 "
        cursor = g.db.execute(query, [request_id, user_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="ongoing_translator")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/complete', methods = ["GET"])
@exception_detector
@login_required
def client_completed_items():
    request_id = int(str_request_id)
    user_id = get_user_id(g.db, session['useremail'])
    cursor = g.db.execute("SELECT * FROM V_REQUESTS WHERE status_id = 2 AND client_user_id = ? AND is_paid = 1 ", [user_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/complete/<str_request_id>', methods = ["GET"])
@exception_detector
@login_required
def client_completed_items_detail(str_request_id):
    request_id = int(str_request_id)
    user_id = get_user_id(g.db, session['useremail'])
    cursor = g.db.execute("SELECT * FROM V_REQUESTS WHERE status_id = 2 AND client_user_id = ? AND request_id = ? AND is_paid = 1 ", [user_id, request_id])
    rs = cursor.fetchall()
    result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")
    return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/complete/<str_request_id>/title', methods=["POST"])
@exception_detector
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

        # Pay back part
        cursor = g.db.execute("SELECT ongoing_worker_id FROM F_REQUESTS WHERE id = ? AND is_paid = 1 ", [request_id])
        rs = cursor.fetchall()
        translator_id = rs[0][0]

        cursor = g.db.execute("SELECT count(*) FROM F_REQUESTS WHERE ongoing_worker_id = ? AND status_id = 2 AND is_paid = 1 AND submitted_time BETWEEN date('now', '-1 month') AND date('now')", [translator_id])
        rs = cursor.fetchall()
        translator_performance = rs[0][0]

        # Back rate
        back_rate = 0.0
        if translator_performance >= 80:
            back_rate = 0.8
        elif translator_performance >= 60:
            back_rate = 0.7
        elif translator_performance >= 45:
            back_rate = 0.65
        elif translator_performance >= 30:
            back_rate = 0.6
        else:
            back_rate = 0.55

        g.db.execute("UPDATE PAYMENT_INFO SET translator_id=?, is_payed_back=?, back_amount=pay_amount*? WHERE request_id = ?",
                [translator_id, False, back_rate, request_id])
        g.db.commit()

        return make_response(json.jsonify(
            message="The title is set as '%s' to the request #%d" % (title_text, request_id)),
            200)

    else:
        return make_response(json.jsonify(
                message="Inappropriate method of this request. POST only"),
            405)

@app.route('/api/user/requests/complete/groups', methods = ["GET"])
@exception_detector
@login_required
def client_complete_groups():
    if request.method == "GET":
        result = complete_groups(g.db, "D_CLIENT_COMPLETED_GROUPS", "GET")
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        parameters = parse_request(request)

        group_name = complete_groups(g.db, parameters, "D_CLIENT_COMPLETED_GROUPS", "POST")
        if group_name != -1:
            return make_response(json.jsonify(message="New group %s has been created" % group_name), 200)
        else:
            return make_response(json.jsonify(message="'Documents' is default group name"), 401)

@app.route('/api/user/requests/complete/groups/<str_group_id>', methods = ["PUT", "DELETE"])
@exception_detector
@login_required
def modify_client_completed_groups(str_group_id):
    parameters = parse_request(request)

    if request.method == "PUT":
        group_name = complete_groups(g.db, parameters, "D_CLIENT_COMPLETED_GROUPS", "PUT", url_group_id=str_group_id)
        if group_name != -1:
            return make_response(json.jsonify(message="Group name is changed to %s" % group_name), 200)
        else:
            return make_response(json.jsonify(message="'Documents' is default group name"), 401)

    elif request.method == "DELETE":
        group_id = complete_groups(g.db, parameters, "D_CLIENT_COMPLETED_GROUPS", "DELETE", url_group_id=str_group_id)
        if group_id != -1:
            return make_response(json.jsonify(message="Group %d is deleted." % group_id), 200)
        else:
            return make_response(json.jsonify(message="You cannot delete 'Documents' group"), 401)

@app.route('/api/user/requests/complete/groups/<str_group_id>', methods = ["POST", "GET"])
@exception_detector
@login_required
def client_completed_items_in_group(str_group_id):
    parameters = parse_request(request)

    if request.method == "POST":
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
        cursor = g.db.execute("SELECT * FROM V_REQUESTS WHERE client_user_id = ? AND client_completed_group_id = ? AND is_paid = 1 ORDER BY request_id DESC",
            [my_user_id, group_id])
        rs = cursor.fetchall()
        result = json_from_V_REQUESTS(g.db, rs, purpose="complete_client")
        return make_response(json.jsonify(data=result), 200)

@app.route('/api/user/requests/<str_request_id>/payment/start', methods = ["POST"])
@exception_detector
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
                client_id="Acoic-FJwf_Eiq6fkHC0NzHEnc0pBJ4ZHywiE_zXjQWtPXtrsLzQGfOaf0zAnYE30UmISe2KwIj4aWsy",
                client_secret="ECevFP6ONiBY3vpFcVYqxxAwtBqtau4X6x96JtLxbgzK45QAWQZFfgeoKSMp5HTKPfggtLfFiMkNY9vk"
                )

        # LIVE
        #paypalrestsdk.configure(
        #        mode="live",
        #        client_id="AaMMC_CcUAx4rM1NwvmJNVZf-I9xxZlyDNLmVtIxk8fqU-j-NAtqpePm7Jf6BXKzLDQuX-prHuCxxd6T",
        #        client_secret="EDKrvTx3Y42SVEJYxbih4NZ__rohsu-YDC7njq4x8-_6Fck_fdzJBRx_bh1rB0csSBUzisicO3P_mF7l"
        #        )

        logging.basicConfig(level=logging.INFO)
        logging.basicConfig(level=logging.ERROR)

        payment = paypalrestsdk.Payment({
          "intent": "sale",
          "payer": {
            "payment_method": "paypal"},
          "redirect_urls":{
            "return_url": "http://localhost:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=success&token=%s&pay_amt=%f" % (request_id, session.get('token'), amount),
            "cancel_url": "http://localhost:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=fail&token=%s&pay_amt=%f" % (request_id, session.get('token'), amount)},
          "transactions": [{
            "amount": {
            "total": amount,
            "currency": "USD",
            "details": {
              "subtotal": amount
            }},
          "description": "Ciceron translation request fee USD: %f" % amount }]})
        rs = payment.create()  # return True or False
        paypal_link = None
        for item in payment.links:
            if item['method'] == 'REDIRECT':
                paypal_link = item['href']
                break

        red_link = "/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=success&token=%s&pay_amt=%f" % (request_id, session.get('token'), amount)
        if bool(rs) is True:
            return make_response(json.jsonify(message="Redirect link is provided!", link=paypal_link, redirect_url=red_link), 200)
        else:
            return make_response(json.jsonify(message="Something wrong in paypal"), 400)

@app.route('/api/user/requests/<str_request_id>/payment/postprocess', methods = ["GET"])
@exception_detector
@login_required
def pay_for_request_process(str_request_id):
    request_id = int(str_request_id)
    pay_via = request.args['pay_via']
    is_success = True if request.args['status'] == "success" else False
    payment_id = request.args['paymentId']
    payer_id = request.args['PayerID']
    token = request.args['token']
    amount = float(request.args.get('pay_amt'))

    if pay_via == 'paypal':
        if token == session.get('token') and request_id == session.get('pending_reqeust') and is_success:
            session.pop('token')
            session.pop('pending_reqeust')

            payment_info_id = get_new_id(g.db, "PAYMENT_INFO")

            g.db.execute("UPDATE F_REQUESTS SET is_paid = ? WHERE id = ?", [True, request_id])

            # Paypal payment exeuction
            payment = paypalrestsdk.Payment.find(payment_id)
            payment.execute({"payer_id": payer_id})

            # Payment information update
            g.db.execute("INSERT PAYMENT_INFO (id, request_id, client_id, payed_via, order_no, pay_amount, payed_time) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)",
                    [payment_info_id, request_id, buffer(session['useremail']), buffer("paypal"), buffer(payment_id), amount])

            g.db.commit()
            #return redirect("success")
            return make_response("success", 200)

        elif token == session.get('token') and request_id == session.get('pending_reqeust') and not is_success:
            # REDIRECT TO FAIL PAGE
            # PAYMENT FAIL
            return redirect("page_provided_with /user/requests/%d/payment" % request_id)

        elif token != session.get('token') or request_id != session.get('pending_reqeust'):
            # REDIRECT TO WARNING PAGE
            # PLEASE DO NOT HACK!!!!!!!!!!!!!
            return redirect("do_not_hack")

@app.route('/api/user/device', methods = ["POST"])
@exception_detector
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
        g.db.execute("INSERT INTO D_MACHINES VALUES (?, ?, (SELECT id FROM D_MACHINE_OSS WHERE text = ?), ?)",
            [record_id, user_id, buffer(device_os), buffer(reg_key)])
    else:
        g.db.execute("UPDATE D_MACHINES SET reg_key = ? WHERE os_id = (SELECT id FROM D_MACHINE_OSS WHERE text = ?) AND user_id = ?",
            [buffer(reg_key), buffer(device_os), user_id])

    return make_response(json.jsonify(message="Succefully updated/inserted"), 200)

################################################################################
#########                        ADMIN TOOL                            #########
################################################################################

@app.route('/admin/publicize', methods = ["GET"])
@exception_detector
@admin_required
def publicize():
    cursor = g.db.execute("""SELECT count(*) FROM F_REQUESTS WHERE status_id = 1
                       AND expected_time is null AND submitted_time is null
                       AND CURRENT_TIMESTAMP-registered_time > (due_time-registered_time)/3 """)
    num_of_publicize = cursor.fetchall()[0][0]
    g.db.execute("""UPDATE F_REQUESTS SET ongoing_worker_id = null, status_id = 0
                     WHERE status_id = 1 AND expected_time is null AND submitted_time is null
                       AND CURRENT_TIMESTAMP-registered_time > (due_time-registered_time)/3 """)
    return make_response(json.jsonify(message="%d requests are publicized."%num_of_publicize), 200)

@app.route('/admin/language_assigner', methods = ["POST"])
@exception_detector
@admin_required
def language_assigner():
    parameters = parse_request(request)

    user_email = parameters['email']
    language_id = int(parameters['language'])
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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    
