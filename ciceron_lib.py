import hashlib, codecs
from flask import make_response, json, g, session
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
    rs = cursor.fetchall()
    if len(rs) == 0: result = -1
    else:            result = int(rs[0][0])
    return result

def get_user_id(conn, text_id):
    cursor = conn.execute("SELECT id from D_USERS WHERE email = ?",
            [buffer(text_id)])
    rs = cursor.fetchall()
    if len(rs) == 0: result = -1
    else:            result = int(rs[0][0])
    return result

def get_user_email(conn, num_id):
    cursor = conn.execute("SELECT email from D_USERS WHERE id = ?",
            [num_id])
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

def get_text_from_id(conn, id_num, table):
    cursor = conn.execute("SELECT text from %s WHERE id = ?" % table, [id_num])
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

def get_new_id(conn, table):
    cursor = conn.execute("SELECT max(id) FROM %s " % table)
    current_id_list = cursor.fetchall()
    new_id = None
    if current_id_list[0][0] is None: new_id = 0
    else:                         new_id = int(current_id_list[0][0]) + 1
    return new_id

def get_path_from_id(conn, id_num, table):
    cursor = conn.execute("SELECT path from %s WHERE id = ?" % table, [id_num])
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

def get_main_text(conn, text_id, table):
    path = get_path_from_id(conn, text_id, table)
    if path is None: return None
    else:
        words = ""
        f = codecs.open(path, 'r', 'utf-8')
        words = ('').join(f.readlines())
        return words

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'useremail' in session:
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
        words += len(lines.split(' '))
    f.close()

    return words

def json_from_V_REQUESTS(conn, rs, purpose="newsfeed"):
    result = []

    for row in rs:
        # For fetching translators in queue
        queue_id = row[23]
        cursor2 = conn.execute("SELECT * FROM V_QUEUE_LISTS WHERE id = ? ORDER BY user_id",
                [queue_id])

        queue_list = []
        for q_item in cursor2.fetchall():
            temp_item=dict(
                    id=      q_item[2],
                    name=    str(q_item[4]),
                    picPath= str(q_item[5]) if q_item[5] is not None else None
                    )
            queue_list.append(temp_item)

        # For getting word count of the request
        cursor2 = conn.execute("SELECT path FROM D_REQUEST_TEXTS  WHERE id = ?", [row[28]])
        list_txt = cursor2.fetchall()
        if len(list_txt[0]) == 0:
            num_of_words = None
        else:
            num_of_words = word_counter(list_txt[0][0])


        item = dict(
                request_id=row[0],
                request_clientId=str(row[2]),
                request_clientName=str(row[3]),
                request_clientPicPath=str(row[4]) if row[4] is not None else None,
                request_originalLang=row[13],
                request_targetLang=row[15],
                request_isSos= True if row[17] == "True" else False,
                request_format=row[19],
                request_subject=row[21],
                request_translatorsInQueue=queue_list,
                request_isTransOngoing=row[18],
                request_ongoingWorkerId=str(row[6]) if row[6] is not None else None,
                request_ongoingWorkerName=str(row[7]) if row[7] is not None else None,
                request_ongoingWorkerPicPath=str(row[8]) if row[8] is not None else None,
                request_registeredTime=row[24],
                request_isText= True if row[27] == "True" else False,
                request_isPhoto= True if row[29] == "True" else False,
                request_isSound= True if row[31] == "True" else False,
                request_isFile= True if row[33] == "True" else False,
                reqeust_words=num_of_words,
                request_dueTime=row[25],
                request_points=row[26]
            )

        if purpose == "newsfeed":
            # Show context if normal request, or show main text
            text_appear = None
            if row[17] == "True": text_appear = get_main_text(g.db, row[28])
            else                : text_appear = str(row[36]) if row[36] is not None else None
            item['request_text'] = text_appear

        elif purpose == "complete_client":
            item['request_title']=str(row[44]) if row[44] is not None else None

        elif purpose == "complete_translator":
            item['request_title']=str(row[48]) if row[48] is not None else None

        elif purpose == "ongoing_translator":
            del item['request_translatorsInQueue']
            del item['request_isTransOngoing']
            del item['request_ongoingWorkerId']
            del item['request_ongoingWorkerName']
            del item['request_ongoingWorkerPicPath']
            del item['request_isTransOngoing']
            item['request_text'] = get_main_text(g.db, row[28], "D_REQUEST_TEXTS")
            item['request_context'] = str(row[36]) if row[36] is not None else None
            item['request_translatedText'] = get_main_text(g.db, row[49], "D_TRANSLATED_TEXT")

        if purpose.startswith('complete') or purpose.startswith('ongoing'):
            # For getting translator's badges
            cursor2 = conn.execute("SELECT badge_id FROM D_AWARDED_BADGES WHERE id = (SELECT badgeList_id FROM D_USERS WHERE email = ? LIMIT 1)", [buffer(row[6])])
            badge_list = [ row[0] for row in cursor2.fetchall() ]
            item['translator_achievement'] = badge_list

        result.append(item)

    return result

def complete_groups(table):
    if request.method == "GET":
        my_user_id = get_user_id(g.db, session['useremail'])
        cursor = g.db.execute("SELECT id, text FROM %s WHERE user_id = ? ORDER BY id ASC" % table, [my_user_id])
        rs = cursor.fetchall()

        result = [ dict(id=row[0], name=str(row[1])) for row in rs ]
        return make_response(json.jsonify(data=result), 200)

    elif request.method == "POST":
        group_name = request.form['group_name']
        if group_name == "Documents":
            return make_response(json.jsonify(message="'Documents' is default group name"), 401)

        my_user_id = get_user_id(g.db, session['useremail'])

        new_group_id = get_new_id(g.db, table)
        g.db.execute("INSERT INTO %s VALUES (?,?,?)" % table,
            [new_group_id, my_user_id, buffer(group_name)])
        g.db.commit()
        return make_response(json.jsonify(message="New group %s has been created" % group_name), 200)

    elif request.method == "PUT":
        group_id = int(request.form['group_id'])
        group_name = request.form['group_name']
        if group_name == "Documents":
            return make_response(json.jsonify(message="'Documents' is default group name"), 401)
        g.db.execute("UPDATE %s SET text = ? WHERE id = ?" % table, [buffer(group_name), group_id])
        g.db.commit()
        return make_response(json.jsonify(message="Group name is changed to %s" % group_name), 200)

    elif request.method == 'DELETE':
        group_id = int(request.form['group_id'])
        group_text = get_text_from_id(g.db, group_id, table)
        if group_text == "Documents":
            return make_response(json.jsonify(message="You cannot delete 'Documents' group"), 401)
        g.db.execute("DELETE FROM %s WHERE id = ?" % table, [group_id])
        g.db.commit()
        return make_response(json.jsonify(message="Group %d is deleted." % group_id), 200)
