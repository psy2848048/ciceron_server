import hashlib, codecs, os, random, string, sys, paypalrestsdk
from flask import make_response, json, g, session, request, current_app
from datetime import datetime, timedelta
from functools import wraps
super_user = ["pjh0308@gmail.com", "happyhj@gmail.com", "admin@ciceron.me"]

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

def get_hashed_password(password, salt=None):
    hash_maker = hashlib.sha256()

    if salt is None:
        hash_maker.update(password)
    else:
        hash_maker.update(salt.encode() + password + salt.encode())

    return hash_maker.hexdigest()

def random_string_gen(size=6, chars=string.letters + string.digits):
    gened_string = ''.join(random.choice(chars) for _ in range(size))
    gened_string = gened_string.encode('utf-8')
    return gened_string

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

def get_group_id_from_user_and_text(conn, user_id, text, table):
    cursor = conn.execute("SELECT id FROM %s WHERE user_id = ? AND text = ?" % table, [user_id, buffer(text)])
    rs = cursor.fetchall()
    if len(rs) == 0:
        return -1
    else:
        return rs[0][0]

def parameter_to_bool(value):
    if value in ['True', 'true', 1, '1', True]:
        return True
    else:
        return False

def bool_value_converter(array):
    new_list = []
    for item in array:
        if type(item) == 'bool':
            if item == True:
                new_list.append(1)
            else:
                new_list.append(0)
        else:
            new_list.append(item)

    return new_list

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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('useremail') in super_user:
            return f(*args, **kwargs)
        else:
            return make_response(json.jsonify(
                       status_code = 403,
                       message = "Admin only"
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
            return make_response(json.jsonify(message=str(e)),500)

    return decorated_function

def translator_checker(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        cursor = g.db.execute("SELECT is_translator FROM D_USERS WHERE email = ?", [buffer(session['useremail'])])
        rs = cursor.fetchall()
        if len(rs) == 0 or rs[0][0] == 0:
            return make_response(
                    json.jsonify(
                       message = "You are not translator. This API is only for translators."
                       ), 403)

        else:
            return f(*args, **kwargs)

    return decorated_function

def strict_translator_checker(conn, user_id, request_id):
    cursor = conn.execute("SELECT is_translator, mother_language_id, other_language_list_id FROM D_USERS WHERE id = ?", [user_id])
    rs = cursor.fetchall()
    if len(rs) == 0 or rs[0][0] == 0 or rs[0][0] == 'False' or rs[0][0] == 'false':
        return False

    # Get language list
    mother_language_id = rs[0][1]

    cursor = conn.execute("SELECT language_id FROM D_TRANSLATABLE_LANGUAGES WHERE user_id = ?",
                 [user_id])
    language_list = [ item[0] for item in cursor.fetchall() ]
    language_list.append(mother_language_id)

    # Check request language
    query = None
    if session['useremail'] in super_user:
        query = "SELECT original_lang_id, target_lang_id FROM F_REQUESTS WHERE id = ? "
    else:
        query = "SELECT original_lang_id, target_lang_id FROM F_REQUESTS WHERE id = ? AND is_paid IN (1, 'True', 'true')"
    cursor = conn.execute(query, [request_id])
    rs = cursor.fetchall()[0]
    original_lang_id = rs[0]
    target_lang_id = rs[1]

    if original_lang_id in language_list and target_lang_id in language_list:
        return True
    else:
        return False

        #return make_response(
        #        json.jsonify(
        #           message = "You are not translator. This API is only for translators."
        #           ), 401)

def char_counter(filePathName):
    f = open(filePathName, 'r')
    words=0
    for lines in f.readlines():
        words += len(lines.decode('utf-8'))
    f.close()

    return words

def crossdomain(f, origin='*', methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    @wraps(f)
    def decorator(*args, **kwargs):
        resp = f(*args, **kwargs)
        resp.headers['Access-Control-Allow-Origin'] = origin
        resp.headers['Access-Control-Max-Age'] = str(max_age)
        return resp

    return decorator

def json_from_V_REQUESTS(conn, rs, purpose="newsfeed"):
    result = []

    for row in rs:
        request_id = row[0]
        # For fetching translators in queue
        cursor2 = conn.execute("SELECT * FROM V_QUEUE_LISTS WHERE request_id = ? ORDER BY user_id",
                [request_id])

        queue_list = []
        for q_item in cursor2.fetchall():
            cursor3 = conn.execute("SELECT language_id FROM D_TRANSLATABLE_LANGUAGES WHERE user_id = ?",
                [q_item[2]])
            other_language_list = ",".join( [ str(item[0]) for item in cursor3.fetchall() ] )
            cursor4 = conn.execute("SELECT badge_id FROM D_AWARDED_BADGES WHERE user_id = ?",
                [q_item[2]])
            badgeList = (',').join([ str(item[0]) for item in cursor4.fetchall() ])

            # GET list: user's keywords
            cursor5 = g.db.execute("SELECT key.text FROM D_USER_KEYWORDS ids JOIN D_KEYWORDS key ON ids.keyword_id = key.id WHERE ids.user_id = ?", [q_item[2]])
            keywords = (',').join([ str(item[0]) for item in cursor5.fetchall() ])

            temp_item=dict(
                user_email=                     str(q_item[3]),
                user_name=                      str(q_item[4]),
                user_motherLang=                q_item[5],
                user_profilePicPath=            str(q_item[8]) if q_item[8] != None else None,
                user_translatableLang=          other_language_list,
                user_numOfRequestsPending=       q_item[9],
                user_numOfRequestsOngoing=       q_item[10],
                user_numOfRequestsCompleted=     q_item[11],
                user_numOfTranslationsPending=   q_item[12],
                user_numOfTranslationsOngoing=   q_item[13],
                user_numOfTranslationsCompleted= q_item[14],
                user_badgeList=                 badgeList,
                user_isTranslator=              True if q_item[6] == 1 else False,
                user_profileText=               str(q_item[16]),
                user_revenue=                   -65535,
                user_keywords=                   keywords
                )
            queue_list.append(temp_item)

        # For getting word count of the request
        cursor2 = conn.execute("SELECT path FROM D_REQUEST_TEXTS  WHERE id = ?", [row[30]])
        list_txt = cursor2.fetchall()

        if len(list_txt) == 0 or len(list_txt[0]) == 0:
            num_of_words = None
        else:
            num_of_words = char_counter(list_txt[0][0])

        item = dict(
                request_id=row[0],
                request_clientId=str(row[2]),
                request_clientName=str(row[3]),
                request_clientPicPath=str(row[4]) if row[4] is not None else None,
                request_originalLang=row[13],
                request_targetLang=row[15],
                request_isSos= True if row[17] == 1 else False,
                request_format=row[19],
                request_subject=row[21],
                request_isText= True if row[29] == 1 else False,
                request_text=get_main_text(conn, row[30], "D_REQUEST_TEXTS"),
                request_isPhoto= True if row[31] == 1 else False,
                request_photoPath=get_path_from_id(g.db, row[32], "D_REQUEST_PHOTOS"),
                request_isSound= True if row[35] == 1 else False,
                request_soundPath=get_path_from_id(g.db, row[36], "D_REQUEST_SOUNDS"),
                request_isFile= True if row[33] == 1 else False,
                request_filePath=get_path_from_id(g.db, row[34], "D_REQUEST_FILES"),
                request_context=None, # For marking
                request_status=row[18],
                request_registeredTime=row[24],
                request_dueTime=row[27],
                request_transStartTime=row[55],
                request_expectedTime=row[25],
                request_words=num_of_words,
                request_points=row[28],
                request_translatorsInQueue=queue_list,
                request_translatorId=str(row[6]) if row[6] is not None else None,
                request_translatorName=str(row[7]) if row[7] is not None else None,
                request_translatorPicPath=str(row[8]) if row[8] is not None else None,
                request_translatorBadgeList="",  # For marking
                request_translatedText=None, # For marking
                request_translatorComment=str(row[40]) if row[40] is not None else None,
                request_translatedTone= str(row[42]) if row[42] is not None else None,
                request_submittedTime=row[26],
                request_feedbackScore=row[54],
                request_title=None # For marking
            )

        if purpose == "newsfeed":
            # Show context if normal request, or show main text
            if row[17] == 1: # True
                item['request_context'] = get_main_text(g.db, row[30], "D_REQUEST_TEXTS")
                item['request_translatedText'] = get_main_text(g.db, row[51], "D_TRANSLATED_TEXT")
            else:
                item['request_context']=str(row[38]) if row[38] is not None else None
                item['request_text']=None
                item['request_soundPath']=None
                item['request_photoPath']=None
                item['request_filePath']=None

        elif purpose == "pending_client":
            # Show context if normal request, or show main text
            if row[17] == 1: # True
                item['request_context'] = get_main_text(g.db, row[30], "D_REQUEST_TEXTS")
                item['request_translatedText'] = get_main_text(g.db, row[51], "D_TRANSLATED_TEXT")
            else:
                item['request_context']=str(row[38]) if row[38] is not None else None

        elif purpose in ["complete_client", "complete_translator", "ongoing_translator"]:
            if row[17] == 0: # False
                item['request_context'] = str(row[38]) if row[38] is not None else None
            item['request_translatedText'] = get_main_text(g.db, row[51], "D_TRANSLATED_TEXT")
            item['request_title']=str(row[46]) if row[46] is not None else None

        elif purpose == "ongoing_client":
            if row[17] == 0: # False
                item['request_context'] = str(row[38]) if row[38] is not None else None

        if purpose.startswith('complete') or purpose.startswith('ongoing'):
            # For getting translator's badges
            cursor2 = conn.execute("SELECT badge_id FROM D_AWARDED_BADGES WHERE id = (SELECT badgeList_id FROM D_USERS WHERE email = ? LIMIT 1)", [buffer(row[6])])
            badge_list = (",").join([ str(row[0]) for row in cursor2.fetchall() ])
            item['request_translatorBadgeList'] = badge_list

        result.append(item)

    return result

def complete_groups(conn, parameters, table, method, url_group_id=None, since=None):
    if method == "GET":
        my_user_id = get_user_id(conn, session['useremail'])
        query = "SELECT id, text FROM %s WHERE user_id = ? "
        if since != None:
            query += "AND registered_time < datetime(%s, 'unixepoch') " % since
        query += "ORDER BY id DESC"
        cursor = conn.execute(query % table, [my_user_id])
        rs = cursor.fetchall()

        result = [ dict(id=row[0], name=str(row[1])) for row in rs ]
        return result

    elif method == "POST":
        group_name = (parameters['group_name']).encode('utf-8')
        if group_name == "Documents":
            return -1

        my_user_id = get_user_id(conn, session['useremail'])

        new_group_id = get_new_id(conn, table)
        conn.execute("INSERT INTO %s VALUES (?,?,?)" % table,
            [new_group_id, my_user_id, buffer(group_name)])
        conn.commit()
        return group_name

    elif method == "PUT":
        group_id = int(url_group_id)
        group_name = (parameters['group_name']).encode('utf-8')
        if group_name == u"Documents":
            return -1
        conn.execute("UPDATE %s SET text = ? WHERE id = ?" % table, [buffer(group_name), group_id])
        conn.commit()
        return group_name

    elif method == 'DELETE':
        group_id = int(url_group_id)
        group_text = get_text_from_id(conn, group_id, table)
        if group_text == "Documents":
            return -1
        conn.execute("DELETE FROM %s WHERE id = ?" % table, [group_id])

        default_group_id = get_group_id_from_user_and_text(g.db, session['useremail'], "Documents", table)
        if table.find("TRANSLATOR") >= 0: col = 'translator_completed_group_id'
        else:                             col = 'client_completed_group_id'
        conn.execute("UPDATE F_REQUESTS SET %(col)s = ? WHERE %(col)s = ?" % {'col':col}, [default_group_id, group_id])

        conn.commit()
        return group_id

def save_request(conn, parameters, str_request_id, result_folder):
    request_id = int(str_request_id)
    new_translatedText = (parameters.get("request_translatedText", None)).encode('utf-8')
    new_comment = parameters.get("request_comment", None)
    if new_comment != None:
        new_comment = new_comment.encode('utf-8')
    new_tone = parameters.get("request_tone", None)

    cursor = conn.execute("SELECT translatedText, comment_id, tone_id FROM V_REQUESTS WHERE request_id = ?", [request_id])
    rs = cursor.fetchall()

    translatedText_path = rs[0][0]
    comment_id = rs[0][1]
    tone_id = rs[0][2]

    if new_translatedText != None:
        # Save new translated text
        if translatedText_path == None:
            filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + ".txt"
            translatedText_path = os.path.join(result_folder, filename)
            new_result_id = get_new_id(conn, "D_TRANSLATED_TEXT")
            conn.execute("INSERT INTO D_TRANSLATED_TEXT VALUES (?,?)", [new_result_id, buffer(translatedText_path)])
            conn.execute("UPDATE F_REQUESTS SET translatedText_id = ? WHERE id = ?", [new_result_id, request_id])

        f = open(translatedText_path, 'wb')
        f.write(new_translatedText)
        f.close()

    # Save new comment
    if new_comment != None:
        if comment_id != None:
            conn.execute("UPDATE D_COMMENTS SET text = ? WHERE id = ?", [buffer(new_comment), comment_id])
        else:
            comment_id = get_new_id(conn, "D_COMMENTS")
            conn.execute("INSERT INTO D_COMMENTS VALUES (?,?)", [comment_id, buffer(new_comment)])
            conn.execute("UPDATE F_REQUESTS SET comment_id = ? WHERE id = ?", [comment_id, request_id])

    # Save new tone
    if new_tone != None:
        if tone_id != None:
            conn.execute("UPDATE D_TONES SET text = ? WHERE id = ?", [buffer(new_tone), tone_id])
            conn.execute("UPDATE F_REQUESTS SET tone_id = ? WHERE id = ?", [tone_id, request_id])
        else:
            tone_id = get_new_id(conn, "D_TONES")
            conn.execute("INSERT INTO D_TONES VALUES (?,?)", [tone_id, buffer(new_tone)])
            conn.execute("UPDATE F_REQUESTS SET tone_id = ? WHERE id = ?", [tone_id, request_id])

    conn.commit()

def update_user_record(conn, client_id=None, translator_id=None):
    if client_id is not None:
        conn.execute("""UPDATE D_USERS SET 
                numOfRequestPending = (SELECT count(id) FROM F_REQUESTS WHERE status_id = 0 AND client_user_id = ?),
                numOfRequestOngoing = (SELECT count(id) FROM F_REQUESTS WHERE status_id = 1 AND client_user_id = ?),
                numOfRequestCompleted = (SELECT count(id) FROM F_REQUESTS WHERE status_id = 2 AND client_user_id = ?)
                WHERE id = ?""", [client_id, client_id, client_id, client_id])

    if translator_id is not None:
        conn.execute("""UPDATE D_USERS SET 
                numOfTranslationPending = (SELECT count(queue.id) FROM F_REQUESTS fact LEFT OUTER JOIN D_QUEUE_LISTS queue ON fact.queue_id = queue.id WHERE fact.status_id = 0 AND queue.user_id = ?),
                numOfTranslationOngoing = (SELECT count(id) FROM F_REQUESTS WHERE status_id = 1 AND ongoing_worker_id = ?),
                numOfTranslationCompleted = (SELECT count(id) FROM F_REQUESTS WHERE status_id = 2 AND ongoing_worker_id = ?)
                WHERE id = ?""", [translator_id, translator_id, translator_id, translator_id])

    conn.commit()

def parse_request(req):
    if len(req.form) == 0 and len(req.files) == 0:
        parameter_list = req.get_json()
        if parameter_list != None:
            result = dict()

            for key, value in parameter_list.iteritems():
                result[key] = value

            return result
        
        else:
            return dict()

    else:
        if len(req.form) != 0:
            result = dict()
            for key, value in req.form.iteritems():
                result[key] = value

            return result

        else:
            return dict()
 
def send_push(conn, gcm_obj,
              user_ids,
              message,
              collapse_key=None,
              delay_while_idle=None,
              time_to_live=None,
              restricted_package_name=None,
              dry_run=None):
    
    registration_keys = []
    for user in user_ids:
        user_number = get_user_id(conn, user)
        cursor = conn.execute("SELECT reg_key FROM D_MACHINES WHERE user_id = ? AND is_push_allowed = 1", [user_number])
        client_infos = cursor.fetchall()

        # Gather registration IDs
        registration_keys.extend([ item[0] for item in client_infos ])

    # Send one message to devices at once
    if len(registration_keys) > 0:
        response = gcm_obj.send(registration_keys, message,
                    collapse_key=collapse_key,
                    delay_while_idle=delay_while_idle,
                    time_to_live=time_to_live,
                    restricted_package_name=restricted_package_name,
                    dry_run=dry_run)

    return response

def send_mail(mail_to, subject, message):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    content = MIMEText(message, 'plain', _charset='utf-8')
    msg = MIMEMultipart('form-data')
    msg['Subject'] = subject
    msg['From'] = 'no-reply@ciceron.me'
    msg['To'] = mail_to
    msg.attach(content)

    a = smtplib.SMTP('smtp.worksmobile.com:587')
    a.starttls()
    a.login('no-reply@ciceron.me', 'Ciceron01!')
    a.sendmail('no-reply@ciceron.me', mail_to, msg.as_string())
    a.quit()
