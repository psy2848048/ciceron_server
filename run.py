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
        username = request.form['username']
	hash_maker = hashlib.md5()
	hash_maker.update(app.config['IDENTIFIER'])
	hash_maker.update(request.form['password'])
	hash_maker.update(app.config['IDENTIFIER'])
	hashed_password = hash_maker.digest()
        
        cursor = g.db.execute("SELECT string_id, password_hased FROM Users where string_id = ?", [buffer(username)])

	rs = cursor.fetchall()
	if len(rs) > 1:
	    return make_response ('Constraint violation error!', 406)

        elif len(rs) == 0:
	    return 'Not registered %s' % username

	if str(rs[0][1]) == str(hashed_password):
	    session['logged_in'] = True
	    session['username'] = username
	    return make_response('You\'re logged with user %s' % username, 200)
	else:
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
    if session['logged_in'] == True:
	username_temp = session['username']
        session.pop('logged_in', None)
	session.pop('username', None)
        return make_response(json.jsonify(
                   status_code = 200,
                   message = "User %s is logged out" % username_temp
               ), 200)
    else:
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

        g.db.execute("INSERT INTO Users VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", 
      		        [buffer(username), buffer(hashed_password), buffer(nickname), None, buffer(mother_language), None, 0, 1, False, 0, False, False])
        g.db.commit() 

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
    nickname = request.args['nickname']
    print "nick: %s" % nickname
    cursor = g.db.execute("select * from Users where nickname = ?", [buffer(nickname)])
    check_data = cursor.fetchall()
    if len(check_data) == 0:
        return make_response(json.jsonify(status=dict(code=200, message="You may use the nick %s" % nickname)), 200)
    else:
	return make_response(json.jsonify(status=dict(code=406, message="Duplicated nick %s" % nickname)), 406)

@app.route('/idCheck', methods=['GET'])
@exception_detector
def idChecker():
    email_id = request.args['email_id']
    print "email_id: %s" % email_id
    cursor = g.db.execute("select * from Users where string_id = ?", [buffer(email_id)])
    check_data = cursor.fetchall()
    if len(check_data) == 0:
        return make_response(json.jsonify(status=dict(code=200, message="You may use the id %s" % email_id)), 200)
    else:
	return make_response(json.jsonify(status=dict(code=406, message="Duplicated nick %s" % email_id)), 406)

@app.route('/update_profile_pic', methods=["GET", "POST"])
@exception_detector
@login_required
def update_profile_pic():
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

@app.route('/post_list', methods=["GET"])
@exception_detector
def post_list():
    # Request method: GET
    # Parameters
    #     last_post_time(optional): Timestamp, take recent 20 post before the timestamp.
    #                               If this parameter is not provided, recent 20 posts from now are returned
    if request.method == "GET":
        query = "SELECT is_SOS, id, requester_id, from_lang, to_lang, main_text, request_date, format, subject, due_date, image_files, sound_file, price FROM Requests_list WHERE is_request_picked = 0 AND is_request_finished = 0 "
        if 'last_post_time' in request.args.keys():
            query += "AND request_date < datetime(%f) " % Decimal(request.args['last_post_time'])
        query += "ORDER BY request_date DESC LIMIT 20"

        cursor = g.db.execute(query)
        rs = cursor.fetchall()
        result = []

        for row in rs:
            item = dict()
	    item['is_SOS'] = bool(row[0])
	    item['id'] = row[1]
	    item['requester_id'] = row[2]
            cursor = g.db.execute("SELECT profile_img, grade FORM Users WHERE string_id = ?", [ item['requester_id'] ])
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

        return make_response(json.jsonify(item_list = result), 200)

@app.route('/post', methods=["POST"])
@exception_detector
@login_required
def post():
    # Request method: POST
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
	post['is_SOS'] = request.form['is_SOS']
	post['main_text'] = request.form['main_text']
	post['context_text'] = request.form.get('context_text', None)
	post['image_files'] = request.form.get('image_files', None)
	post['sound_file'] = request.form.get('sound_file', None)
	post['request_date'] = datetime.now()
	post['format'] = request.form['format']
	post['subject'] = request.form['subject']
        
	post['due_date'] = None
	if bool(post['is_SOS']) == True:
            post['due_date'] = post['request_date'] + timedelta(minutes=30)
	else:
	    post['due_date'] = post['request_date'] + timedelta(days=7)

	post['price'] = request.form['price']

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

	g.db.commit()

	return make_response(json.jsonify(status=200, message="Posted %d" % post['id']), 200)

@app.route('/history', methods=["GET"])
@login_required
@exception_detector
def history():
    # Request method: GET
    # Parameters
    #     last_post_time(optional): Timestamp, take recent 20 post before the timestamp.
    #                               If this parameter is not provided, recent 20 posts from now are returned
    #query = "SELECT is_SOS, id, requestor_id, from_lang, to_lang, main_text, request_date, translator_id, is_request_picked, is_request_finished FROM Requests_list WHERE (requestor_id = ? OR translator_id = ?) AND translator_id IS NOT NULL "
    query = "SELECT is_SOS, id, requester_id, from_lang, to_lang, main_text, request_date, translator_id, is_request_picked, is_request_finished FROM Requests_list WHERE (requester_id = ? OR translator_id = ?) "
    if 'last_post_time' in request.args.keys():
        query += " AND request_date < datetime(%f) " % Decimal(request.args['last_post_time'])
    query += " ORDER BY request_date DESC LIMIT 20"

    cursor = g.db.execute(query, [session['username'], session['username']])
    rs = cursor.fetchall()
    result = []

    for row in rs:
        item = dict()

	item['is_SOS'] = bool(row[0])
	item['id'] = row[1]
	item['requester_id'] = row[2]
	item['from_lang'] = row[3]
	item['to_lang'] = row[4]
	item['main_text'] = row[5]
	item['request_date'] = row[6]
	item['translator_id'] = row[7]
	item['is_request_picked'] = row[8]
	item['is_request_finished'] = row[9]

	result.append(item)

    return make_response(json.jsonify(item_list = result), 200)

@app.route('/pick_request/<post_id>', methods=['GET'])
@login_required
@exception_detector
def pick_request(post_id):
    # Request method: GET
    # Parameters
    #    post_id: requested post id

    query_pic = "SELECT profile_img from Users WHERE string_id = ?"
    cursor = g.db.execute(query_pic, [buffer(session['username'])])
    image_address = cursor.fetchall()[0][0]

    query_information = "UPDATE Requests_list SET due_date = current_timestamp, translator_id = '%s', translator_pic = '%s', is_request_picked = 1 WHERE id = %d" \
                             % (buffer(session['username']), buffer(image_address), post_id)
    g.db.execute(query_information)
    g.db.commit()

if __name__ == '__main__':
    app.run()
