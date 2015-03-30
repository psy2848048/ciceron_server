import hashlib
from flask import make_response, json
from functools import wraps

# hashed ID maker for REVUNUE table
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


# hashed ID maker for REVUNUE table
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

def get_hashed_password(password, salt):
	hash_maker = hashlib.md5()
	hash_maker.update(salt)
	hash_maker.update(password)
	hash_maker.update(salt)
	return hash_maker.digest()

#def check_and_update_reg_key(conn, os_name, registration_id):
#    # Register key: Android
#    user_id = session['username']
#    cursor = conn.execute("SELECT * FROM RegKey_%s WHERE id = ?" % os_name, [buffer(user_id)])
#    result = cursor.fetchall()
#    if len(result) == 0:
#        conn.execute("INSERT INTO RegKey_android VALUES (?, ?)"), [buffer(user_id), buffer(registration_id)]
#    elif len(result) == 1 and result[0][1] != registration_id:
#        conn.execute("UPDATE RegKey_android SET reg_key = ? WHERE id = ?", [buffer(registration_id), buffer(user_id)])

def get_id_from_text(conn, text, table):
    cursor = conn.execute("SELECT id from %s WHERE text = ?" % table, [buffer(text)])
    return cursor.fetchall()[0][0]

def get_user_id(conn, text_id):
    cursor = conn.execute("SELECT id from D_USERS WHERE email = ?",
            [buffer(text_id)])
    return int(cursor.fetchall()[0][0])

def get_user_email(conn, num_id):
    cursor = conn.execute("SELECT email from D_USERS WHERE id = ?",
            [num_id])
    return str(cursor.fetchall()[0][0])

def get_text_from_id(conn, id_num, table):
    cursor = conn.execute("SELECT text from %s WHERE id = ?" % table, id_num)
    return cursor.fetchall()[0][0]

def get_new_id(conn, table):
    cursor = conn.execute("SELECT max(id) FROM %s " % table)
    current_id_list = cursor.fetchall()
    new_id = None
    if len(current_id_list[0]) == 0: new_id = 0
    else:                            new_id = int(current_id_list[0][0]) + 1

    return new_id

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        else:
    	    return make_response(json.jsonify(
                       status_code = 403,
    	               message = "Login required"
	           ), 403)
    return decorated_function

def exception_detector(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print e
            g.db.rollback()
            return make_response(
                    json.jsonify(
                       status_code = 500,
                       message = "DB Internal error"
                       ),
                    500
                   )
    return decorated_function

def word_counter(filePathName):
    f = open(filePathName, 'r')
    words=0
    for lines in f.readlines():
        words += len(lines.aplit(' '))
    f.close()

    return words
