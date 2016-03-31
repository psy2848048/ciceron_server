# -*- coding: utf-8 -*-

import hashlib, codecs, os, random, string, sys, paypalrestsdk, logging
from flask import make_response, json, g, session, request, current_app
from datetime import datetime, timedelta
from functools import wraps
super_user = ["pjh0308@gmail.com", "happyhj@gmail.com", "admin@ciceron.me"]

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
    query = "SELECT id from CICERON.%s WHERE text = " % table
    query += "%s"
    cursor = conn.cursor()
    cursor.execute(query, (text, ))
    rs = cursor.fetchall()
    if len(rs) == 0: result = -1
    else:            result = int(rs[0][0])
    return result

def get_user_id(conn, text_id):
    cursor = conn.cursor()
    cursor.execute("SELECT id from CICERON.D_USERS WHERE email = %s", (text_id, ))
    rs = cursor.fetchall()
    if len(rs) == 0: result = -1
    else:            result = int(rs[0][0])
    return result

def get_facebook_user_id(conn, text_id):
    cursor = conn.cursor()
    cursor.execute("SELECT id, real_id from CICERON.D_FACEBOOK_USERS WHERE email = %s", (text_id, ))
    rs = cursor.fetchall()
    if len(rs) == 0: result = (-1, None)
    elif len(rs) > 1: raise Exception('Duplicated facebook user ID')
    else:            result = (rs[0][0], rs[0][1])
    return result

def get_user_email(conn, num_id):
    cursor = conn.cursor()
    cursor.execute("SELECT email from CICERON.D_USERS WHERE id = %s",
            [num_id])
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

def get_user_name(conn, num_id):
    cursor = conn.cursor()
    cursor.execute("SELECT name from CICERON.D_USERS WHERE id = %s",
            [num_id])
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

def get_text_from_id(conn, id_num, table):
    query = "SELECT text from CICERON.%s WHERE id = " % table
    query += "%s"
    cursor = conn.cursor()
    cursor.execute(query, (id_num, ))
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

def get_new_id(conn, table):
    cursor = conn.cursor()
    cursor.execute("SELECT nextval('CICERON.SEQ_%s') " % table)
    current_id_list = cursor.fetchone()
    return int(current_id_list[0])

def get_path_from_id(conn, id_num, table):
    query = "SELECT path from CICERON.%s WHERE id = " % table
    query += "%s"
    cursor = conn.cursor()
    cursor.execute(query, (id_num, ))
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

def get_main_text(conn, text_id, table):
    cursor = conn.cursor()
    query = "SELECT text FROM CICERON.%s WHERE id =" % table
    query += "%s "
    cursor.execute(query, (text_id, ) )
    main_text = cursor.fetchone()
    if main_text is not None:
        return main_text[0]
    else:
        return None

def get_group_id_from_user_and_text(conn, user_id, text, table):
    cursor = conn.cursor()
    query = "SELECT id FROM CICERON.%s " % table
    query += "WHERE user_id = %s AND text = %s "
    cursor.execute(query, (user_id, text) )
    rs = cursor.fetchall()
    if len(rs) == 0:
        return -1
    else:
        return rs[0][0]

def get_device_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT reg_key FROM CICERON.D_MACHINES WHERE user_id = %s AND is_push_allowed = true", (user_id, ) )
    return [reg_key[0] for reg_key in cursor.fetchall()]

def parameter_to_bool(value):
    if value in ['True', 'true', 1, '1', True]:
        return True
    else:
        return False

def get_total_amount(conn, request_id, user_id, is_additional='false'):
    cursor = conn.cursor()

    total_amount = 0
    if is_additional == 'false':
        cursor.execute("SELECT points FROM CICERON.F_REQUESTS WHERE id = %s" , (request_id, ))
        total_amount = cursor.fetchone()[0]

    else:
        cursor.execute("SELECT points FROM CICERON.F_REQUESTS WHERE id = %s" , (request_id, ))
        cur_amount = cursor.fetchone()[0]

        cursor.execute("SELECT nego_price FROM CICERON.D_QUEUE_LISTS WHERE request_id = %s AND user_id = %s", (request_id, user_id, ))
        rs = cursor.fetchone()
        nego_amount = None
        if rs is not None and len(rs) != 0:
            nego_amount = rs[0]
        else:
            return 'ERROR'

        total_amount = nego_amount - cur_amount

    return total_amount

def ddosCheckAndWriteLog(conn):
    cursor = conn.cursor()

    user_id = get_user_id(conn, session['useremail'])
    method = request.method
    api_endpoint = request.environ['PATH_INFO']
    ip_address = request.headers.get('x-forwarded-for-client-ip')

    query_apiCount = """
        SELECT count(*) FROM CICERON.TEMP_ACTIONS_LOG
          WHERE (user_id = %s OR ip_address = %s)
            AND log_time BETWEEN (CURRENT_TIMESTAMP - interval '1 seconds') AND CURRENT_TIMESTAMP"""
    cursor.execute(query_apiCount, (user_id, ip_address, ))
    conn_count = cursor.fetchone()[0]

    query_getBlacklist = """
        SELECT count(*) FROM CICERON.BLACKLIST
          WHERE user_id = %s
            AND %s BETWEEN time_from AND time_to
    """
    cursor.execute(query_getBlacklist, (user_id, ))
    blacklist_count = cursor.fetchone()[0]

    is_OK = True
    if conn_count > 100:
        session.pop('logged_in', None)
        session.pop('useremail', None)
        query_insertBlackList = """
            INSERT INTO CICERON.BLACKLIST (id, user_id, ip_address, time_from, time_to)
            VALUES
            (
               nextval('CICERON.SEQ_BLACKLIST')
              ,%s
              ,%s
              ,CURRENT_TIMESTAMP
              ,CURRENT_TIMESTAMP + interval('30 minutes')
            )
        """
        cursor.execute(query_insertBlackList, (user_id, ip_address, ))
        is_OK = False

    if blacklist_count > 0:
        session.pop('logged_in', None)
        session.pop('useremail', None)
        is_OK = False

    query_insertLog = """
        INSERT INTO CICERON.TEMP_ACTIONS_LOG
          (id, user_id, method, api, log_time, ip_address)
        VALUES
          (
             nextval('CICERON.SEQ_USER_ACTIONS')
            ,%s
            ,%s
            ,%s
            ,CURRENT_TIMESTAMP
            ,%s
          )
    """
    cursor.execute(query_insertLog, (user_id, method, api_endpoint, ))
    conn.commit()

    return is_OK

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_ddos_free = ddosCheckAndWriteLog(g.db)
        if 'useremail' in session and is_ddos_free == True:
            return f(*args, **kwargs)
        elif is_ddos_free == False:
            return make_response(json.jsonify(
                       status_code = 499,
                       message = "Blocked connection"
               ), 499)
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
        cursor = g.db.cursor()
        cursor.execute("SELECT is_translator FROM CICERON.D_USERS WHERE email = %s", (session['useremail'], ) )
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
    cursor = conn.cursor()
    cursor.execute("SELECT is_translator, mother_language_id, other_language_list_id FROM CICERON.D_USERS WHERE id = %s ", (user_id, ))
    rs = cursor.fetchall()
    if len(rs) == 0 or rs[0][0] == 0 or rs[0][0] == 'False' or rs[0][0] == 'false':
        return False

    # Get language list
    mother_language_id = rs[0][1]

    cursor.execute("SELECT language_id FROM CICERON.D_TRANSLATABLE_LANGUAGES WHERE user_id = %s ", (user_id, ))
    language_list = [ item[0] for item in cursor.fetchall() ]
    language_list.append(mother_language_id)

    # Check request language
    query = None
    if session['useremail'] in super_user:
        query = "SELECT original_lang_id, target_lang_id FROM CICERON.F_REQUESTS WHERE id = %s "
    else:
        query = "SELECT original_lang_id, target_lang_id FROM CICERON.F_REQUESTS WHERE id = %s AND is_paid = true "
    cursor.execute(query, (request_id, ) )
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

def getProfile(conn, user_id, rate=1, price=None):
    cursor = conn.cursor()
    query_userinfo = """
        SELECT  
            id, email, name, mother_language_id, is_translator,
            other_language_list_id, profile_pic_path,
            numOfRequestPending, numOfRequestOngoing, numOfRequestCompleted,
            numOfTranslationPending, numOfTranslationOngoing, numOfTranslationCompleted,
            badgeList_id, profile_text, trans_request_state, nationality, residence
        FROM CICERON.D_USERS WHERE id = %s
        """
    cursor.execute(query_userinfo, (user_id, ))
    userinfo = cursor.fetchone()

    cursor.execute("SELECT language_id FROM CICERON.D_TRANSLATABLE_LANGUAGES WHERE user_id = %s",
        (user_id, ))
    other_language_list = ",".join( [ str(item[0]) for item in cursor.fetchall() ] )
    cursor.execute("SELECT badge_id FROM CICERON.D_AWARDED_BADGES WHERE user_id = %s",
        (user_id, ))
    badgeList = (',').join([ str(item[0]) for item in cursor.fetchall() ])

    # GET list: user's keywords
    cursor.execute("SELECT key.text FROM CICERON.D_USER_KEYWORDS ids JOIN CICERON.D_KEYWORDS key ON ids.keyword_id = key.id WHERE ids.user_id = %s", (user_id, ))
    keywords = (',').join([ str(item[0]) for item in cursor.fetchall() ])

    result=dict(
        user_email=                     str(userinfo[1]),
        user_name=                      str(userinfo[2]),
        user_motherLang=                userinfo[3],
        user_profilePicPath=            str(userinfo[6]) if userinfo[6] != None else None,
        user_translatableLang=          other_language_list,
        user_numOfRequestsPending=       userinfo[7],
        user_numOfRequestsOngoing=       userinfo[8],
        user_numOfRequestsCompleted=     userinfo[9],
        user_numOfTranslationsPending=   userinfo[10],
        user_numOfTranslationsOngoing=   userinfo[11],
        user_numOfTranslationsCompleted= userinfo[12],
        user_badgeList=                 badgeList,
        user_isTranslator=              True if userinfo[4] == 1 else False,
        user_profileText=               str(userinfo[14]),
        user_revenue=                   -65535,
        user_keywords=                   keywords,
        user_transRequestState=         userinfo[15],
        user_nationality=                 userinfo[16],
        user_residence=                 userinfo[17]
        )

    if price != None:
        result['user_additionalPoint'] = price

    return result

def json_from_V_REQUESTS(conn, rs, purpose="newsfeed"):
    result = []
    cursor = g.db.cursor()

    # Return rate
    query_returnRate = "SELECT return_rate FROM CICERON.D_USERS WHERE email = %s"
    cursor.execute(query_returnRate, (session['useremail'], ))
    ret_returnRate = cursor.fetchone()

    return_rate = None
    if ret_returnRate is not None and len(ret_returnRate) > 0:
        return_rate = ret_returnRate[0]

    for row in rs:
        request_id = row[0]
        # For fetching translators in queue
        cursor.execute("SELECT * FROM CICERON.V_QUEUE_LISTS WHERE request_id = %s ORDER BY user_id",
                (request_id, ) )

        queue_list = []
        for q_item in cursor.fetchall():
            profile = getProfile(conn, q_item[2], rate=return_rate, price=q_item[17])
            queue_list.append(profile)

        # For getting word count of the request
        cursor.execute("SELECT path, text FROM CICERON.D_REQUEST_TEXTS  WHERE id = %s ", (row[30], ) )
        list_txt = cursor.fetchall()

        main_text = None
        if len(list_txt) == 0 or len(list_txt[0]) == 0:
            num_of_words = 0
            num_of_letters = 0
        else:
            num_of_letters = len(list_txt[0][1].decode('utf-8'))
            num_of_words = len(list_txt[0][1].decode('utf-8').split(' '))
            main_text = list_txt[0][1]

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
                request_isText=row[29],
                request_text=main_text,
                request_isPhoto=row[31],
                request_photoPath=get_path_from_id(g.db, row[32], "D_REQUEST_PHOTOS"),
                request_isSound=row[35],
                request_soundPath=get_path_from_id(g.db, row[36], "D_REQUEST_SOUNDS"),
                request_isFile=row[33],
                request_filePath=get_path_from_id(g.db, row[34], "D_REQUEST_FILES"),
                request_context=None, # For marking
                request_status=row[18],
                request_registeredTime=int(row[24].strftime("%s")) * 1000 if row[24] != None else None,
                request_dueTime=int(row[27].strftime("%s")) * 1000 if row[27] != None else None,
                request_transStartTime=int(row[55].strftime("%s")) * 1000 if row[55] != None else None,
                request_expectedTime=int(row[25].strftime("%s")) * 1000 if row[25] != None else None,
                request_words=num_of_words,
                request_letters=num_of_letters,
                request_points=row[28] if purpose.endswith("client") else row[28] * return_rate,
                request_translatorsInQueue=queue_list,
                request_translatorId=row[6],
                request_translatorName=row[7],
                request_translatorPicPath=row[8],
                request_translatorBadgeList="",  # For marking
                request_translatedText=None, # For marking
                request_translatorComment=row[40],
                request_translatedTone=row[42],
                request_submittedTime=row[26],
                request_feedbackScore=row[54],
                request_title=None, # For marking
            )

        item['request_isAdditionalPointNeeded'] = row[56]
        if purpose.endswith("client") and row[57] != None:
            item['request_addionalPoint'] = row[57]
        elif (not purpose.endswith("client")) and row[57] != None:
            item['request_addionalPoint'] = row[57] * return_rate
        else:
            item['request_addionalPoint'] = None
        item['request_isAdditionalPointPaid'] = row[58] 

        if purpose.startswith("stoa"):
            # Show context if normal request, or show main text
            if row[17] == True: # True
                item['request_context'] = main_text
                item['request_translatedText'] = get_main_text(g.db, row[51], "D_TRANSLATED_TEXT")
            else:
                item['request_context'] = row[38]
                item['request_text'] = None
                item['request_soundPath'] = None
                item['request_photoPath'] = None
                item['request_filePath'] = None

        elif purpose == "pending_client":
            # Show context if normal request, or show main text
            if row[17] == True: # True
                item['request_context'] = get_main_text(g.db, row[30], "D_REQUEST_TEXTS")
                item['request_translatedText'] = get_main_text(g.db, row[51], "D_TRANSLATED_TEXT")
            else:
                item['request_context'] = row[38]

        elif purpose in ["complete_client", "complete_translator", "ongoing_translator"]:
            if row[17] == False: # False
                item['request_context'] = row[38]
            item['request_translatedText'] = get_main_text(g.db, row[51], "D_TRANSLATED_TEXT")
            item['request_title']=row[46]

        elif purpose == "ongoing_client":
            if row[17] == False: # False
                item['request_context'] = row[38]

        if purpose.startswith('complete') or purpose.startswith('ongoing'):
            # For getting translator's badges
            cursor.execute("SELECT badge_id FROM CICERON.D_AWARDED_BADGES WHERE id = (SELECT badgeList_id FROM CICERON.D_USERS WHERE id = %s LIMIT 1)", (row[5], ))
            badge_list = (",").join([ row[0] for row in cursor.fetchall() ])
            item['request_translatorBadgeList'] = badge_list

            # Add profile for translator

            translator_info = getProfile(conn, row[5])
            item['translatorInfo'] = translator_info if translator_info != None else ""

        result.append(item)

    return result

def complete_groups(conn, parameters, table, method, url_group_id=None, since=None, page=None):
    if method == "GET":
        cursor = conn.cursor()

        my_user_id = get_user_id(conn, session['useremail'])
        query = "SELECT id, text FROM CICERON.%s WHERE user_id = " % table
        query += "%s "
        if since != None:
            query += "AND registered_time < to_timestamp(%s) " % since
        query += "ORDER BY id DESC "
        if page != None:
            query += " OFFSET %d " % (( int(page)-1 ) * 20)

        cursor.execute(query, (my_user_id, ) )
        rs = cursor.fetchall()

        result = [ dict(id=row[0], name=row[1]) for row in rs ]
        return result

    elif method == "POST":
        cursor = conn.cursor()
        group_name = parameters['group_name']
        if group_name == "Documents":
            return -1

        my_user_id = get_user_id(conn, session['useremail'])

        new_group_id = get_new_id(conn, table)
        query = "INSERT INTO CICERON.%s VALUES " % table
        query += "(%s, %s, %s)"
        cursor.execute(query, (new_group_id, my_user_id, group_name))
        conn.commit()
        return group_name

    elif method == "PUT":
        cursor = conn.cursor()
        group_id = int(url_group_id)
        group_name = parameters['group_name']
        if group_name == u"Documents" or group_name == "Documents":
            return -1

        query = "UPDATE CICERON.%s " % table
        query += "SET text = %s WHERE id = %s "
        cursor.execute(query, (group_name, group_id) )
        conn.commit()
        return group_name

    elif method == 'DELETE':
        cursor = conn.cursor()

        group_id = int(url_group_id)
        group_text = get_text_from_id(conn, group_id, table)
        if group_text == "Documents":
            return -1
        elif group_text == None:
            return -2

        query = "DELETE FROM CICERON.%s " % table
        query += "WHERE id = %s"
        cursor.execute(query , (group_id, ))

        user_id = get_user_id(conn, session['useremail'])
        default_group_id = get_group_id_from_user_and_text(conn, user_id, "Documents", table)
        if table.find("TRANSLATOR") >= 0: col = 'translator_completed_group_id'
        else:                             col = 'client_completed_group_id'

        query_update_temp = "UPDATE CICERON.F_REQUESTS SET %(col)s = ? WHERE %(col)s = ?" % {'col':col}
        query_update = query_update_temp.replace("?", "%s")
        cursor.execute(query_update, (default_group_id, group_id))

        conn.commit()
        return group_id

def save_request(conn, parameters, str_request_id, result_folder):
    cursor = conn.cursor()

    request_id = int(str_request_id)
    new_translatedText = parameters.get("request_translatedText", None)
    new_comment = parameters.get("request_comment", None)
    new_tone = parameters.get("request_tone", None)

    cursor.execute("SELECT translatedText, comment_id, tone_id FROM CICERON.V_REQUESTS WHERE request_id = %s ", (request_id, ) )
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
            cursor.execute("INSERT INTO CICERON.D_TRANSLATED_TEXT (id, path, text) VALUES (%s,%s,%s)", (new_result_id, translatedText_path, new_translatedText))
            cursor.execute("UPDATE CICERON.F_REQUESTS SET translatedText_id = %s WHERE id = %s", (new_result_id, request_id))

    # Save new comment
    if new_comment != None:
        if comment_id != None:
            cursor.execute("UPDATE CICERON.D_COMMENTS SET text = %s WHERE id = %s", (new_comment, comment_id))
        else:
            comment_id = get_new_id(conn, "D_COMMENTS")
            cursor.execute("INSERT INTO CICERON.D_COMMENTS VALUES (%s,%s)", (comment_id, new_comment))
            cursor.execute("UPDATE CICERON.F_REQUESTS SET comment_id = %s WHERE id = %s", (comment_id, request_id))

    # Save new tone
    if new_tone != None:
        if tone_id != None:
            cursor.execute("UPDATE CICERON.D_TONES SET text = %s WHERE id = %s", (new_tone, tone_id))
            cursor.execute("UPDATE CICERON.F_REQUESTS SET tone_id = %s WHERE id = %s", (tone_id, request_id))
        else:
            tone_id = get_new_id(conn, "D_TONES")
            cursor.execute("INSERT INTO CICERON.D_TONES VALUES (%s,%s)", (tone_id, new_tone))
            cursor.execute("UPDATE CICERON.F_REQUESTS SET tone_id = %s WHERE id = %s", (tone_id, request_id))

    conn.commit()

def update_user_record(conn, client_id=None, translator_id=None):
    cursor = conn.cursor()
    if client_id is not None:
        cursor.execute("""UPDATE CICERON.D_USERS SET 
                numOfRequestPending = (SELECT count(id) FROM CICERON.F_REQUESTS WHERE status_id = 0 AND client_user_id = %s),
                numOfRequestOngoing = (SELECT count(id) FROM CICERON.F_REQUESTS WHERE status_id = 1 AND client_user_id = %s),
                numOfRequestCompleted = (SELECT count(id) FROM CICERON.F_REQUESTS WHERE status_id = 2 AND client_user_id = %s)
                WHERE id = %s """, (client_id, client_id, client_id, client_id))

    if translator_id is not None:
        cursor.execute("""UPDATE CICERON.D_USERS SET 
                numOfTranslationPending = (SELECT count(queue.id) FROM CICERON.F_REQUESTS fact LEFT OUTER JOIN CICERON.D_QUEUE_LISTS queue ON fact.queue_id = queue.id WHERE fact.status_id = 0 AND queue.user_id = %s ),
                numOfTranslationOngoing = (SELECT count(id) FROM CICERON.F_REQUESTS WHERE status_id = 1 AND ongoing_worker_id = %s ),
                numOfTranslationCompleted = (SELECT count(id) FROM CICERON.F_REQUESTS WHERE status_id = 2 AND ongoing_worker_id = %s )
                WHERE id = %s """, (translator_id, translator_id, translator_id, translator_id))

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
    cursor = conn.cursor()
    for user in user_ids:
        user_number = get_user_id(conn, user)
        cursor.execute("SELECT reg_key FROM CICERON.D_MACHINES WHERE user_id = %s AND is_push_allowed = true", (user_number, ) )
        client_infos = cursor.fetchall()

        # Gather registration IDs
        registration_keys.extend([ item[0] for item in client_infos ])

    notification = {
            "title": message.get('title'),
            "text": message.get('detail')
        }

    # Send one message to devices at once
    if len(registration_keys) > 0:
        response = gcm_obj.send(registration_keys, message,
                    collapse_key=collapse_key,
                    delay_while_idle=delay_while_idle,
                    time_to_live=time_to_live,
                    restricted_package_name=restricted_package_name,
                    dry_run=dry_run,
                    notification=notification
                    )

    return response

def send_mail(mail_to, subject, message, mail_from='no-reply@ciceron.me'):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    content = MIMEText(message, 'html', _charset='utf-8')
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'Ciceron team <%s>' % mail_from
    msg['To'] = str(mail_to)
    msg.attach(content)

    print msg
    a = smtplib.SMTP('smtp.worksmobile.com:587')
    a.starttls()
    a.login('no-reply@ciceron.me', 'Ciceron01!')
    a.sendmail('no-reply@ciceron.me', str(mail_to), msg.as_string())
    a.quit()

def store_notiTable(conn, user_id, noti_type_id, target_user_id, request_id):
    cursor = conn.cursor()
    new_noti_id = get_new_id(conn, "F_NOTIFICATION")
    # The query below is original
    query = "INSERT INTO CICERON.F_NOTIFICATION VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP,false,false)"
    # The query below is that mail alarm is forcefully turned off
    #query = "INSERT INTO F_NOTIFICATION VALUES (?,?,?,?,CURRENT_TIMESTAMP,1)"
    cursor.execute(query, (new_noti_id, user_id, noti_type_id, target_user_id, request_id) )
    conn.commit()

def pick_random_translator(conn, number, from_lang, to_lang):
    cursor = conn.cursor()

    query = """WITH translators AS (
                   SELECT distinct usr.id usr_id FROM CICERON.D_USERS usr
        JOIN CICERON.V_TRANSLATABLE_LANGUAGES trans ON usr.id = trans.user_id
        JOIN CICERON.V_TRANSLATABLE_LANGUAGES trans2 ON usr.id = trans2.user_id
        WHERE (usr.mother_language_id = %s AND trans.translatable_language_id = %s)
           OR (trans.translatable_language_id = %s AND usr.mother_language_id = %s)
           OR (trans.translatable_language_id = %s AND trans2.translatable_language_id = %s)
           )
           SELECT distinct usr_id FROM translators OFFSET FLOOR(RANDOM() * (SELECT COUNT(*) FROM translators)) LIMIT %s """
    cursor.execute(query, (from_lang, to_lang, from_lang, to_lang, from_lang, to_lang, number, ))
    result = cursor.fetchall()

    return result

def string2Date(string):
    try:
        return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
    except:
        return datetime.strptime(string, "%Y-%m-%d")

def getRoutingAddressAndAlertType(conn, user_id, request_id, noti_type):
    cursor = conn.cursor()
    requesterNoti = [7, 8, 9, 10, 11, 12, 13]
    translatorNotiType = [1, 2, 3, 4, 5, 6]

    HOST = ""
    if os.environ.get('PURPOSE') == 'PROD':
        HOST = 'http://ciceron.me'
    else:
        HOST = 'http://ciceron.xyz'

    isAlert = None
    alertType = None
    link = None

    queryGetStatus = "SELECT is_paid, status_id, ongoing_worker_id FROM CICERON.F_REQUESTS WHERE id = %s "
    cursor.execute(queryGetStatus, (request_id,) )
    row = cursor.fetchone()
    is_paid = row[0]
    status_id = row[1]
    translator_id = row[2]

    if status_id in [-1, -2]:
        # Deleted or outdated request
        isAlert = True
        alertType = 0 # Not existing
        link = None

    elif status_id == 0 and is_paid == 1:
        # Ticket in stoa
        isAlert = False
        alertType = None
        link = '%s/%s/%d' % (HOST, 'stoa', request_id)

    elif status_id in [1, 2] and is_paid == 1 and noti_type in translatorNotiType and user_id != translator_id:
        # Not my ticket / ongoing, closed ticket
        isAlert = True
        alertType = 1 # Cannot access
        link = None

    elif status_id == 1 and is_paid == 1 and noti_type in translatorNotiType and user_id == translator_id:
        # My ongoing ticket / Expected due
        isAlert = False
        alertType = None
        link = '%s/%s/%d' % (HOST, 'translating', request_id)
        
    elif status_id == 2 and is_paid == 1 and noti_type in translatorNotiType and user_id == translator_id:
        isAlert = False
        alertType = None
        link = '%s/%s/%d' % (HOST, 'activity', request_id)

    elif status_id == 1 and is_paid == 1 and noti_type in requesterNoti:
        # My ongoing ticket / Expected due
        isAlert = False
        alertType = None
        link = '%s/%s/%d' % (HOST, 'processingrequests', request_id)
        
    elif status_id == 2 and is_paid == 1 and noti_type in requesterNoti:
        isAlert = False
        alertType = None
        link = '%s/%s/%d' % (HOST, 'donerequests', request_id)

    elif noti_type in (14, 15):
        isAlert = False
        alertType = None
        link = '%s/%s' % (HOST, 'profile')

    return (isAlert, alertType, link)

def get_noti_data(conn, noti_type, user_id, request_id, optional_info=None):
    HOST = ""
    if os.environ.get('PURPOSE') == 'PROD':
        HOST = 'http://ciceron.me'
    else:
        HOST = 'http://ciceron.xyz'

    user_name = get_user_name(conn, user_id)

    message = {
         "notiType": None,
         "host": HOST,
         "user": user_name,
         "link": None,
         "expected": None,
         "hero": None,
         "new_due": None,
         "request_id": request_id,
         "link": getRoutingAddressAndAlertType(conn, user_id, request_id, noti_type)
         }

    if noti_type == 1:
        message["notiType"] = 1
        message["title"] = "New request!"
        message['detail'] = "New ticket is waiting for your help!"

    elif noti_type == 2:
        message["notiType"] = 2
        message["title"] = "When could you finish?"
        message['detail'] = "Inform your deadline to the client!"

    elif noti_type == 3:
        message["notiType"] = 3
        message["title"] = "Check client's feedback :)"
        message['detail'] = "Client left a feedback for your help:) Please check it!"
            
    elif noti_type == 4:
        message["notiType"] = 4
        message["title"] = "Deadline exceeded :("
        message['detail'] = "Deadline of your ticket has just exceeded. Client will decide how to deal with."

    elif noti_type == 5:
        message["notiType"] = 5
        message["new_due"] = optional_info.get('new_due')
        message["title"] = "You can work for your ticket more!"
        message['detail'] = "Client has just exteneded the deadline! Please be strict the deadline for this time :)"

    elif noti_type == 6:
        message["notiType"] = 6
        message["title"] = "No expected deadline :("
        message['detail'] = "Your ticket has just been put back into stoa due to no answer of deadline :( Please make sure to answer deadline until one third of deadline."

    elif noti_type == 7:
        message["notiType"] = 7
        message['hero'] = get_user_name(conn, optional_info.get('hero'))
        message["title"] = "Hero comes!"
        message['detail'] = "Hero has just started working for your ticket!"

    elif noti_type == 8:
        message["notiType"] = 8
        message["expected"] = str(optional_info.get('expected')) if optional_info.get('expected') != None else None
        message["title"] = "Check expected deadline"
        message['detail'] = "Hero thinks that your ticket can be finished by XX:XX:XX"

    elif noti_type == 9:
        message["notiType"] = 9
        message["hero"] = get_user_name(conn, optional_info.get('hero'))
        message["title"] = "Hero gave up translation :("
        message['detail'] = "Hero checked your ticket but he/she gave up translating."

    elif noti_type == 10:
        message["notiType"] = 10
        message["title"] = "No expected deadline from hero :("
        message['detail'] = "Hero didn't answer when the ticket could be finished. Your request is put into stoa."

    elif noti_type == 11:
        message["notiType"] = 11
        message["title"] = "Translation complete!"
        message['detail'] = "Your ticket has just been finished translating! Please rate the translation queality of your ticket!"

    elif noti_type == 12:
        message["notiType"] = 12
        message["title"] = "Deadline exceeded :("
        message['detail'] = "Your hero didn't finish your ticket yet."

    elif noti_type == 13:
        message["notiType"] = 13
        message["title"] = "No hero for your ticket :("
        message['detail'] = "No hero comes for your ticket. You may keep posting in stoa, or delete the ticket."

    elif noti_type == 15:
        message["notiType"] = 15
        message["title"] = "Point returned :)"
        message['detail'] = "Your points has just paid back to your account!"

    return message

def send_noti_suite(gcm_server, conn, user_id, noti_type_id, target_user_id, request_id, optional_info=None):
    store_notiTable(conn, user_id, noti_type_id, target_user_id, request_id)
    message_dict = get_noti_data(conn, noti_type_id, user_id, request_id, optional_info=optional_info)
    regKeys_oneuser = get_device_id(conn, user_id)
    print "Send push to the device: %s" % regKeys_oneuser
    if len(regKeys_oneuser) > 0:
        gcm_noti = gcm_server.send(regKeys_oneuser, "Ciceron push", notification=message_dict)
        print str(gcm_noti.responses)

def signUpQuick(conn, email, hashed_password, name, mother_language_id, nationality_id=None, residence_id=None, external_service_provider=[]):
    # Duplicate check
    cursor = conn.cursor()
    cursor.execute("select id from CICERON.D_USERS where email = %s", (email, ))
    check_data = cursor.fetchall()
    if len(check_data) > 0:
        # Status code 400 (BAD REQUEST)
        # Description: Duplicate ID
        return 412

    if '@' not in email:
        return 417

    # Insert values to D_USERS
    user_id = get_new_id(conn, "D_USERS")

    print "New user id: %d" % user_id
    cursor.execute("""INSERT INTO CICERON.D_USERS
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (user_id,
             email,
             name,
             mother_language_id,
             False,
             None,
             None,
             0,
             0,
             0,
             0,
             0,
             0,
             None,
             "nothing",
             0,
             nationality_id,
             residence_id,
             0.7))

    cursor.execute("INSERT INTO CICERON.PASSWORDS VALUES (%s,%s)",
        (user_id, hashed_password))
    cursor.execute("INSERT INTO CICERON.REVENUE VALUES (%s,%s)",
        (user_id, 0))
    cursor.execute("INSERT INTO CICERON.RETURN_POINT VALUES (%s,%s)",
        (user_id, 0))

    if 'facebook' in external_service_provider:
        new_facebook_id = get_new_id(conn, "D_FACEBOOK_USERS")
        cursor.execute("INSERT INTO CICERON.D_FACEBOOK_USERS VALUES (%s,%s,%s) ",
                (new_facebook_id, email, user_id))

    conn.commit()

    return 200

def commonPromotionCodeChecker(conn, user_id, code):
    # return: (val1, val2, message)
    #          val1: is valid code? (codeType)
    #          val2: How much?
    #          message: Message
    cursor = conn.cursor()
    query_commonPromotionCode= """
        SELECT id, benefitPoint, expireTime FROM CICERON.PROMOTIONCODES_COMMON WHERE text = %s """
    cursor.execute(query_commonPromotionCode, (code, ))
    ret = cursor.fetchone()

    if ret == None:
        return (3, 0, "There is no promo code matched.")

    code_id = ret[0]
    benefitPoint = ret[1]
    expireTime = string2Date(ret[2])

    if expireTime < datetime.now():
        return (2, 0, "This promo code is expired.")

    query_userCheck = """
        SELECT count(*) FROM CICERON.USEDPROMOTION_COMMON WHERE id = %s AND user_id = %s """

    cursor.execute(query_userCheck, (code_id, user_id))
    cnt = cursor.fetchone()[0]

    if cnt > 0:
        return (1, 0, "You've already used this code.")

    else:
        return (0, benefitPoint, "You may use this code.")

def commonPromotionCodeExecutor(conn, user_id, code):
    cursor = conn.cursor()
    query_searchPromoCodeId = """
        SELECT id FROM CICERON.PROMOTIONCODES_COMMON WHERE text = %s """
    cursor = conn.execute(query_searchPromoCodeId, (code ))
    code_id = cursor.fetchone()[0]
    query_commonPromotionCodeExeutor = """
        INSERT INTO CICERON.USEDPROMOTION_COMMON VALUES (%s,%s)"""
    cursor.execute(query_commonPromotionCodeExeutor, (code_id, user_id))
    conn.commit()

def individualPromotionCodeChecker(conn, user_id, code):
    # return: (val1, val2)
    #          val1: is valid code?
    #          val2: How much?
    cursor = conn.cursor()
    query_individualPromotionCode= """
        SELECT benefitPoint, expireTime, is_used FROM CICERON.PROMOTIONCODES_USER WHERE user_id = %s AND text = %s """
    cursor.execute(query_individualPromotionCode, (user_id, code))
    ret = cursor.fetchone()

    if ret == None:
        return (3, 0, "There is no promo code matched.")

    benefitPoint = ret[0]
    expireTime = string2Date(ret[1])
    isUsed = ret[2]

    if expireTime < datetime.now():
        return (2, 0, "This promo code is expired.")

    if isUsed == 1:
        return (1, 0, "You've already used this code.")

    else:
        return (0, benefitPoint, "You may use this code.")

def individualPromotionCodeExecutor(conn, user_id, code):
    cursor = conn.cursor()
    query_commonPromotionCodeExeutor = """
        UPDATE CICERON.PROMOTIONCODES_USER SET is_used = true WHERE user_id = %s AND text = %s """
    cursor.execute(query_commonPromotionCodeExeutor, (user_id, code))
    conn.commit()

def payment_start(conn, pay_by, pay_via, request_id, total_amount, user_id, host_ip,
        use_point=0, promo_type='null', promo_code='null', is_additional='false'):

    cursor = conn.cursor()

    # Point deduction
    if use_point > 0:
        # Check whether use_point exceeds or not
        cursor.execute("SELECT amount FROM CICERON.RETURN_POINT WHERE id = %s", (user_id, ))
        current_point = float(cursor.fetchall()[0][0])
        print "Current_point: %f" % current_point
        print "Use_point: %f" % use_point
        print "Diff: %f" % (current_point - use_point)

        if current_point - use_point < -0.00001:
            return 'point_exceeded_than_you_have', None, current_point

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
            "return_url": "%s:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=success&user_id=%s&pay_amt=%.2f&pay_by=%s&use_point=%.2f&promo_type=%s&promo_code=%s&is_additional=%s" % (host_ip, request_id, session['useremail'], amount, pay_by, use_point, promo_type, promo_code, is_additional),
            "cancel_url": "%s:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=fail&user_id=%s&pay_amt=%.2f&pay_by=%s&use_point=%.2f&promo_type=%s&promo_code=%s&is_additional=%s" % (host_ip, request_id, session['useremail'], amount, pay_by, use_point, promo_type, promo_code, is_additional)},
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

        red_link = "%s:5000/api/user/requests/%d/payment/postprocess?pay_via=paypal&status=success&user_id=%s&pay_amt=%.2f&pay_by=%s&use_point=%.2f&promo_type=%s&promo_code=%s&is_additional=%s" % (host_ip, request_id, session['useremail'], amount, pay_by, use_point, promo_type, promo_code, is_additional)
        if bool(rs) is True:
            return 'paypal_success', paypal_link, None

        else:
            return 'paypal_error', None, None

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
            'return_url': "%s:5000/api/user/requests/%d/payment/postprocess?pay_via=alipay&status=success&user_id=%s&pay_amt=%.2f&pay_by=%s&use_point=%.2f&promo_type=%s&promo_code=%s&is_additional=%s" % (host_ip, request_id, session['useremail'], amount, pay_by, use_point, promo_type, promo_code, is_additional)
            }

        provided_link = None
        if pay_by == 'web':
            provided_link = alipay_obj.create_forex_trade_url(**params)
        elif pay_by == 'mobile':
            provided_link = alipay_obj.create_forex_trade_wap_url(**params)

        return 'alipay_success', provided_link, None

    elif pay_via == "point_only":
        cursor.execute("SELECT amount FROM CICERON.RETURN_POINT WHERE id = %s", (user_id, ))
        current_point = float(cursor.fetchall()[0][0])

        amount = 0
        if current_point - use_point < -0.00001:
            return make_response(json.jsonify(
                message="You requested to use your points more than what you have. Price: %.2f, Your purse: %.2f" % (total_amount, current_point)), 402)
        else:
            amount = current - use_point

        cursor.execute("UPDATE CICERON.RETURN_POINT SET amount = amount - %s WHERE id = %s", (use_point, user_id, ))

        if is_additional == 'false':
            query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_paid = %s WHERE id = %s"
        else:
            query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_additional_points_paid = %s WHERE id = %s"
        cursor.execute(query_setToPaid, (True, request_id, ))
        g.db.commit()

        if pay_by == "web":
            return 'point_success', None, None
        elif pay_by == "mobile":
            return 'point_success', None, None

def payment_postprocess(conn, pay_by, pay_via, request_id, user_id, is_success, amount,
        use_point=0, promo_type='null', promo_code='null', is_additional='false'):

    cursor = conn.cursor()

    # Point deduction
    if use_point > 0:
        cursor.execute("UPDATE CICERON.return_point SET amount = amount - %s WHERE id = %s", (use_point, user_id, ))

    if pay_via == 'paypal':
        payment_id = request.args['paymentId']
        payer_id = request.args['PayerID']
        if is_success:
            payment_info_id = get_new_id(g.db, "PAYMENT_INFO")
            # Paypal payment exeuction
            payment = paypalrestsdk.Payment.find(payment_id)
            payment.execute({"payer_id": payer_id})

            if is_additional == 'false':
                query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_paid = %s WHERE id = %s"
            else:
                query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_additional_points_paid = %s WHERE id = %s"
            cursor.execute(query_setToPaid, (True, request_id, ))

            # Payment information update
            cursor.execute("INSERT INTO CICERON.PAYMENT_INFO (id, request_id, client_id, payed_via, order_no, pay_amount, payed_time) VALUES (%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)",
                    (payment_info_id, request_id, user_id, "paypal", payment_id, amount, ))

            g.db.commit()
            #return redirect("success")

    elif pay_via == "alipay":
        if is_success:
            # Get & store order ID and price
            payment_info_id = get_new_id(g.db, "PAYMENT_INFO")

            if is_additional == 'false':
                query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_paid = %s WHERE id = %s"
            else:
                query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_additional_points_paid = %s WHERE id = %s"
            cursor.execute(query_setToPaid, (True, request_id, ))

            # Payment information update
            cursor.execute("INSERT INTO CICERON.PAYMENT_INFO (id, request_id, client_id, payed_via, order_no, pay_amount, payed_time) VALUES (%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)",
                    (payment_info_id, request_id, user_id, "alipay", None, amount))

            g.db.commit()

    if promo_type == 'common':
        commonPromotionCodeExecutor(g.db, user_id, promo_code)
    elif promo_type == 'indiv':
        individualPromotionCodeExecutor(g.db, user_id, promo_code)

    # Notification for normal request
    cursor.execute("SELECT original_lang_id, target_lang_id FROM CICERON.F_REQUESTS WHERE id = %s ", (request_id, ))
    record = cursor.fetchone()
    if record is None or len(record) == 0:
        print "No record for this request. Request ID: %d" % request_id
        return 'no_record'

    original_lang_id = record[0]
    target_lang_id = record[1]

    rs = pick_random_translator(g.db, 10, original_lang_id, target_lang_id)
    for item in rs:
        store_notiTable(g.db, item[0], 1, None, request_id)
        regKeys_oneuser = get_device_id(g.db, item[0])

        message_dict = get_noti_data(g.db, 1, item[0], request_id)
        if len(regKeys_oneuser) > 0:
            gcm_noti = gcm_server.send(regKeys_oneuser, message_dict)

    if pay_by == "web":
        return 'payment_success', None, None
    elif pay_by == "mobile":
        return 'payment_success', None, None

def approve_negoPoint(conn, request_id, translator_id, user_id):
    cursor = conn.cursor()

    if translator_id == -1:
        return 406

    # 1. Get diff_amount
    # 1.1. Get current point of the ticket and queue ID
    query_getCurPointAndQueueID = "SELECT points, queue_id, status_id FROM CICERON.F_REQUESTS WHERE id = %s AND client_user_id = %s"
    cursor.execute(query_getCurPointAndQueueID, (request_id, user_id, ))
    rs = cursor.fetchone()
    if rs is None or len(rs) == 0:
        return 406

    current_point = rs[0]
    queue_id = rs[1]
    status_id = rs[2]

    if status_id != 0:
        return 402

    # 1.2. Get suggested point
    query_getSuggestedPoint = "SELECT nego_price FROM CICERON.D_QUEUE_LISTS WHERE id = %s AND request_id = %s AND user_id = %s"
    cursor.execute(query_getSuggestedPoint, (queue_id, request_id, translator_id, ))
    rs = cursor.fetchone()
    if rs is None or len(rs) == 0:
        return 406

    nego_point = rs[0]
    diff_point = nego_point - current_point
    if diff_point < 0:
        return 409

    # 2. Set the queued hero to your hero, status = 1, is_need_additional_points = true, is_additional_points_paid = false
    query_updateHero = "UPDATE CICERON.F_REQUESTS SET is_need_additional_points = true, ongoing_worker_id = %s, additional_points= %s, is_additional_points_paid=false, status_id = 1 WHERE id = %s"
    cursor.execute(query_updateHero, (translator_id, diff_point, request_id, ))

    conn.commit()
    return 200

def logTransfer(conn):
    cursor = conn.cursor()

    query_getmax = "SELECT MAX(id) FROM CICERON.TEMP_ACTIONS_LOG"
    cursor.execute(query_getmax)
    max_id = cursor.fetchone()[0]

    query_insertLog = """INSERT INTO CICERON.USER_ACTIONS (id, user_id, method, api, log_time, ip_address)
        SELECT id, user_id, method, api, log_time, ip_address
        FROM CICERON.TEMP_ACTIONS_LOG
        WHERE id <= %s"""
    cursor.execute(query_insertLog, (max_id, ))
    conn.commit()
