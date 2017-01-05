# -*- coding: utf-8 -*-

import hashlib, codecs, os, random, string, sys, paypalrestsdk, logging
from flask import make_response, json, g, session, request, current_app
from datetime import datetime, timedelta
from functools import wraps
from iamport import Iamport

try:
    from .requestwarehouse import Warehousing
except:
    from requestwarehouse import Warehousing

super_user = ["pjh0308@gmail.com", "happyhj@gmail.com", "admin@ciceron.me"]

"""
매우 자주 사용하게 될 라이브러리 함수
get_user_id(): 이메일 주소를 넣으면 user_id를 받을 수 있음.
get_new_id(): 해당 테이블에서 사용하는 sequence
parameter_to_bool(): parameter가 boolean 타입이면 True/False로 parsing해줌

@login_required: 세션을 먼저 감지하여 로그인이 되어 있는지 살펴본다.
strict_translator_checker: 해당 티켓에 로그인한 번역가가 번역 가능한지 언어 체크
translationAuthChecker: 로그인한 번역가가 해당 티켓의 번역가인지 알아봄
clientAuthChecker: 로그인한 의뢰인이 해당 티켓의 의뢰인인지 알려줌

json_from_V_REQUESTS: 쿼리한 결과를 python dict로 만들어줌.
update_user_record: 유저 통계 업데이트
parse_request: request를 parsing하여 dictionary로 만들어줌. www-urlencode이든, form-data이튼, application/json이든 모두 감별함

string2Data: 문자열 날짜/시간 데이터를 Datetime object로 만들어줌
"""

def get_hashed_password(password, salt=None):
    """
    비밀번호 hashing 라이브러리. Salt 넣으면 그것도 반영하여 만들어줌
    """
    hash_maker = hashlib.sha256()

    if salt is None:
        hash_maker.update(password)
    else:
        hash_maker.update(salt.encode() + password + salt.encode())

    return hash_maker.hexdigest()

def random_string_gen(size=6, chars=string.letters + string.digits):
    """
    무작위 string 만들어줌. 길이 조절도 가능함
    """
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
    """
    text와 테이블 이름을 넣으면 입력한 text의 ID를 찾아줌
    """
    query = "SELECT id from CICERON.%s WHERE text = " % table
    query += "%s"
    cursor = conn.cursor()
    cursor.execute(query, (text, ))
    rs = cursor.fetchall()
    if len(rs) == 0: result = -1
    else:            result = int(rs[0][0])
    return result

def get_user_id(conn, text_id):
    """
    이메이을 넣으면 해당 사용자의 ID를 찾아줌
    email은 indexing 해놨기때문에 성능상의 큰 문제는 없을것임
    """
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
    """
    User ID를 넣으면 email을 찾아주는 함수인데 얼마나 사용할진 모르겠음
    """
    cursor = conn.cursor()
    cursor.execute("SELECT email from CICERON.D_USERS WHERE id = %s",
            [num_id])
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

def get_user_name(conn, num_id):
    """
    User ID를 넣으면 유저 이름을 찾아줌. 주로 이메일 날릴때 Dear xxx를 채우기 위하여 새용
    """
    cursor = conn.cursor()
    cursor.execute("SELECT name from CICERON.D_USERS WHERE id = %s",
            [num_id])
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

def get_text_from_id(conn, id_num, table):
    """
    ID를 넣으면 해당 테이블의 text를 찾아줌
    """
    query = "SELECT text from CICERON.%s WHERE id = " % table
    query += "%s"
    cursor = conn.cursor()
    cursor.execute(query, (id_num, ))
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

def get_new_id(conn, table):
    """
    테이블에서 사용하는 sequece에서 새 ID를 따줌.
    이 기능을 사용하려면 seqeunce 이름을 SEQ_<table_name>으로 해야 함 (ex CICERON.SEQ_F_REQUESTS)
    """
    cursor = conn.cursor()
    cursor.execute("SELECT nextval('CICERON.SEQ_%s') " % table)
    current_id_list = cursor.fetchone()
    return current_id_list[0]

def get_path_from_id(conn, id_num, table):
    query = "SELECT path from CICERON.%s WHERE id = " % table
    query += "%s"
    cursor = conn.cursor()
    cursor.execute(query, (id_num, ))
    rs = cursor.fetchall()
    if len(rs) == 0: result = None
    else:            result = str(rs[0][0])
    return result

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
    """
    네고 기능때문에 points 자체로는 총액이 되지 않기 때문에 nego_price와 더해줘야 한다.
    이 때, 총합을 계산하는 라이브러리
    """
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
    """
    API 실행 전, 해당 IP에서 1초에 100번 이상 실행되면 30분동안 접속 차단한다.
    그리고 차단하지 않은 IP는 임시 테이블에 로그를 남겨 나중에 분석 자료로 이용한다.

    그리고 현재 로그를 쌓는 곳은 임시테이블이고, 30분에 한 번씩 Agent가 돌아 로그를 영구보관소로 옮긴다.
    """
    cursor = conn.cursor()

    if session.get('useremail') != None:
        user_id = get_user_id(conn, session['useremail'])
    else:
        user_id = 0

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
            AND CURRENT_TIMESTAMP BETWEEN time_from AND time_to
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
    cursor.execute(query_insertLog, (user_id, method, api_endpoint, ip_address, ))
    conn.commit()

    return is_OK

def apiURLOrganizer(api_base, **kwargs):
    basic = api_base + '?'
    param = []
    for key, value in kwargs.items():
        param.append('%s=%s' % (key, value))

    query = '&'.join(param)

    return basic + query

def login_required(f):
    """
    DDOS 공격 검출기로 해당 IP가 블랙 리스트에 올라갔는지, 그리고 블랙 리스트에 올려야 하는지 살펴본다.
    아무 이상이 없다면 로그인이 되어 있는지 세션 설정값을 본다.
    """
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
    """
    Admin으로 로그인되어 있는지 체크한다.
    """
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
            print(e)
            g.db.rollback()
            return make_response(json.jsonify(message=str(e)),500)

    return decorated_function

def translator_checker(f):
    """
    번역가 권한이 있는 유저인지 체크한다.
    """
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

def translator_checker_plain(conn, email):
    """
    위와 같은 일을 하나, 이건 decorator가 아니다.
    """
    cursor = g.db.cursor()
    cursor.execute("SELECT is_translator FROM CICERON.D_USERS WHERE email = %s", (email, ) )
    rs = cursor.fetchone()

    if rs is None or len(rs) == 0:
        return False
    else:
        return rs[0]

def strict_translator_checker(conn, user_id, request_id):
    """
    번역가가 해당 의뢰를 번역할 수 있는지 체크
        1. 해당 의뢰의 언어쌍 조사
        2. 모국어와 구사가능언어를 수집하여 두 언어 모두 구사가능 언어인지 살펴봄.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT is_translator, mother_language_id, other_language_list_id FROM CICERON.D_USERS WHERE id = %s ", (user_id, ))
    rs = cursor.fetchone()
    if rs is None or len(rs) == 0 or rs[0] == 0 or rs[0] == 'False' or rs[0] == 'false':
        return False

    # Get language list
    mother_language_id = rs[1]

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
    rs = cursor.fetchone()
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

def translationAuthChecker(conn, user_id, request_id, status_id):
    """
    실제 해당 번역가 유저가 번역하고 있는 의뢰인지 살펴봄
    """
    cursor = conn.cursor()
    query = """SELECT count(*) FROM CICERON.V_REQUESTS WHERE status_id = %s AND request_id = %s AND ongoing_worker_id = %s """
    cursor.execute(query, (status_id, request_id, user_id, ))
    count = cursor.fetchone()[0]
    if count == 0:
        return False
    else:
        return True

def clientAuthChecker(conn, user_id, request_id, status_id):
    """
    실제 자신이 의뢰한 티켓인지 살펴봄
    """
    cursor = g.db.cursor()

    query = """SELECT count(*) FROM CICERON.V_REQUESTS WHERE status_id = %s AND request_id = %s AND client_user_id = %s """
    cursor.execute(query, (status_id, request_id, user_id, ))
    count = cursor.fetchone()[0]
    if count == 0:
        return False
    else:
        return True

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

def orderNoGenerator(conn):
    """
    Iamport 방식으로 결제할 때에는 주문번호를 만들어 주지 않기 때문에 우리가 직접 만들어야 한다.
    주문번호 형식은 YYYYMMDDxxxx (ex 20160716abcd) 방식으로 한다.
    """
    cursor = conn.cursor()
    order_no = None

    for _ in range(1000):
        order_no = datetime.strftime(datetime.now(), "%Y%m%d") + random_string_gen(size=4)
        cursor.execute("SELECT count(*) FROM CICERON.PAYMENT_INFO WHERE order_no = %s", (order_no, ))
        cnt = cursor.fetchone()[0]

        if cnt == 0:
            break
        else:
            continue

    return order_no

def getProfile(conn, user_id, rate=1, price=None):
    """
    프로파일 조회
    D_USERS와 그 밖에 필요한 정보들을 JSON 형태로 보여줌

    옛날 기획에 뱃지도 보여주자 했는데 현재는 중단된 상태.
    """
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
        user_profilePicPath=            str(userinfo[6]) if userinfo[6] != None else 'img/anon.jpg',
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
    """
    의뢰에 관련된 모든 정보를 JSON 형태로 보여줌. 권한이랑 포인트 등등 때문에 적잖이 로직이 복잡하다.

        1. return_rate: 기본 0.7. 번역가는 개별적으로 환급 비율을 따로 설정할 수 있다. 
          의뢰인이 가격을 10이라고 설정했어도, 번역가에게는 받아갈 돈 7로 표시하기 위하여 쿼리질을 한다.
        2. CICERON.V_QUEUE_LISTS 에서 해당 티켓에 네고를 건 사용자 프로필들을 조회해온다.
        3. 글자수 및 단어수 계산
        4. 그 밖에.. 번역가와 의뢰인, 단문 번역과 일반 번역, 그리고 번역 status에 따라 보여주고 가려야 할 내용 통제를 로직으로 수행한다.
    """
    result = []
    cursor = g.db.cursor()

    # Return rate
    query_returnRate = "SELECT return_rate FROM CICERON.D_USERS WHERE email = %s"
    cursor.execute(query_returnRate, (session['useremail'], ))
    ret_returnRate = cursor.fetchone()

    return_rate = None
    if ret_returnRate is not None and len(ret_returnRate) > 0:
        return_rate = ret_returnRate[0]

    warehouse = Warehousing(conn)

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
        #request_id = row[30]
        text_for_counting = warehouse.restoreRequestByString(row[0])
        if len(text_for_counting) == 0:
            num_of_words = 0
            num_of_letters = 0
        else:
            num_of_letters = len(text_for_counting.decode('utf-8').replace(' ', ''))
            num_of_words = len(text_for_counting.decode('utf-8').split(' '))

        main_text = text_for_counting

        item = dict(
                request_id=row[0],
                request_clientId=row[2],
                request_clientName=row[3],
                request_clientPicPath=row[4] if row[4] is not None else 'img/anon.jpg',
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
                request_translatorPicPath=row[8] if row[8] is not None else 'img/anon.jpg',
                request_translatorBadgeList="",  # For marking
                request_translatedText=None, # For marking
                request_translatorComment=row[40],
                request_translatedTone=row[42],
                request_submittedTime=int(row[26].strftime("%s")) * 1000 if row[26] != None else None,
                request_feedbackScore=row[54],
                request_title=None, # For marking
                request_isI18n=row[59],
                request_isMovie=row[60],
                request_isGroupRequest=row[61],
                request_isDocx=row[62],
                request_isPublic=row[63],
                request_resellPrice=row[64],
                request_isCopyrightChecked=row[65],
                request_numberOfMemberInGroup=row[66],
                request_currentNumberOfMember=row[67],
                request_isCopyrightConfirmed=row[68]
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
                item['request_translatedText'] = main_text
            else:
                item['request_context'] = row[38]
                item['request_text'] = None
                item['request_soundPath'] = None
                item['request_photoPath'] = None
                item['request_filePath'] = None

        elif purpose in ["pending_client", "pending_translator"]:
            # Show context if normal request, or show main text
            if row[17] == True: # True
                item['request_context'] = main_text
                item['request_translatedText'] = warehouse.restoreTranslationByString(row[0])
            else:
                item['request_context'] = row[38]

        elif purpose == "ongoing_translator":
            if row[17] == True:
                item['request_context'] = main_text
                item['request_text'] = main_text
            else:
                item['request_context'] = row[38]

            item['request_translatedText'] = warehouse.restoreTranslationByString(row[0])

        elif purpose in ["complete_translator", "complete_client"]:
            if row[17] == True:
                item['request_context'] = main_text
                item['request_text'] = main_text

            else:
                item['request_context'] = row[38]

            item['request_translatedText'] = warehouse.restoreTranslationByString(row[0])

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
    """
    그룹 조회, 생성, 그룹명 수정, 및 삭제 라이브러리
    기능은 똑같지만 번역가와 의뢰인계정이 쓰는 테이블 이름이 다르기에 라이브러리화 시키고 테이블 이름을 받아 동일한 로직을 사용할 수 있도록 구성하였다.
    """
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
        if group_name == "Incoming" or group_name == 'Incoming':
            return -1

        my_user_id = get_user_id(conn, session['useremail'])

        query_count = "SELECT count(*) FROM CICERON.%s " % table
        query_count += "WHERE user_id = %s AND text = %s"
        cursor.execute(query_count, (my_user_id, group_name, ))
        cnt = cursor.fetchone()[0]
        if cnt > 0:
            return -1

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
        if group_name == "Incoming" or group_name == "Incoming":
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
        if group_text == "Incoming" or group_text == 'Incoming':
            return -1
        elif group_text == None:
            return -2

        query = "DELETE FROM CICERON.%s " % table
        query += "WHERE id = %s"
        cursor.execute(query , (group_id, ))

        user_id = get_user_id(conn, session['useremail'])
        default_group_id = get_group_id_from_user_and_text(conn, user_id, "Incoming", table)
        if table.find("TRANSLATOR") >= 0: col = 'translator_completed_group_id'
        else:                             col = 'client_completed_group_id'

        query_update_temp = "UPDATE CICERON.F_REQUESTS SET %(col)s = ? WHERE %(col)s = ?" % {'col':col}
        query_update = query_update_temp.replace("?", "%s")
        cursor.execute(query_update, (default_group_id, group_id))

        conn.commit()
        return group_id

def save_request(conn, parameters, str_request_id):
    """
    번역을 완료하면서 마지막 코멘트, 글의 톤 등을 저장하는 데 쓰이는 라이브러리이다.
    """
    cursor = conn.cursor()

    request_id = int(str_request_id)
    new_comment = parameters.get("request_comment", None)
    new_tone = parameters.get("request_tone", None)

    cursor.execute("SELECT translatedText, comment_id, tone_id FROM CICERON.V_REQUESTS WHERE request_id = %s ", (request_id, ) )
    rs = cursor.fetchall()

    translatedText_path = rs[0][0]
    comment_id = rs[0][1]
    tone_id = rs[0][2]

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
    """
    application/json, application/x-wwwurlencode, multipart/form-data 같은 다양한 형식에서도
    POST request를 python dict 형태로 나타낼 수 있게 만들어주는 라이브러리이다.
    """
    if len(req.form) == 0 and len(req.files) == 0:
        parameter_list = req.get_json()
        if parameter_list != None:
            result = dict()

            for key, value in parameter_list.items():
                result[key] = value

            return result
        
        else:
            return dict()

    else:
        if len(req.form) != 0:
            result = dict()
            for key, value in req.form.items():
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

    """
    푸시 알람 날려주는 API이다. 근데 잘 안먹힌다. 이유는 모르겠다. 경험자가 필요하다.
    """
    
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

def get_gmail_service():
    #from oauth2client import client
    #from oauth2client import tools
    #from oauth2client.file import Storage
    #import httplib2
    #CLIENT_SECRET_FILE = 'client_secret.json'
    #APPLICATION_NAME = 'SexyCookie'

    #home_dir = os.path.expanduser('~')
    #credential_dir = os.path.join(home_dir, '.credentials')
    #if not os.path.exists(credential_dir):
    #    os.makedirs(credential_dir)
    #credential_path = os.path.join(credential_dir,
    #                               'gmail-python-quickstart.json')

    #store = Storage(credential_path)

    from oauth2client.service_account import ServiceAccountCredentials
    from apiclient import discovery
    import httplib2

    scopes = ['https://www.googleapis.com/auth/gmail.send']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'ciceron_oauth2.json', scopes)

    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    return service

def send_mail(mail_to, subject, message, mail_from='no-reply@ciceron.me'):
    """
    주어진 mesasge를 메일로 날려주는 라이브러리이다.
    """
    import smtplib
    import base64
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    content = MIMEText(message, 'html', _charset='utf-8')
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'Ciceron team <%s>' % mail_from
    msg['To'] = str(mail_to)
    msg.attach(content)
    encoded_msg = {'raw': base64.urlsafe_b64encode(msg.as_string())}

    service = get_gmail_service()

    print(msg)
    #a = smtplib.SMTP('smtp.gmail.com:587')
    #a.ehlo()
    #a.starttls()
    #a.login('no-reply@ciceron.me', 'ciceron3388!')
    #a.sendmail('no-reply@ciceron.me', str(mail_to), base64.urlsafe_b64encode(msg.as_string()))
    #a.quit()
    message = (service.users().messages().send(userId=mail_to, body=encoded_msg)
                           .execute())

def store_notiTable(conn, user_id, noti_type_id, target_user_id, request_id):
    """
    노테를 테이블에 쌓아준다.
    """
    cursor = conn.cursor()
    new_noti_id = get_new_id(conn, "F_NOTIFICATION")
    # The query below is original
    query = "INSERT INTO CICERON.F_NOTIFICATION VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP,false,false)"
    # The query below is that mail alarm is forcefully turned off
    #query = "INSERT INTO F_NOTIFICATION VALUES (?,?,?,?,CURRENT_TIMESTAMP,1)"
    cursor.execute(query, (new_noti_id, user_id, noti_type_id, target_user_id, request_id) )
    conn.commit()

def pick_random_translator(conn, number, from_lang, to_lang):
    """
    해당 언어쌍을 번역할 수 있는 번역가를 랜덤으로 number명만큼 추출하여 준다.
    """
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
    """
    노티에서 링크를 제공할 때, request의 상태를 파악하여 좀 더 똑똑하게 링크를 주기 위함이다.

    테스트 시스템인지, 프로덕션 시스템인지..
    티켓이 기간 만료인지, 삭제인지, 그 밖인지
    유저가 번역가인지 아닌지
    등등을 고려하여 라우팅 주소를 만든다.
    """
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
    """
    노티 데이터를 제공한다.
    """
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
    """
    파라미터를 받아와
    노티 테이블에 넣고
    어떤 메시지를 줄 지 가져온다음 푸시 알람 및 메일까지 날려주는 종합 노티 라이브러리 함수이다.
    """
    store_notiTable(conn, user_id, noti_type_id, target_user_id, request_id)
    message_dict = get_noti_data(conn, noti_type_id, user_id, request_id, optional_info=optional_info)
    regKeys_oneuser = get_device_id(conn, user_id)
    #print "Send push to the device: %s" % regKeys_oneuser
    if len(regKeys_oneuser) > 0:
        gcm_noti = gcm_server.send(regKeys_oneuser, "Ciceron push", notification=message_dict)

def send_noti_lite(conn, user_id, noti_type_id, target_user_id, request_id, optional_info=None):
    """
    노티 전송 라이트 버전이다. 미완성으로 보인다.
    """
    store_notiTable(conn, user_id, noti_type_id, target_user_id, request_id)
    message_dict = get_noti_data(conn, noti_type_id, user_id, request_id, optional_info=optional_info)
    regKeys_oneuser = get_device_id(conn, user_id)

def signUpQuick(conn, email, hashed_password, name, mother_language_id, nationality_id=None, residence_id=None, external_service_provider=[]):
    """
    회원 가입 함수이다.
    회원 테이블에 정보 밀어넣고, 그 밖에 비밀번호, 적립금 및 포인트를 넣는다.
    """
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

    print("New user id: %d" % user_id)
    cursor.execute("""INSERT INTO CICERON.D_USERS
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)""",
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
    """
    공용 프로모션 코드 validator이다.
    코드는 유효한지, 유효한 코드지만 이미 사용한 코드인지 등등을 체크한다.
    """
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
    """
    프로모션 코드를 적용한다.
    """
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
    """
    개인 프로모션 코드 validator이다.
    그 밖의 기능은 위와 같다.
    """
    cursor = conn.cursor()
    query_individualPromotionCode= """
        SELECT benefitPoint, expireTime, is_used FROM CICERON.PROMOTIONCODES_USER WHERE user_id = %s AND text = %s """
    cursor.execute(query_individualPromotionCode, (user_id, code))
    ret = cursor.fetchone()

    if ret == None or len(ret) == 0:
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
    """
    개인용 프로모션 코드 적용기이다.
    """
    cursor = conn.cursor()
    query_commonPromotionCodeExeutor = """
        UPDATE CICERON.PROMOTIONCODES_USER SET is_used = true WHERE user_id = %s AND text = %s """
    cursor.execute(query_commonPromotionCodeExeutor, (user_id, code))
    conn.commit()

def payment_start(conn, pay_by, pay_via, request_id, total_amount, user_id, host_ip,
        use_point=0, promo_type='null', promo_code='null', is_additional='false', payload=None):
    """
    결제 함수이다. 자세한 설명은 아래에 계속...
    """

    cursor = conn.cursor()

    # Point deduction
    """
    use_point: 포인트를 사용한다면, 먼저 가지고 있는 포인트보다 사용한다고 넣은 포인트가 큰지 아닌지부터 판단해야 한다.
    """
    if use_point > 0:
        # Check whether use_point exceeds or not
        cursor.execute("SELECT amount FROM CICERON.RETURN_POINT WHERE id = %s", (user_id, ))
        current_point = float(cursor.fetchall()[0][0])
        if current_point - use_point < -0.00001:
            return 'point_exceeded_than_you_have', None, current_point

        else:
            amount = total_amount - use_point
    else:
        amount = total_amount

    # Promo code deduction
    """
    프로모션 코드를 적용한다면, 먼저 validate 해 보고 유효하면 적용한 후, 총액에서 할인해준다.
    """
    if promo_type != 'null':
        isCommonCode, commonPoint, commonMessage = commonPromotionCodeChecker(g.db, user_id, promo_code)
        isIndivCode, indivPoint, indivMessage = individualPromotionCodeChecker(g.db, user_id, promo_code)
        if isCommonCode == 0:
            amount = amount - commonPoint
        elif isIndivCode == 0:
            amount = amount - indivPoint

    """
    Paypal, Alipay, Iamport 등등에 따라서 잘 처리해준다.
    """

    if pay_via == 'paypal' and amount > 0:
        """
        페이팔은 그냥 모든 정보를 URL에 박아서 페이팔에 넘겨주면 된다.
        결제는 페이팔에서 한 후 콜백으로 postprocessing을 불러오기때문에, 여기서는 페이팔로의 링크만 제공해주면 된다.
        """
        # SANDBOX
        if os.environ.get("PURPOSE") != "PROD":
            paypalrestsdk.configure(
                    mode="sandbox",
                    client_id="AQX4nD2IQ4xQ03Rm775wQ0SptsSe6-WBdMLldyktgJG0LPhdGwBf90C7swX2ymaSJ-PuxYKicVXg12GT",
                    client_secret="EHUxNGZPZNGe_pPDrofV80ZKkSMbApS2koofwDYRZR6efArirYcJazG2ao8eFqqd8sX-8fUd2im9GzBG"
            )

        # LIVE
        else:
            paypalrestsdk.set_config(
                    mode="live",
                    client_id="AevAg0UyjlRVArPOUN6jjsRVQrlasLZVyqJrioOlnF271796_2taD1HOZFry9TjkAYSTZExpyFyJV5Tl",
                    client_secret="EJjp8RzEmFRH_qpwzOyJU7ftf9GxZM__vl5w2pqERkXrt3aI6nsVBj2MnbkfLsDzcZzX3KW8rgqTdSIR"
                    )

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

    elif pay_via == 'alipay' and amount > 0:
        """
        알리페이도 페이팔과 흐름은 비슷하다. 알리페이 결제 링크 생성 후, 알리페이로 이동하여 결제가 완료되면 다시 콜백으로 씨세론으로 들어와 접수가 완료됨을 알 수 있는 시스템이다.
        """
        from alipay import Alipay
        order_no = orderNoGenerator(conn)

        alipay_obj = Alipay(pid='2088021580332493', key='lksk5gkmbsj0w7ejmhziqmoq2gdda3jo', seller_email='contact@ciceron.me')
        params = {
            'subject': '诗谐论翻译'.decode('utf-8'),
            'out_trade_no': order_no,
            #'subject': 'TEST',
            'total_fee': '%.2f' % amount,
            'currency': 'USD',
            'quantity': '1',
            'return_url': "%s:5000/api/user/requests/%d/payment/postprocess?pay_via=alipay&status=success&user_id=%s&pay_amt=%.2f&pay_by=%s&use_point=%.2f&promo_type=%s&promo_code=%s&is_additional=%s&ciceron_order_no=%s" % (host_ip, request_id, session['useremail'], amount, pay_by, use_point, promo_type, promo_code, is_additional, order_no)
            }

        provided_link = None
        try:
            if pay_by == 'web':
                provided_link = alipay_obj.create_forex_trade_url(**params)
            elif pay_by == 'mobile':
                provided_link = alipay_obj.create_forex_trade_wap_url(**params)
        except:
            return 'alipay_failure', None, None

        return 'alipay_success', provided_link, None

    elif pay_via == 'iamport' and amount > 0:
        """
        아임포트 No-ActiveX 결제 시스템이다.

        직접 카드번호 및 유효기간 등의 정보를 물러와서 결제를 바로 한다.
        그리고 이 자리에서 바로 결제를 하기 때문에 postprocessing 과정을 거쳐서 할 작업을 여기서 다 한다.
        """
        # Should check USD->KRW currency
        # Hard coded: 1200
        new_payload = payload
        kor_amount = int(amount * 1160)
        order_no = orderNoGenerator(conn)

        new_payload['merchant_uid'] = order_no
        new_payload['amount'] = kor_amount

        pay_module = Iamport(imp_key=2311212273535904, imp_secret='jZM7opWBO5K2cZfVoMgYJhsnSw4TiSmBR8JgyGRnLCpYCFT0raZbsrylYDehvBSnKCDjivG4862KLWLd')

        payment_result = pay_module.pay_onetime(**new_payload)
        double_check = pay_module.is_paid(**payment_result)
        if double_check == False:
            return 'iamport_error', None, None

        # DB process
        if is_additional == 'false':
            query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_paid = %s WHERE id = %s"
        else:
            query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_additional_points_paid = %s WHERE id = %s"
        cursor.execute(query_setToPaid, (True, request_id, ))

        payment_info_id = get_new_id(g.db, "PAYMENT_INFO")
        cursor.execute("INSERT INTO CICERON.PAYMENT_INFO (id, request_id, client_id, payed_via, order_no, pay_amount, payed_time) VALUES (%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)",
                    (payment_info_id, request_id, user_id, "iamport", order_no, amount))

        conn.commit()

        if pay_by == "web":
            return 'iamport_success', None, None
        elif pay_by == "mobile":
            return 'iamport_success', None, None

    elif pay_via == "point_only" or amount < 0.001:
        """
        이도 저도 아니고 포인트로 결제한다면 iamport와 마찬가지로 postprocessing 없이 진행할 수 있다.
        """
        cursor.execute("SELECT amount FROM CICERON.RETURN_POINT WHERE id = %s", (user_id, ))
        current_point = float(cursor.fetchall()[0][0])

        amount = 0
        if use_point > 0.01 and current_point - use_point < -0.00001:
            return make_response(json.jsonify(
                message="You requested to use your points more than what you have. Price: %.2f, Your purse: %.2f" % (total_amount, current_point)), 402)
        else:
            amount = current_point - use_point

        if amount > 0.01:
            cursor.execute("UPDATE CICERON.RETURN_POINT SET amount = amount - %s WHERE id = %s", (use_point, user_id, ))

        if is_additional == 'false':
            query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_paid = %s WHERE id = %s"
        else:
            query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_additional_points_paid = %s WHERE id = %s"
        cursor.execute(query_setToPaid, (True, request_id, ))
        conn.commit()

        if pay_by == "web":
            return 'point_success', None, None
        elif pay_by == "mobile":
            return 'point_success', None, None

def payment_postprocess(conn, pay_by, pay_via, request_id, user_id, is_success, amount,
        use_point=0, promo_type='null', promo_code='null', is_additional='false'):
    """
    로직
        1. 지불로 처리힌다.
        2. 지불 정보 한 줄 INSERT한다.
        3. 프로모션 코드 사용처리한다.
    """

    cursor = conn.cursor()

    # Point deduction
    if use_point > 0:
        cursor.execute("UPDATE CICERON.return_point SET amount = amount - %s WHERE id = %s", (use_point, user_id, ))

    if pay_via == 'paypal':
        payment_id = request.args['paymentId']
        payer_id = request.args['PayerID']
        if is_success:
            payment_info_id = get_new_id(conn, "PAYMENT_INFO")
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

            conn.commit()
            #return redirect("success")

    elif pay_via == "alipay":
        if is_success:
            # Get & store order ID and price
            payment_info_id = get_new_id(conn, "PAYMENT_INFO")
            order_no = request.args['ciceron_order_no']

            if is_additional == 'false':
                query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_paid = %s WHERE id = %s"
            else:
                query_setToPaid = "UPDATE CICERON.F_REQUESTS SET is_additional_points_paid = %s WHERE id = %s"
            cursor.execute(query_setToPaid, (True, request_id, ))

            # Payment information update
            cursor.execute("INSERT INTO CICERON.PAYMENT_INFO (id, request_id, client_id, payed_via, order_no, pay_amount, payed_time) VALUES (%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)",
                    (payment_info_id, request_id, user_id, "alipay", order_no, amount))

            conn.commit()

    if promo_type == 'common':
        commonPromotionCodeExecutor(conn, user_id, promo_code)
    elif promo_type == 'indiv':
        individualPromotionCodeExecutor(conn, user_id, promo_code)

    # Notification for normal request
    cursor.execute("SELECT original_lang_id, target_lang_id FROM CICERON.F_REQUESTS WHERE id = %s ", (request_id, ))
    record = cursor.fetchone()
    if record is None or len(record) == 0:
        print("No record for this request. Request ID: %d" % request_id)
        return 'no_record'

    original_lang_id = record[0]
    target_lang_id = record[1]

    rs = pick_random_translator(conn, 10, original_lang_id, target_lang_id)
    for item in rs:
        store_notiTable(conn, item[0], 1, None, request_id)
        regKeys_oneuser = get_device_id(conn, item[0])

        message_dict = get_noti_data(conn, 1, item[0], request_id)
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

def calculateChecksum(*args):
    checksum_obj = hashlib.md5()
    for line in args:
        checksum_obj.update(line)
    return checksum_obj.hexdigest()
