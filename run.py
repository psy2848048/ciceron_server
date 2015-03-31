from flask import Flask, session, redirect, escape, request, g, abort, json, flash, make_response
from contextlib import closing
from datetime import datetime, timedelta
import hashlib, sqlite3, os, time, requests
from functools import wraps
from werkzeug import secure_filename
from decimal import Decimal
from ciceron_lib import *

DATABASE = '../db/ciceron.db'
DEBUG = True
IDENTIFIER = "millionare@ciceron!@"
UPLOAD_FOLDER_PROFILE_PIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","profile_pic")
UPLOAD_FOLDER_REQUEST_PIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "request_pic")
UPLOAD_FOLDER_REQUEST_SOUND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sounds")
UPLOAD_FOLDER_REQUEST_DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "request_doc")
UPLOAD_FOLDER_REQUEST_TEXT =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "request_text")

ALLOWED_EXTENSIONS_PIC = set(['jpg', 'jpeg', 'gif', 'png', 'tiff'])
ALLOWED_EXTENSIONS_DOC = set(['doc', 'hwp', 'docx', 'pdf', 'ppt', 'pptx', 'rtf'])
ALLOWED_EXTENSIONS_WAV = set(['wav', 'mp3', 'aac', 'ogg', 'oga', 'flac', '3gp', 'm4a'])
VERSION= "2014.12.28"

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'AIzaSyDsuwrNC0owqpm6eznw6mUexFt18rBcq88'
app.project_number = 1021873337108

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

@app.route('/')
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
            , 200)

@app.route('/login', methods=['POST', 'GET'])
@exception_detector
def login():
    if request.method == "POST":
        # Parameter
        #     email:        E-mail ID
        #     password:     password
        #     client_os:    := Android, iPhone, Blackberry, web.. (OPTIONAL)
        #     machine_id:   machine_id of client phone device (OPTIONAL)

        # Get parameters
        email = request.form['email']
        hashed_password = get_hashed_password(
                request.form['password'],
                app.config['IDENTIFIER'])
        machine_id = request.form.get('machine_id', None)
        client_os = request.form.get('client_os', None)
        user_id = get_user_id(g.db, email)

        # Get hashed_password using user_id for comparing
        cursor = g.db.execute("SELECT hashed_pass FROM PASSWORDS where user_id = ?",
                [user_id])
        rs = cursor.fetchall()

        if len(rs) > 1:
            # Status code 500 (ERROR)
            # Description: Same e-mail address tried to be inserted into DB
            return make_response ('Constraint violation error!', 500)

        elif len(rs) == 0:
            # Status code 403 (ERROR)
            # Description: Not registered
            return make_response ('Not registered %s' % email, 403)
        
        elif len(rs) == 1 and str(rs[0][0]) == str(hashed_password):
            # Status code 200 (OK)
            # Description: Success to log in
            session['logged_in'] = True
            session['useremail'] = email
        
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
        return '''
        <!doctype html>
        <title>LogIn test</title>
        <h1>Login</h1>
        <form action="" method="post">
      <p>ID: <input type=text name="email"></p>
      <p>Password: <input type=password name="password"></p>
          <p><input type=submit value=login></p>
        </form>
        '''

@app.route('/logout')
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
        # Status code 406 (ERROR)
        # Description: Not logged in yet
        return make_response(json.jsonify(
                   message = "You've never logged in"
               ), 406)

@app.route('/signup', methods=['POST', 'GET'])
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
        email = request.form['email']
        hashed_password = get_hashed_password(
            request.form['password'],
            app.config['IDENTIFIER'])
        facebook_id = request.form.get('facebook_id', None)
        name = request.form['name']
        mother_language_id = request.form['mother_language_id']
        #registration_id = request.form.get('registration_id', None)
        #client_os = request.form.get('client_os', None)

        # Insert values to D_USERS
        user_id = get_new_id(g.db, "D_USERS")

        print "New user id: %d" % user_id
        g.db.execute("INSERT INTO D_USERS VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
                 None,
                 buffer("")])

        g.db.execute("INSERT INTO PASSWORDS VALUES (?,?)",
            [user_id, buffer(hashed_password)])
        g.db.execute("INSERT INTO REVENUE VALUES (?,?)",
            [user_id, 0])
        client_completed_group_id = get_new_id(g.db, "D_CLIENT_COMPLETED_GROUPS")
        g.db.execute("INSERT INTO D_CLIENT_COMPLETED_GROUPS VALUES (?,?,?)",
                [client_completed_group_id, user_id, buffer("All")])

        g.db.commit() 

        # Status code 200 (OK)
        # Description: Signed up successfully
        return make_response(json.jsonify(status=dict(message="Registration %s: successful" % email)), 200)
    
    return '''
        <!doctype html>
        <title>Sign up</title>
        <h1>Sign up</h1>
        <form action="" method="post">
      <p>ID: <input type=text name="username"></p>
      <p>Pass: <input type=password name="password"></p>
      <p>Nickname: <input type=text name="nickname"></p>
      <p>Mother language setting: <input type=text name="mother_language"></p>
          <p><input type=submit value="Sign up!"></p>
        </form>
        '''

@app.route('/idCheck', methods=['GET'])
@exception_detector
def idChecker():
    # Method: GET
    # Parameter: String id
    email = request.args['email']
    print "email_id: %s" % email
    cursor = g.db.execute("select id from D_USERS where email = ?", [buffer(email)])
    check_data = cursor.fetchall()
    if len(check_data) == 0:
        # Status code 200 (OK)
        # Description: Inputted e-mail ID is available
        return make_response(json.jsonify(
            message="You may use the id %s" % email), 200)
    else:
        # Status code 406 (OK)
        # Description: Inputted e-mail ID is duplicated with other's one
        return make_response(json.jsonify(
            message="Duplicated ID '%s'" % email), 406)

@app.route('/user/profile', methods = ['GET', 'POST'])
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
            user_isTranslator=              userinfo[0][4],
            user_profileText=               str(userinfo[0][15])
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
        profileText = request.form.get('user_profileText', None)

        # Start logic
        # Get user number
        email = session['useremail']

        if profileText is not None:
            g.db.execute("UPDATE D_USERS SET profile_text = ? WHERE email = ?",
                    [buffer(profileText), buffer(email)])
            g.db.commit()

        return make_response(json.jsonify(
            message="Your profile is susccessfully updated!"), 200)

@app.route('/user/profile/photo', methods=["POST", "GET"])
@exception_detector
@login_required
def user_profile_photo():
    if request.method == "POST":
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

@app.route('/requests', methods=["GET", "POST"])
@exception_detector
def requests():
    if request.method == "GET":
        # Request method: GET
        # Parameters
        #     since(optional): Timestamp, take recent 20 post before the timestamp.
        #                  If this parameter is not provided, recent 20 posts from now are returned
        
        query = "SELECT * FROM V_REQUESTS WHERE ongoing_worker_id is null AND status_id in (0,1) AND is_request_finished = 0 "
        if 'since' in request.args.keys():
            condition.append("AND registered_time < datetime(%f) " % Decimal(request.args['since']))
        query += "ORDER BY registered_time DESC LIMIT 20"

        cursor = g.db.execute(query)
        rs = cursor.fetchall()
        result = []

        for row in rs:
            # For fetching translators in queue
            queue_id = row[23]
            cursor2 = g.db.execute("SELECT * FROM V_QUEUE_LISTS WHERE id = ? ORDER BY user_id",
                    [queue_id])

            queue_list = []
            for q_item in cursor2.fetchall():
                temp_item=dict(
                        id=      q_item[2],
                        name=    q_item[4],
                        picPath= q_item[5]
                        )
                queue_list.append(temp_item)

            # For getting word count of the request
            cursor2 = g.db.execute("SELECT path FROM id = ?" [row[28]])
            list_txt = cursor2.fetchall()
            if len(list_txt[0]) == 0:
                num_of_words = None
            else:
                num_of_words = word_counter(list_txt[0][0])

            # For getting context text

            item = dict(
                    request_id=row[0],
                    request_clientId=row[2],
                    request_clientName=row[3],
                    request_clientPicPath=row[4],
                    request_originalLang=row[13],
                    request_targetLang=row[15],
                    request_isSos=row[17],
                    request_format=row[19],
                    request_subject=row[21],
                    request_translatorsInQueue=queue_list,
                    request_isTransOngoing=row[18],
                    request_ongoingWorkerId=row[6],
                    request_ongoingWorkerName=row[7],
                    request_ongoingWorkerPicPath=row[8],
                    request_registeredTime=row[24],
                    request_isText=row[27],
                    request_isPhoto=row[29],
                    request_isSound=row[31],
                    request_isFile=row[33],
                    reqeust_words=num_of_words,
                    request_dueTime=row[25],
                    request_points=row[26],
                    request_text=row[36]
                )
            result.append(item)

        return make_response(json.jsonify(result), 200)

    elif request.method == "POST":
        request_id = get_new_id(g.db, "F_REQUESTS")
        client_user_id = get_user_id(g.db, request.form['request_clientId'])
        original_lang_id = request.form['request_originalLang']
        target_lang_id = request.form['request_targetLang']
        isSos = request.form['request_isSos']
        format_id = request.form.get('request_format')
        subject_id = request.form.get('request_subject')
        registered_time = request.form['request_registeredTime']
        is_text = request.form.get('request_isText')
        text_string = request.form.get('request_text')
        is_photo = request.form.get('request_isPhoto')
        #photo_binary
        is_sound = request.form.get('request_isSound')
        #sound_binary
        is_file = request.form.get('request_isFile')
        #file_binary
        words = request.form.get('reqeust_words')
        due_time = request.form['request_dueTime']
        point = request.form.get('request_points')
        context = request.form.get('request_context')

        new_photo_id = None
        new_sound_id = None
        new_file_id = None
        new_text_id = None

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
            filename = str(datetime.now()) + ".txt"
            path = os.path.join(app.config['UPLOAD_FOLDER_REQUEST_TEXT'], filename)
            f = open(path, 'w')
            f.write(text_string)
            f.close()

            new_text_id = get_new_id(g.db, "D_REQUEST_TEXTS")
            g.db.execute("INSERT INTO D_REQUEST_TEXTS VALUES (?,?)",
                    [new_text_id, buffer(path)])

        # Input context text into dimension table
        new_context_id = get_new_id(g.db, "D_CONTEXTS")
        g.db.exeucte("INSERT INTO D_CONTEXTS VALUES (?,?)",
                [new_context_id, buffer(context)])

        g.db.execute("INSERT INTO F_REQUESTS VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                   [request_id,           # id
                    client_user_id,       # client_user_id
                    original_lang_id,     # original_lang_id
                    target_lang_id,       # target_lang_id
                    isSos,                # isSOS
                    0,                    # status_id
                    format_id,            # format_id
                    subject_id,           # subject_id
                    None,                 # queue_id
                    None,                 # ongoing_worker_id
                    is_text,              # is_text
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
                    None])                # tone_id

        g.db.commit()

        return make_response(json.jsonify(
            message="Request ID %d  has been posted by %s" % (request_id, email)
            ), 200)

@app.route('/charge', methods = ["GET", "POST"])
@exception_detector
@login_required
def charge():
    if request.method == "POST":
    # Method: POST
        # Parameters
    #     username: e-mail ID
    #     password: password
    #     point: charged point in USD
        user_id = request.form['username']
    # Check credential again. Because, this step is related real money.
    if user_id != session['username']:
            # Status code 406 (ERROR)
        # Description: Signed-in ID and inputted ID are different each other
        return make_response(json.jsonify(status=406, message="Suspicious user tried to access your account!"), 406)
        password = request.form['password']
        point = request.form['point']

    hash_maker = hashlib.md5()
    hash_maker.update(app.config['IDENTIFIER'])
    hash_maker.update(password)
    hash_maker.update(app.config['IDENTIFIER'])
    hashed_password = hash_maker.digest()
        
    cursor = g.db.execute("SELECT string_id, password_hashed FROM Users where string_id = ?", [buffer(user_id)])

    rs = cursor.fetchall()
    if len(rs) == 0:
        # Status code 406 (ERROR)
        # Description: User is not registered with inputted ID (Dummy part but double check)
        return make_response(json.jsonify(status=406, message="Not registered with the ID %s" % session['username']), 406)

    elif str(rs[0][1]) != str(hashed_password):
        # Status code 406 (ERROR)
        # Description: Incorrect password
        return make_response(json.jsonify(status=406, message="Check password"), 406)

        id_hashed = hashed_id_maker(g.db)
        query_update_point = "UPDATE Property SET amount = amount + ? WHERE id = ?"
        g.db.execute(query_update_point, [point, buffer(id_hashed)])

        g.db.commit()
        # Status code 200 (OK)
        # Description: Point is charged successfully
        return make_response(json.jsonify(status=200, message="Charged USD %f to %s" % (float(point), user_id)), 200)

    elif request.method == "GET":
    # Method: GET
    # Show HTML input form for POSTing easily
        return '''
            <!doctype html>
        <title>Charging</title>
        <h1>Charge point for ''' + session['username'] +  '''</h1>
        <form action="" method=post>
        <p>Point: <input type=text name=point></p>
        <p>ID: <input type=text name=username></p>
        <p>Password: <input type=password name=password></p>
        <p><input type=submit value=Charge>
        </form>
        '''

@app.route('/history_requester', methods=["GET"])
@login_required
@exception_detector
def history_requester():
    # Request method: GET
    # Parameters
    #     last_post_time(optional): Timestamp, take recent 20 post before the timestamp.
    #                               If this parameter is not provided, recent 20 posts from now are returned
    #     filter: Show user's order with the status following- Pending, in progress, completed
    #query = "SELECT is_SOS, id, requestor_id, from_lang, to_lang, main_text, request_date, translator_id, is_request_picked, is_request_finished FROM Requests_list WHERE (requestor_id = ? OR translator_id = ?) AND translator_id IS NOT NULL "
    query = "SELECT * FROM Requests_list WHERE requester_id = ? "

    condition =[]
    if 'last_post_time' in request.args.keys():
        condition.append("request_date < datetime(%f) " % Decimal(request.args['last_post_time']))

    if 'filter' in request.args.keys():
        if request.args['filter'] == 'pending':
            condition.append("is_request_picked = 0")
        elif request.args['filter'] == 'in_progress':
            condition.append("is_request_picked = 1 AND is_request_finished = 0")
        elif request.args['filter'] == 'completed':
            condition.append("is request_picked = 1 AND is_request_finished = 1")

    for item in condition:
        query += " AND " + item

    query += " ORDER BY request_date DESC LIMIT 20"
    print query

    cursor = g.db.execute(query, [session['username']])
    rs = cursor.fetchall()
    result = []

    for row in rs:
        item = dict()
        item['id'] = int(row[0])
        item['requester_id'] = str(row[1])
        item['from_lang'] = row[2]
        item['to_lang'] = row[3]
        item['is_SOS'] = bool(int(row[4]))
        item['main_text'] = str(row[5])
        item['context_text'] = str(row[6])
        item['image_files'] = str(row[7])
        item['sound_file'] = str(row[8])
        item['request_date'] = row[9]
        item['format'] = str(row[10])
        item['subject'] = str(row[11])
        item['due_date'] = str(row[12])
        item['translator_id'] = str(row[13])
        item['is_request_picked'] = bool(int(row[14]))
        item['is_request_finished'] = bool(int(row[15]))
        item['price'] = float(row[16])
        result.append(item)

    # Status code 200 (OK)
    # Description: Give JSON data to client machine
    return make_response(json.jsonify(item_list = result), 200)

@app.route('/history_translator', methods=["GET"])
@login_required
@exception_detector
def history_translator():
    # Request method: GET
    # Parameters
    #     last_post_time(optional): Timestamp, take recent 20 post before the timestamp.
    #                               If this parameter is not provided, recent 20 posts from now are returned
    #     filter: Show user's order with the status following- Pending, in progress, completed
    #query = "SELECT is_SOS, id, requestor_id, from_lang, to_lang, main_text, request_date, translator_id, is_request_picked, is_request_finished FROM Requests_list WHERE (requestor_id = ? OR translator_id = ?) AND translator_id IS NOT NULL "
    query = "SELECT * FROM Requests_list WHERE translator_id = ? "

    condition =[]
    if 'last_post_time' in request.args.keys():
        condition.append("request_date < datetime(%f) " % Decimal(request.args['last_post_time']))
    if 'filter' in request.args.keys():
        if request.args['filter'] == 'pending':
            condition.append("is_request_picked = 0")
        elif request.args['filter'] == 'in_progress':
            condition.append("is_request_picked = 1 AND is_request_finished = 0")
        elif request.args['filter'] == 'completed':
            condition.append("is request_picked = 1 AND is_request_finished = 1")

    for item in condition:
        query += " AND " + item

    query += " ORDER BY request_date DESC LIMIT 20"
    print query

    cursor = g.db.execute(query, [session['username']])
    rs = cursor.fetchall()
    result = []

    for row in rs:
        item = dict()
        item['id'] = int(row[0])
        item['requester_id'] = str(row[1])
        item['from_lang'] = row[2]
        item['to_lang'] = row[3]
        item['is_SOS'] = bool(int(row[4]))
        item['main_text'] = str(row[5])
        item['context_text'] = str(row[6])
        item['image_files'] = str(row[7])
        item['sound_file'] = str(row[8])
        item['request_date'] = row[9]
        item['format'] = str(row[10])
        item['subject'] = str(row[11])
        item['due_date'] = str(row[12])
        item['translator_id'] = str(row[13])
        item['is_request_picked'] = bool(int(row[14]))
        item['is_request_finished'] = bool(int(row[15]))
        item['price'] = float(row[16])
        result.append(item)

    # Status code 200 (OK)
    # Description: Give JSON data to client machine
    return make_response(json.jsonify(item_list = result), 200)

@app.route('/pick_request/<post_id>', methods=['GET'])
@login_required
@exception_detector
def pick_request(post_id):
    # Request method: GET
    # Parameters
    #    post_id: requested post id

    # Find requester ID using requested post ID number
    query_validation = "SELECT requester_id FROM Requests_list WHERE id = ?"
    cursor = g.db.execute(query_validation, [post_id])
    requester_id = cursor.fetchall()[0][0]

    # Blocking abusing:
    #   Check whether requester tries to translate his/hers or not.
    if session['username'] == requester_id:
        return make_response(json.jsonify(code=406, message="You cannot translate your request"), 406)

    # For checking the translator's ability, the language ability data should be parsed and organize into list structure.
    # DB data:
    #     mother_tongue_language = Korean
    #     other_language = English;Chinese;Hrvatska
    #                      (Each language could be deliminated by ';')
    #
    # Parsed data:
    #     translator_language_list = [Korean, English, Chinese, Hrvatska]

    query_check_user_language = "SELECT mother_tongue_language, other_language FROM Users WHERE string_id = ?"
    cursor = g.db.execute(query_check_user_language, [buffer(session['username'])])
    temp_lang = cursor.fetchall()[0]
    translator_language_list = []
    translator_language_list.append(temp_lang[0])
    if temp_lang[1] is not None:
        for lang_item in temp_lang[1].split(';'):
            if temp_lang is not None:
                translator_language_list.append(lang_item)
        else:
                pass

    # Translator should use origin and target language, both of them
    #     if both of Korean and English are in [Korean, Enlish, Chinese, Hrvatska] (O) -> Give the work to the translator
    #     if both of Korean and English are in [Chinese, English, Hrvatska, Suomi] (X) -> Block
    query_check_item_language = "SELECT from_lang, to_lang FROM Requests_list WHERE id = ?"
    cursor = g.db.execute(query_check_item_language, [int(post_id)])
    request_lang = cursor.fetchall()[0]
    if not (request_lang[0] in translator_language_list and request_lang[1] in translator_language_list):
        return make_response(json.jsonify(code=401, message="According to your language ability, you cannot translate this request.\nIf you want to request, please register as a translator!"), 401)

    # If translatable, give the work to the translator.
    # "is_request_picked=1" means that the work is given to translator
    # Also mark in "translator_id" column
    query_information = "UPDATE Requests_list SET translator_id = ?, is_request_picked = 1 WHERE id = ?"
    g.db.execute(query_information, [buffer(session['username']), int(post_id)])
    g.db.commit()

    return make_response("Post %d is picked by %s" % (int(post_id), session['username']), 200)

@app.route('/add_language', methods=["POST"])
@login_required
@exception_detector
def add_langaugae():
    # Method: POST
    # Parametes
    #     language: Insert one language into "other_language" colunm in DB

    # Gather current language ability except mother language
    query_load_current_language_status = "SELECT other_language FROM Users WHERE string_id = ?"
    cursor = g.db.execute(query_load_current_language_status, [ buffer(session['username']) ])

    current_language_list = cursor.fetchall()[0][0]
    current_language = None
    if current_language_list is not None:
        current_language = current_language_list[0][0]
        current_language += (';' + request.form['language'])
    else:
        current_language = request.form['language']

    # Replace data into updated one
    query_add_language = "UPDATE Users SET other_language = ? WHERE string_id = ?"
    g.db.execute(query_add_language, [ current_language, buffer(session['username'])  ])

    g.db.commit()

    # Status code 200 (OK)
    # Description: Another language ability is added successfully
    return make_response(json.jsonify(status=200, message="%s is added for user %s as his/her language ability" % (request.form['language'], session['username'])), 200)

@app.route('/comment/<request_id>', methods=["GET", "POST"])
@login_required
@exception_detector
def comment(request_id):
    if request.method == "POST":
    # Method: POST
    # Parameter
    #     comment_text: String text
    #     is_result: Don't think about that now

        # Check commenter's position, requester or translator
        query_distinguish_requester = "SELECT requester_id, translator_id FROM Requests_list WHERE id = ?"
        cursor = g.db.execute(query_distinguish_requester, [request_id])
        result_distinguish_requester = cursor.fetchall()

        is_requester = None
        if len(result_distinguish_requester) == 0:
            # Status code 406
            # Description: The user does not belong to requester nor translator.
            return make_response(json.jsonify(status=406, message="This request id DOES NOT exist. Please check the DB"), 406)

        elif str(result_distinguish_requester[0][0]) == str(session['username']):
            is_requester = True
        elif str(result_distinguish_requester[0][1]) == str(session['username']):
            is_requester = False

        # Check last reply number
        # The new comment shoulbe be posted as (last comment id number + 1)
        query_check_reply_id = "SELECT reply_id FROM Result WHERE request_id = ? ORDER BY reply_id DESC LIMIT 1"
        cursor = g.db.execute(query_check_reply_id, [request_id])
        result_check_reply_id = cursor.fetchall()

        reply_counter = 0
        if len(result_check_reply_id) == 0:
            reply_counter = 1
        else:
            reply_counter = result_check_reply_id[0][0] + 1

            query = "INSERT INTO Result VALUES(?,?,?,?,?,?)"

            item=dict()
            item['request_id'] = request_id
            item['reply_id'] = reply_counter
            item['is_requester'] = is_requester
            item['post_time'] = datetime.now()
            item['comment_text'] = request.form['comment_text']
            item['is_result'] = int(request.form['is_result']) # Might be userless column

            # Insert data into DB
            g.db.execute(query, [
                item['request_id'],
                item['reply_id'],
                      item['is_requester'],
            item['post_time'],
                item['comment_text'],
                item['is_result']
                ])

        g.db.commit()

        # Status code 200 (OK)
        # Description: Comment is posted successfully
        return make_response(
                json.jsonify(
                    status=200, 
                    message="Comment %d is posted in post id %d" % (int(item['reply_id']), int(item['request_id']) )
                    ), 
                200)

    elif request.method == "GET":
    # Method: GET
    # No additional parameters

        query_comment_list = "SELECT * FROM Result WHERE request_id = ? ORDER BY reply_id"
        cursor = g.db.execute(query_comment_list, [request_id])

        result_comment_list = []

        for row in cursor.fetchall():
            item = dict()
            item['request_id'] = row[0]
            item['reply_id'] = row[1]
            item['is_requester'] = bool(row[2])
            item['post_time'] = row[3]
            item['comment_text'] = row[4]
            item['is_result'] = bool(row[5]) # Might be useless column

            result_comment_list.append(item)

            # Status code 200 (OK)
            # Description: Provide all comments data of given request post
        return make_response(json.jsonify(result=result_comment_list), 200)

@app.route('/accept/<request_id>', methods = ["GET"])
@login_required
@exception_detector
def accept(request_id):
    # Method: GET
    # No additional parameters

    # Check post, requester ID, and post status
    query_request_checker = "SELECT requester_id, is_request_picked, is_request_finished, is_SOS, price, translator_id FROM Requests_list WHERE id = ?"
    cursor = g.db.execute(query_request_checker, [request_id])
    result = cursor.fetchall()

    if len(result) == 0:
    # Status code 406 (ERROR)
    # Description: No post exist with given post ID number
        return make_response(json.jsonify(status=404, message="No post exists with id %d" % int(request_id)), 404)

    elif not (str(result[0][0]) == str(session['username']) and bool(result[0][1]) == True and bool(result[0][2]) == False):
    # Status code 406 (ERROR)
    # Description: Post exists but current user is not belonged to requester. Only requester has authority to close request post.
    #              Even translator cannot close the request.
        return make_response(json.jsonify(status=406, message="No authority of accepting the translation result and closing the post %d" % int(request_id)), 406)
    else:
    # Mark the post as finished post
        query_closing_request = "UPDATE Requests_list SET is_request_finished = 1 WHERE id = ?"
        g.db.execute(query_closing_request, [request_id])

        # Apply translated record
        # Give point to tranlator
        query_update_userinfo = "UPDATE Users SET %s = %s + 1 WHERE string_id = ?"
        if result[0][3] == True:
            g.db.execute(query_update_userinfo % ("translated_SOS", "requested_normal"), [result[0][5]])
        else:
            g.db.execute(query_update_userinfo % ("translated_normal", "requested_normal"), [result[0][5]])
            g.db.execute("UPDATE Property SET amount = amount + ? WHERE id = ?", [result[0][4], buffer(hashed_other_id_maker(g.db, result[0][5]))])

        g.db.commit()
        return make_response(json.jsonify(status=200, message="Post %d has just closed" % int(request_id)), 200)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
