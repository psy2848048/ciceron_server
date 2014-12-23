from flask import Flask, session, redirect, escape, request, g, abort, json, flash, make_response
from contextlib import closing
from datetime import datetime, timedelta
import hashlib, sqlite3, os, time
from functools import wraps
from werkzeug import secure_filename
from decimal import Decimal

DATABASE = 'ciceron.db'
DEBUG = True
IDENTIFIER = "millionare@ciceron!@"
UPLOAD_FOLDER_PROFILE_PIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile_pic")
UPLOAD_FOLDER_REQUEST_PIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "request_pic")
UPLOAD_FOLDER_REQUEST_SOUND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
UPLOAD_FOLDER_REQUEST_DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "request_doc")
ALLOWED_EXTENSIONS_PIC = set(['jpg', 'jpeg', 'gif', 'png', 'tiff'])
ALLOWED_EXTENSIONS_DOC = set(['doc', 'hwp', 'docx', 'pdf', 'ppt', 'pptx', 'rtf'])
ALLOWED_EXTENSIONS_WAV = set(['wav', 'mp3', 'aac', 'ogg', 'oga', 'flac', '3gp', 'm4a'])
VERSION= "2014.12.28"

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        else:
    	    return make_response(json.jsonify(
                       status_code = 401,
    	               message = "Login required"
	           ), 401)
    return decorated_function

def exception_detector(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print e
	    g.db.rollback()
	    return make_response(json.jsonify(
                       status_code = 400,
    	               message = "Abnormal DB connection"
	           ), 400)
    return decorated_function

def pic_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_PIC']

def doc_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS_DOC']

def hashed_id_maker(conn):
    cursor = conn.execute( "SELECT password_hashed FROM Users WHERE string_id = ?", [buffer(session['username'])])
    password_hashed = cursor.fetchall()[0][0]

    hash_maker = hashlib.md5()

    hash_maker.update(app.config['VERSION'])
    hash_maker.update(session['username'])
    hash_maker.update(password_hashed)
    hash_maker.update(app.config['VERSION'])
    hashed_ID = hash_maker.digest()

    return hashed_ID

def hashed_other_id_maker(conn, string_id):
    cursor = conn.execute( "SELECT password_hashed FROM Users WHERE string_id = ?", [buffer(string_id)])
    password_hashed = cursor.fetchall()[0][0]

    hash_maker = hashlib.md5()

    hash_maker.update(app.config['VERSION'])
    hash_maker.update(string_id)
    hash_maker.update(password_hashed)
    hash_maker.update(app.config['VERSION'])
    hashed_ID = hash_maker.digest()

    return hashed_ID

@app.route('/')
@exception_detector
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in'

@app.route('/login_email', methods=['POST', 'GET'])
@exception_detector
def login_email():
    if request.method == "POST":
	# Parameter
        #     username: E-mail ID
        #     password: password
        username = request.form['username']
	hash_maker = hashlib.md5()
	hash_maker.update(app.config['IDENTIFIER'])
	hash_maker.update(request.form['password'])
	hash_maker.update(app.config['IDENTIFIER'])
	hashed_password = hash_maker.digest()
        
        cursor = g.db.execute("SELECT string_id, password_hashed FROM Users where string_id = ?", [buffer(username)])

	rs = cursor.fetchall()
	if len(rs) > 1:
	    # Status code 406 (ERROR)
            # Description: Same e-mail address tried to be inserted into DB
	    return make_response ('Constraint violation error!', 406)

        elif len(rs) == 0:
	    # Status code 406 (ERROR)
            # Description: Not registered
	    return make_response ('Not registered %s' % username, 406)

	if str(rs[0][1]) == str(hashed_password):
	    # Status code 200 (OK)
	    # Description: Success to log in
	    session['logged_in'] = True
	    session['username'] = username
	    return make_response('You\'re logged with user %s' % username, 200)
	else:
	    # Status code 406 (ERROR)
	    # Description: Password incorrect
	    print "Current pass: %s" % rs[0][1]
	    print "Input pass: %s" % hashed_password
	    return make_response('Please check the password', 406)
	return
    else:
        return '''
        <!doctype html>
        <title>LogIn test</title>
        <h1>Login</h1>
        <form action="" method="post">
	  <p>ID: <input type=text name="username"></p>
	  <p>Password: <input type=password name="password"></p>
          <p><input type=submit value=login></p>
        </form>
        '''

@app.route('/logout')
@exception_detector
def logout():
    # No parameter needed
    if session['logged_in'] == True:
	username_temp = session['username']
        session.pop('logged_in', None)
	session.pop('username', None)
	# Status code 200 (OK)
        # Logout success
        return make_response(json.jsonify(
                   status_code = 200,
                   message = "User %s is logged out" % username_temp
               ), 200)
    else:
	# Status code 406 (ERROR)
	# Description: Not logged in yet
        return make_response(json.jsonify(
                   status_code = 406,
                   message = "You've never logged in"
               ), 406)
        

@app.route('/signUp_email', methods=['POST', 'GET'])
@exception_detector
def sign_up_email():
    # Request method: POST
    # Parameters
    #     username: String, email ID ex) psy2848048@gmail.com
    #     password: String, password
    #     nickname: String, this name will be used and appeared in Ciceron system
    #     mother_language: String, 1st language of user
    if request.method == 'POST':
        username = request.form['username']

        hash_maker = hashlib.md5()
        hash_maker.update(app.config['IDENTIFIER'])
        hash_maker.update(request.form['password'])
        hash_maker.update(app.config['IDENTIFIER'])
        hashed_password = hash_maker.digest()

        nickname = request.form['nickname']
        mother_language = request.form['mother_language']

        g.db.execute("INSERT INTO Users VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", 
      		        [buffer(username), buffer(hashed_password), buffer(nickname), None, buffer(mother_language), None, 1, 0, 0, False, 0, 0, False, False])

	hash_maker = hashlib.md5()
        hash_maker.update(app.config['VERSION'])
	hash_maker.update(request.form['username'])
	hash_maker.update(hashed_password)
	hash_maker.update(app.config['VERSION'])
	hashed_ID = hash_maker.digest()
	g.db.execute("INSERT INTO Property VALUES (?,0)", [buffer(hashed_ID)])

        g.db.commit() 

        # Status code 200 (OK)
	# Description: Signed up successfully
        return make_response(json.jsonify(status=dict(code=200, message="Registration %s: successful" % username)), 200)
    
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

@app.route('/nickCheck', methods=['GET'])
@exception_detector
def nickChecker():
    # Method: GET
    # Parameter: String, nickname
    nickname = request.args['nickname']
    print "nick: %s" % nickname
    cursor = g.db.execute("select * from Users where nickname = ?", [buffer(nickname)])
    check_data = cursor.fetchall()
    if len(check_data) == 0:
	# Status code 200 (OK)
	# Description: Inputted nickname is avaiable
        return make_response(json.jsonify(status=dict(code=200, message="You may use the nick %s" % nickname)), 200)
    else:
	# Status code 406
	# Description: Inputted nickname is duplicated with other's one
	return make_response(json.jsonify(status=dict(code=406, message="Duplicated nick %s" % nickname)), 406)

@app.route('/idCheck', methods=['GET'])
@exception_detector
def idChecker():
    # Method: GET
    # Parameter: String id
    email_id = request.args['email_id']
    print "email_id: %s" % email_id
    cursor = g.db.execute("select * from Users where string_id = ?", [buffer(email_id)])
    check_data = cursor.fetchall()
    if len(check_data) == 0:
	# Status code 200 (OK)
	# Description: Inputted e-mail ID is available
        return make_response(json.jsonify(status=dict(code=200, message="You may use the id %s" % email_id)), 200)
    else:
	# Status code 406 (OK)
	# Description: Inputted e-mail ID is duplicated with other's one
	return make_response(json.jsonify(status=dict(code=406, message="Duplicated nick %s" % email_id)), 406)

@app.route('/update_profile_pic', methods=["GET", "POST"])
@exception_detector
@login_required
def update_profile_pic():
    # IN CONSTRUCTION
    profile_pic = request.files['file']
    filename = ""
    if profile_pic and pic_allowed_file(profile_pic.filename):
        filename = secure_filename(profile_pic.filename)
        profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER_PROFILE_PIC'], filename))

	g.db.execute("UPDATE Users SET profile_img = ? WHERE string_id = ?", [buffer(filename), buffer(session['username'])])
	return make_response(json.jsonify(status=200, message="Upload complete", path=os.path.join(app.config['UPLOAD_FOLDER_PROFILE_PIC'], filename)), 200)

    return '''
        <!doctype html>
        <title>Upload test / Profile pic</title>
        <h1>Upload new File</h1>
        <form action="" method=post enctype=multipart/form-data>
          <p><input type=file name=file>
             <input type=submit value=Upload>
        </form>
        '''

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

@app.route('/post_list', methods=["GET"])
@exception_detector
def post_list():
    # Request method: GET
    # Parameters
    #     last_post_time(optional): Timestamp, take recent 20 post before the timestamp.
    #                               If this parameter is not provided, recent 20 posts from now are returned
    if request.method == "GET":
        query = "SELECT is_SOS, id, requester_id, from_lang, to_lang, main_text, request_date, format, subject, due_date, image_files, sound_file, price FROM Requests_list WHERE is_request_picked = 0 AND is_request_finished = 0 "
        #query = "SELECT is_SOS, id, requester_id, from_lang, to_lang, main_text, request_date, format, subject, due_date, image_files, sound_file, price FROM Requests_list "
        if 'last_post_time' in request.args.keys():
            condition.append("AND request_date < datetime(%f) " % Decimal(request.args['last_post_time']))
        query += "ORDER BY request_date DESC LIMIT 20"

        cursor = g.db.execute(query)
        rs = cursor.fetchall()
        result = []

        for row in rs:
            item = dict()
	    item['is_SOS'] = bool(row[0])
	    item['id'] = row[1]
	    item['requester_id'] = row[2]
            cursor = g.db.execute("SELECT profile_img, grade FROM Users WHERE string_id = ?", [ buffer(item['requester_id']) ])
	    rs = cursor.fetchall()
	    item['requester_pic'] = rs[0][0]
	    item['requester_grade'] = rs[0][1]

	    item['from_lang'] = row[3]
	    item['to_lang'] = row[4]
	    item['main_text'] = row[5]
	    item['request_date'] = row[6]
	    item['format'] = row[7]
	    item['subject'] = row[8]
	    item['due_date'] = row[9]
	    item['is_image'] = True if row[10] is not None else False
	    item['is_sound'] = True if row[11] is not None else False
	    item['price'] = row[12]

	    result.append(item)

        # Status code 200 (OK)
	# Description: Listing up 20 requested items which is not picked by translator and is not closed.
        #              Recent 20 items if time parameter is not given
	#              Recent 20 times from the given time if time parameter is given
        return make_response(json.jsonify(item_list = result), 200)

@app.route('/post', methods=["POST"])
@exception_detector
@login_required
def post():
    # Request method: POST
    # Parameter
    #     from_lang: String, language of origin text
    #     to_lang: String, target language
    #     is_SOS: Bool, True(1) - SOS request, False(0) - Normal request
    #     main_text: Text, origin text
    #     context_text: Text, context text
    #     image_files: image file name list will be given if user requested with photo files
    #     sound_file: sound file name will be biven if user requested with sound file
    #     format: request format of this post
    #     subject: request subject of this post
    if request.method == "POST":
        query_for_get_last_id = "SELECT id from Requests_list ORDER BY id DESC LIMIT 1"
	cursor = g.db.execute(query_for_get_last_id)
	count_data = cursor.fetchall()

	start_count = 0
	if len(count_data) == 0:
            start_count = 1
	else:
            start_count = int(count_data[0][0]) + 1 # [0]? or [0][0]

	post = dict()
	post['id'] = start_count
	post['requester_id'] = session['username']
	post['from_lang'] = request.form['from_lang']
	post['to_lang'] = request.form['to_lang']
	post['is_SOS'] = int(request.form['is_SOS'])
	post['main_text'] = request.form['main_text']
	post['context_text'] = request.form.get('context_text', None)
	post['image_files'] = request.form.get('image_files', None)
	post['sound_file'] = request.form.get('sound_file', None)
	post['request_date'] = datetime.now()
	post['format'] = request.form['format']
	post['subject'] = request.form['subject']
        
	post['due_date'] = None
	if post['is_SOS'] == True:
            post['due_date'] = post['request_date'] + timedelta(minutes=30)
	    post['price'] = 0
	else:
	    post['due_date'] = post['request_date'] + timedelta(days=7)
	    post['price'] = request.form['price']

        property_id = hashed_id_maker(g.db)

        cursor = g.db.execute("SELECT amount FROM Property WHERE id = ?", [buffer(property_id)])
	amount = cursor.fetchall()
	if len(amount) == 0:
	    # Status code 406 (ERROR)
	    # Description: Cannot find point information with given ID
	    return make_response(json.jsonify(status=406, message="No price information of ID %s" % session['username']), 406)
        elif float(amount[0][0]) < float(post['price']):
	    # Status code 406 (ERROR)
	    # Description: price in POST is bigger than user's account
	    return make_response(json.jsonify(status=400, message="Not enough money required"), 400)

        query_post = "INSERT INTO Requests_list VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
	g.db.execute(query_post, [
	        post['id'],
	        (post['requester_id']),
	        (post['from_lang']),
	        (post['to_lang']),
		post['is_SOS'],
	        (post['main_text']),
	        (post['context_text']) if post['context_text'] is not None else None,
	        (post['image_files']) if post['image_files'] is not None else None,
	        (post['sound_file']) if post['sound_file'] is not None else None,
		post['request_date'],
		post['format'],
		post['subject'],
		post['due_date'],
		None,
		0,
		0,
		post['price']
	    ])

	query_update_request = "UPDATE Users SET %s = %s + 1 WHERE string_id = ?"
	if post['is_SOS'] == True:
	    g.db.execute(query_update_request % ("requested_SOS", "requested_SOS"), [session['username']])
	else:
	    g.db.execute(query_update_request % ("requested_normal", "requested_normal"), [session['username']])
	    g.db.execute("UPDATE Property SET amount = amount - ? WHERE id = ?", [ post['price'], buffer(property_id) ])

	g.db.commit()

        # Status code 200 (OK)
        # Description: Succeed to post the request
	return make_response(json.jsonify(status=200, message="Posted %d" % post['id']), 200)

@app.route('/history', methods=["GET"])
@login_required
@exception_detector
def history():
    # Request method: GET
    # Parameters
    #     last_post_time(optional): Timestamp, take recent 20 post before the timestamp.
    #                               If this parameter is not provided, recent 20 posts from now are returned
    #     filter: Show user's order with the status following- Pending, in progress, completed
    #query = "SELECT is_SOS, id, requestor_id, from_lang, to_lang, main_text, request_date, translator_id, is_request_picked, is_request_finished FROM Requests_list WHERE (requestor_id = ? OR translator_id = ?) AND translator_id IS NOT NULL "
    query = "SELECT is_SOS, id, requester_id, from_lang, to_lang, main_text, request_date, translator_id, is_request_picked, is_request_finished FROM Requests_list WHERE requester_id = ? "

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

	item['is_SOS'] = bool(row[0])
	item['id'] = int(row[1])
	item['requester_id'] = str(row[2])
	item['from_lang'] = row[3]
	item['to_lang'] = row[4]
	item['main_text'] = row[5]
	item['request_date'] = row[6]
	item['translator_id'] = str(row[7])
	item['is_request_picked'] = bool(int(row[8]))
	item['is_request_finished'] = bool(int(row[9]))

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
    app.run()
