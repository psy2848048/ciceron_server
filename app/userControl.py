# -*- coding: utf-8 -*-
from flask import Flask, request, g, make_response, json, session, send_file
from datetime import datetime, timedelta
import os
import requests
import io
import traceback
import psycopg2

try:
    import ciceron_lib
except:
    from . import ciceron_lib

try:
    from ciceron_lib import login_required, admin_required
except:
    from .ciceron_lib import login_required, admin_required


class UserControl(object):
    def __init__(self, conn):
        self.conn = conn

    def _adminCheck(self, email):
        cursor = self.conn.cursor()
        query = """
            SELECT is_admin FROM CICERON.D_USERS
            WHERE email = %s
        """
        cursor.execute(query, (email, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False

        return ret[0]

    def passwordCheck(self, email, salt, hashed_password):
        cursor = self.conn.cursor()

        user_id = ciceron_lib.get_user_id(self.conn, email)
        # Get hashed_password using user_id for comparing
        cursor.execute("SELECT hashed_pass FROM CICERON.PASSWORDS WHERE user_id = %s", (user_id, ))
        rs = cursor.fetchall()

        if len(rs) > 1:
            # Status code 500 (ERROR)
            # Description: Same e-mail address tried to be inserted into DB
            return 501, 'Constraint violation error!'

        elif len(rs) == 0:
            # Status code 403 (ERROR)
            # Description: Not registered
            return 403, 'Not registered {}'.format(email)

        elif len(rs) == 1 and ciceron_lib.get_hashed_password(str(rs[0][0]), salt) == hashed_password:
            # Status code 200 (OK)
            # Description: Success to log in
            return 200, None

    def signUp(self, email, hashed_password, name, mother_language_id
            , nationality_id=None
            , residence_id=None
            , external_service_provider=[]):

        # Duplicate check
        cursor = self.conn.cursor()
        cursor.execute("select id from CICERON.D_USERS where email = %s", (email, ))
        check_data = cursor.fetchall()
        if len(check_data) > 0:
            # Status code 400 (BAD REQUEST)
            # Description: Duplicate ID
            return 412
    
        if '@' not in email:
            return 417
    
        # Insert values to D_USERS
        user_id = ciceron_lib.get_new_id(self.conn, "D_USERS")
    
        print("    New user id: {}".format(user_id) )
        try:
            cursor.execute("""
                INSERT INTO CICERON.D_USERS
                  (
                    id
                  , email
                  , name
                  , mother_language_id
                  , is_translator

                  , other_language_list_id
                  , profile_pic_path
                  , numOfRequestPending
                  , numOfRequestOngoing
                  , numOfRequestCompleted

                  , numOfTranslationPending
                  , numOfTranslationOngoing
                  , numOfTranslationCompleted
                  , badgeList_id
                  , profile_text

                  , trans_request_state
                  , nationality
                  , residence
                  , return_rate
                  , member_since

                  , is_admin
                  , is_active

                  )
                VALUES
                (
                  %s,%s,%s,%s,%s,
                  %s,%s,%s,%s,%s,
                  %s,%s,%s,%s,%s,
                  %s,%s,%s,%s,CURRENT_TIMESTAMP,
                  false, true
                )""",
                    (
                  user_id, email, name, mother_language_id, False,
                  None, None, 0, 0, 0,
                  0, 0, 0, None, "nothing",
                  0, nationality_id, residence_id, 0.7)
                )
    
            cursor.execute("INSERT INTO CICERON.PASSWORDS VALUES (%s,%s)",
                (user_id, hashed_password, ))
            # 번역가의 매출
            cursor.execute("INSERT INTO CICERON.REVENUE VALUES (%s,%s)",
                (user_id, 0, ))
            # 의뢰인의 소지 포인트
            cursor.execute("INSERT INTO CICERON.RETURN_POINT VALUES (%s,%s)",
                (user_id, 0, ))

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return 400
    
        #if 'facebook' in external_service_provider:
        #    new_facebook_id = get_new_id(conn, "D_FACEBOOK_USERS")
        #    cursor.execute("INSERT INTO CICERON.D_FACEBOOK_USERS VALUES (%s,%s,%s) ",
        #            (new_facebook_id, email, user_id))

        return 200

    def duplicateIdChecker(self, email):
        cursor = self.conn.cursor()
        cursor.execute("select id from CICERON.D_USERS where email = %s", (email, ))
        check_data = cursor.fetchall()
        if len(check_data) == 0:
            return True
        else:
            return False

    def createRecoveryCode(self, email):
        cursor = self.conn.cursor()
        user_id = ciceron_lib.get_user_id(self.conn, email)
        if user_id == -1:
            return 400, None

        cursor.execute("SELECT name FROM CICERON.D_USERS WHERE id = %s ", (user_id, ))
        user_name = cursor.fetchall()[0][0]

        recovery_code = ciceron_lib.random_string_gen(size=12)
        hashed_code = ciceron_lib.get_hashed_password(recovery_code)
        query_insert_emergency="""
            WITH "RECOV_UPDATE" AS (
                UPDATE CICERON.EMERGENCY_CODE SET code = %s
                    WHERE user_id = %s RETURNING *
            )
            INSERT INTO CICERON.EMERGENCY_CODE (user_id, code)
            SELECT %s, %s WHERE NOT EXISTS (SELECT * FROM "RECOV_UPDATE")
            """

        try:
            cursor.execute(query_insert_emergency, (hashed_code, user_id, user_id, hashed_code, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False, None

        return True, recovery_code

    def sendRecoveryCode(self, email, recovery_code):
        user_id = ciceron_lib.get_user_id(self.conn, email)
        user_name = ciceron_lib.get_user_name(self.conn, user_id)
        subject = "Here is your temporary password"
        message = None
        with open('templates/password_recovery_mail.html', 'r') as f:
            message = f.read().format(
                          user=user_name
                        , password=recovery_code
                        , page=ciceron_lib.HOST
                        , host=ciceron_lib.HOST + ':5000'
                        )

        try:
            ciceron_lib.send_mail(email, subject, message)
        except:
            traceback.print_exc()
            return False

        return True

    def passwordUpdater(self, user_id, rs, hashed_old_password, hashed_new_password):
        cursor = self.conn.cursor()
        if len(rs) > 1:
            # Status code 500 (ERROR)
            # Description: Same e-mail address tried to be inserted into DB
            return 501, 'Constraint violation error!'

        elif str(hashed_new_password) == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855':
            return 405, 'Need password'

        elif len(rs) == 1 and str(rs[0][0]) == hashed_old_password:
            try:
                cursor.execute("UPDATE CICERON.PASSWORDS SET hashed_pass = %s WHERE user_id = %s ", (hashed_new_password, user_id))
                return 200, 'Password successfully changed!'
            except:
                traceback.print_exc()
                self.conn.rollback()
                return 502, "DB Error"

        else:
            return 403, 'Security code incorrect!'

    def recoverPassword(self, email, hashed_code, hashed_new_password):
        cursor = self.conn.cursor()
        user_id = ciceron_lib.get_user_id(self.conn, email)

        # Get hashed_password using user_id for comparing
        cursor.execute("SELECT code FROM CICERON.EMERGENCY_CODE where user_id = %s ", (user_id, ))
        rs = cursor.fetchall()
        resp_code, message = self.passwordUpdater(user_id, rs, hashed_code, hashed_new_password)
        if resp_code == 200:
            cursor.execute("UPDATE CICERON.EMERGENCY_CODE SET code = null WHERE user_id = %s ", (user_id, ))
            self.conn.commit()
            return resp_code, message

        else:
            self.conn.rollback()
            return resp_code, message

    def changePassword(self, email, hashed_old_password, hashed_new_password):
        cursor = self.conn.cursor()
        user_id = ciceron_lib.get_user_id(self.conn, email)
        cursor.execute("SELECT hashed_pass FROM CICERON.PASSWORDS where user_id = %s ", (user_id, ))
        rs = cursor.fetchall()
        resp_code, message = self.passwordUpdater(user_id, rs, hashed_old_password, hashed_new_password)
        if resp_code == 200:
            self.conn.commit()
            return resp_code, message

        else:
            self.conn.rollback()
            return resp_code, message

    def profile(self, email, rate=1, is_my_profile=False):
        cursor = self.conn.cursor()
        query_userinfo = """
            SELECT  
                id, email, name, mother_language_id, is_translator,
                other_language_list_id, profile_pic_path,
                numOfRequestPending, numOfRequestOngoing, numOfRequestCompleted,
                numOfTranslationPending, numOfTranslationOngoing, numOfTranslationCompleted,
                badgeList_id, profile_text, trans_request_state, nationality, residence
            FROM CICERON.D_USERS WHERE id = %s
            """

        # 프로필 주 정보 가져오기
        user_id = ciceron_lib.get_user_id(self.conn, email)
        cursor.execute(query_userinfo, (user_id, ))
        columns = [ desc[0] for desc in cursor.description ]
        userinfo = cursor.fetchall()
        profile_ret = ciceron_lib.dbToDict(columns, userinfo)[0]

        # 각종 부가정보 불러오기
        # 1) 번역 가능 언어
        cursor.execute("SELECT language_id FROM CICERON.D_TRANSLATABLE_LANGUAGES WHERE user_id = %s",
            (user_id, ))
        other_language_list = ",".join( [ str(item[0]) for item in cursor.fetchall() ] )
        cursor.execute("SELECT badge_id FROM CICERON.D_AWARDED_BADGES WHERE user_id = %s",
            (user_id, ))
        badgeList = (',').join([ str(item[0]) for item in cursor.fetchall() ])

        # 2) 키워드
        cursor.execute("SELECT key.text FROM CICERON.D_USER_KEYWORDS ids JOIN CICERON.D_KEYWORDS key ON ids.keyword_id = key.id WHERE ids.user_id = %s", (user_id, ))
        keywords = (',').join([ str(item[0]) for item in cursor.fetchall() ])

        if profile_ret['profile_pic_path'] == None:
            profile_ret['profile_pic_path'] = 'img/anon.jpg'
        profile_ret['translatableLang'] = other_language_list
        profile_ret['badgeList'] = badgeList
        profile_ret['is_translator'] = True if profile_ret['is_translator'] == 1 else False
        profile_ret['keywords'] = keywords

        if is_my_profile == True and profile_ret['is_translator'] == True:
            # 번역가 계좌의 돈
            cursor.execute("SELECT amount FROM CICERON.REVENUE WHERE id = %s",  (user_id, ))
            profile_ret['user_point'] = cursor.fetchone()[0]
        elif is_my_profile == True and profile_ret['is_translator'] == False:
            # 사용자 미환급금
            cursor.execute("SELECT amount FROM CICERON.RETURN_POINT WHERE id = %s",  (user_id, ))
            profile_ret['user_point'] = cursor.fetchone()[0]
        else:
            profile_ret['user_point'] = -65535

        return 200, profile_ret

    def changeProfileInfo(self
            , email
            , profile_text=None
            , profile_pic=None):

        cursor = self.conn.cursor()
        pic_path = None

        # Get user number
        user_id = ciceron_lib.get_user_id(g.db, email)

        # Profile text update
        if profile_text != None:
            try:
                cursor.execute("UPDATE CICERON.D_USERS SET profile_text = %s WHERE id = %s ", (profile_text, user_id))
            except:
                traceback.print_exc()
                self.conn.rollback()
                return False

        # Profile photo update
        filename = ""
        path = ""
        if profile_pic and ciceron_lib.pic_allowed_file(profile_pic.filename):
            extension = profile_pic.filename.split('.')[-1]
            filename = str(datetime.today().strftime('%Y%m%d%H%M%S%f')) + '.' + extension
            pic_path = os.path.join("user", "profile", str(user_id), "profilePic", filename)

            try:
                cursor.execute("UPDATE CICERON.D_USERS SET profile_pic_path = %s WHERE id = %s ", (pic_path, user_id))
                profile_pic_bin = profile_pic.read()
                query_insert = """
                    WITH "UPDATE_PROFILE_PIC" AS (
                        UPDATE CICERON.F_USER_PROFILE_PIC SET filename = %s, bin = %s
                            WHERE user_id = %s RETURNING *
                    )
                    INSERT INTO CICERON.F_USER_PROFILE_PIC (user_id, filename, bin)
                    SELECT %s, %s, %s WHERE NOT EXISTS (SELECT * FROM "UPDATE_PROFILE_PIC")
                    """
                cursor.execute(query_insert, (filename, bytearray(profile_pic_bin), user_id, user_id, filename, bytearray(profile_pic_bin)))
            except:
                traceback.print_exc()
                self.conn.rollback()
                return False

        return True

    def profilePic(self, user_id):
        cursor = self.conn.cursor()
        query_getPic = "SELECT bin FROM CICERON.F_USER_PROFILE_PIC WHERE user_id = %s"
        cursor.execute(query_getPic, (user_id, ))
        profile_pic = cursor.fetchone()[0]
        if profile_pic == None:
            return None
        else:
            return io.BytesIO(profile_pic)

    def userLists(self, page=1):
        cursor = self.conn.cursor()
        query = """
            SELECT *
            FROM CICERON.D_USERS
            ORDER BY id DESC
            LIMIT 20 OFFSET 20 * ({} - 1)
        """.format(page)
        cursor.execute(query)
        columns = [ row[0] for row in cursor.description ]
        ret = cursor.fetchall()
        data = ciceron_lib.dbToDict(columns, ret)

        for row in data:
            # Permission level check
            if row['is_admin'] == True:
                row['permission_level'] = 2
            elif row['is_admin'] == False and row['is_translator'] = True:
                row['permission_level'] = 1
            elif row['is_admin'] == False and row['is_translator'] = False:
                row['permission_level'] = 0

            # Activity level check
            if row['is_active'] == True:
                row['activity_id'] = 0
            else:
                row['activity_id'] = 1

            # Baogao 등, B2C 상품 출시 후 활성 가능
            row['recent_work_timestamp'] = None

        return data

    def permissionChange(self, user_id, permission):
        cursor = self.conn.cursor()
        is_admin = None
        if permission == "normal":
            is_admin = False
        elif permission == "admin":
            is_admin = True

        query = """
            UPDATE CICERON.D_USERS
              SET is_admin = %s
              WHERE id = %s
        """
        try:
            cursor.execute(query, (is_admin, user_id, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def activeStatusChange(self, user_id, activeStatus):
        cursor = self.conn.cursor()
        is_active = None
        if activeStatus == "active":
            is_active = True
        elif activeStatus == "deactive":
            is_active = False

        query = """
            UPDATE CICERON.D_USERS
              SET is_active = %s
              WHERE id = %s
        """
        try:
            cursor.execute(query, (is_active, user_id, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def langaugeAssigner(self, user_id, language_id_list):
        cursor = self.conn.cursor()

        # 번역 언어 추가
        cursor.execute("UPDATE CICERON.D_USERS SET is_translator = true, trans_request_state = 2 WHERE id = %s ", (user_id, ))
        for language_id in language_id_list:
            new_translation_list_id = ciceron_lib.get_new_id(self.conn, "D_TRANSLATABLE_LANGUAGES")
            try:
                cursor.execute("SELECT count(*) FROM CICERON.D_TRANSLATABLE_LANGUAGES WHERE user_id = %s and language_id = %s ", (user_id, language_id, ))
                rs = cursor.fetchone()
                if rs[0] == 0:
                    cursor.execute("INSERT INTO CICERON.D_TRANSLATABLE_LANGUAGES VALUES (%s,%s,%s)", (new_translation_list_id, user_id, language_id, ))

            except:
                self.conn.rollback()
                traceback.print_exc()
                return False

        # 기존 번역가능어 중 새 Parameter에서는 빠진 것들 지우기
        cursor.execute("SELECT language_id FROM CICERON.D_TRANSLATABLE_LANGUAGES WHERE user_id = %s ", (user_id, ))
        rs = cursor.fetchall()
        for row in rs:
            language_id = row[0]
            if language_id not in language_id_list:
                try:
                    cursor.execute("DELETE FROM CICERON.D_TRANSLATABLE_LANGUAGES WHERE user_id = %s AND language_id = %s", (user_id, language_id, ))
                except:
                    self.conn.rollback()
                    traceback.print_exc()
                    return False

        return True



class UserControlAPI(object):
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}'.format(endpoint), view_func=self.loginCheck, methods=["GET"])
            self.app.add_url_rule('{}/login'.format(endpoint), view_func=self.login, methods=["POST"])
            self.app.add_url_rule('{}/login'.format(endpoint), view_func=self.getLoginToken, methods=["GET"])
            self.app.add_url_rule('{}/logout'.format(endpoint), view_func=self.logout, methods=["GET"])
            self.app.add_url_rule('{}/idCheck'.format(endpoint), view_func=self.duplicateIdChecker, methods=["POST"])
            self.app.add_url_rule('{}/user/create_recovery_code'.format(endpoint), view_func=self.createRecoveryCode, methods=["POST"])
            self.app.add_url_rule('{}/user/recover_password'.format(endpoint), view_func=self.recoverPassword, methods=["POST"])
            self.app.add_url_rule('{}/user/change_password'.format(endpoint), view_func=self.changePassword, methods=["POST"])
            self.app.add_url_rule('{}/user/profile'.format(endpoint), view_func=self.profileCheck, methods=["GET"])
            self.app.add_url_rule('{}/user/profile'.format(endpoint), view_func=self.profileRevise, methods=["POST"])
            self.app.add_url_rule('{}/user/profile/<int:user_id>/profilePic/<fake_filename>'.format(endpoint), view_func=self.profilePic, methods=["GET"])



            self.app.add_url_rule('{}/admin/userLists'.format(endpoint), view_func=self.adminUserLists, methods=["GET"])
            self.app.add_url_rule('{}/admin/user/<int:user_id>/permission/<status>'.format(endpoint), view_func=self.adminPermissionChange, methods=["PUT"])
            self.app.add_url_rule('{}/admin/user/<int:user_id>/activity/<status>'.format(endpoint), view_func=self.adminActiveStatusChange, methods=["PUT"])
            self.app.add_url_rule('{}/admin/user/<int:user_id>/assignLanguage'.format(endpoint), view_func=self.adminAssignLanguage, methods=["POST"])

            if os.environ.get('PURPOSE') != 'PROD':
                self.app.add_url_rule('{}/login/admin'.format(endpoint), view_func=self.fakeLoginAdmin, methods=["GET", "POST"])
                self.app.add_url_rule('{}/login/user'.format(endpoint), view_func=self.fakeLoginUser, methods=["GET", "POST"])


    def loginCheck(self):
        """
        해당 API

        해당 세션의 상태를 보여준다.
        아래 return값은 session[var_name]으로 접근 가능하다

        **Parameters**
          Nothing
    
        **Response**
          **200**
            .. code-block:: json
               :linenos:

               {
                 "useremail": "blahblah@gmail.com", // 로그인한 유저의 이메일주소. 로그인 상태 아니면 null
                 "isLoggedIn": true, // 로그인 여부 True/False
                 "isAdmin": true, // 관리자 여부 True/False
                 "isTranslator" : false  //로그인한 유저의 번역가여부 True/False
               }

          **403**
            로그인되지 않았음

        """
        if 'useremail' in session:
            client_os = request.args.get('client_os', None)
            isTranslator = ciceron_lib.translator_checker_plain(g.db, session['useremail'])
            isAdmin = True # TODO

            #if client_os is not None and registration_id is not None:
            #    check_and_update_reg_key(g.db, client_os, registration_id)
            #    g.db.commit()

            return make_response(json.jsonify(
                useremail=session['useremail'],
                isLoggedIn = True,
                isTranslator=isTranslator,
                isAdmin=isAdmin,
                message="User %s is logged in" % session['useremail'])
                , 200)
        else:
            return make_response(json.jsonify(
                useremail=None,
                isLoggedIn=False,
                isTranslator=False,
                isAdmin=isAdmin,
                message="No user is logged in")
                , 403)

    def login(self):
        """
        로그인하기

        로그인 로직
          #. GET /api/v2/login에 접속
          #. 로그인 Salt를 받는다.
          #. 클라이언트에서는 sha256(salt + sha256(password) + salt) 값을 만들어 서버에 전송한다.
          #. Password 테이블 값과 비교하여 일치하면 session 값들을 고쳐준다.

          **Parameters**
            #. "email": 유저 email 주소 (ciceron_lib.get_user_id를 통하여 email에서 user_id를 추출할 수 있다.)
            #. "password": 3번 참조

          **Response**
            **200** 로그인 성공
              .. code-block:: json
                 :linenos:

                 {
                   "logged_in": true, // 로그인 상태
                   "useremail": "blahblah@ciceron.me", // 로그인한 유저 메일
                   "isTranslator": true // 번역가 계정인지 아닌지 확인
                 }

            **403**: 로그인 실패

            **501**: 1유저 2 패스워드 (있을 수 없는 동작)
        """

        userControlObj = UserControl(g.db)
        if request.method == "POST":
            # Parameter
            #     email:        E-mail ID
            #     password:     password
            #     client_os:    := Android, iPhone, Blackberry, web.. (OPTIONAL)
            #     machine_id:   machine_id of client phone device (OPTIONAL)

            # Get parameters
            parameters = ciceron_lib.parse_request(request)
            email = parameters['email']
            hashed_password = parameters['password']
            #machine_id = parameters.get('machine_id', None)
            #client_os = parameters.get('client_os', None)

            resp_code, err_msg = userControlObj.passwordCheck(email, session['salt'], hashed_password)
            if resp_code != 200:
                return make_response(json.jsonify(message=err_msg), resp_code)
            else:
                isTranslator = ciceron_lib.translator_checker_plain(g.db, email)
                session['logged_in'] = True
                session['useremail'] = email
                session['isTranslator'] = isTranslator
                session.pop('salt', None)
                return make_response(json.jsonify(
                    message='Logged in',
                    isTranslator=isTranslator,
                    email=email)
                    , resp_code)

    def getLoginToken(self):
        """
        로그인 토큰 발급

        **Parameters**
          Nothing
       
        **Response**
          **200**
       
            .. code-block:: json
               :linenos:
       
               {
                 "identifier": "a3Bd1g", // Password Salt
               }

        """
        salt = ciceron_lib.random_string_gen()
        session['salt'] = salt
        return make_response(json.jsonify(identifier=salt), 200)

    def logout(self):
        """
        로그아웃 함수

        **Parameters**
          Nothing

        **Response**
          **200**
            .. code-block:: json
               :linenos:

               {
                 "email": "blahblah@ciceron.me", // 로그인했던 유저 메일
               }

          **403**
            로그인한 적이 없을 때
        """
        if session['logged_in'] == True:
            username_temp = session['useremail']
            session.pop('logged_in', None)
            session.pop('useremail', None)
            # Status code 200 (OK)
            # Logout success
            return make_response(json.jsonify(
                       message = "Logged out",
                       email=username_temp
                   ), 200)
        else:
            # Status code 403 (ERROR)
            # Description: Not logged in yet
            return make_response(json.jsonify(
                       message = "You've never logged in"
                   ), 403)

    def signUp(self):
        """
        회원가입 함수

        **Parameters**
          #. "email": String, 회원 E-mail
          #. "password": sha256(password) 전송. Salt 적용 안 함.
          #. "name": String, 이름
          #. "mother_tongue_id": Int, 모국어 ID

        **Response**
          **200**
            .. code-block:: json
               :linenos:

               {
                 "email": "blahblah@ciceron.me", // 로그인했던 유저 메일
               }

          **400**: 파라미터 빠뜨림

          **412**: 중복가입

          **417**: 올바른 이메일 형식이 아님

          **420**: 어딘가의 이상
        """
        userControlObj = UserControl(g.db)

        # Get parameter values
        parameters = parse_request(request)
        email = parameters['email']
        hashed_password = parameters['password']
        name = parameters['name']
        if 'mother_language_id' in parameters:
            mother_language_id = int(parameters['mother_language_id'])
        else:
            return make_response(json.jsonify(
                message="Some parameters are missing"), 400)

        nationality_id = int(parameters.get('nationality_id')) if parameters.get('nationality_id') != None else None
        residence_id = int(parameters.get('residence_id')) if parameters.get('residence_id') != None else None

        resp_code = userControlObj.signUp(email, hashed_password, name, mother_language_id, nationality_id=nationality_id, residence_id=residence_id)

        if resp_code == 200:
            return make_response(json.jsonify(
                email=email
              , message="Successfully signed up!"
              ), resp_code)

        elif resp_code == 412:
            return make_response(json.jsonify(
                message="Duplicate ID"
                ), resp_code)
        elif resp_code == 417:
            return make_response(json.jsonify(
                message="ID is not e-mail form"
                ), resp_code)
        elif resp_code == 420:
            return make_response(json.jsonify(
                message="Something wrong"
                ), resp_code)

    def duplicateIdChecker(self):
        """
        중복 ID check

        **Parameters**
          #. "email": String email

        **Response**
          **200**
            중복 ID 없음. 사용가능

            .. code-block:: json
               :linenos:

               {
                 "email": "blahblah@ciceron.me", // 테스트했던 유저 메일
               }

          **417**
            해당 입력 email은 중복 ID

        """
        userControlObj = UserControl(g.db)
        parameters = ciceron_lib.parse_request(request)
        email = parameters['email']
        is_unique = userControlObj.duplicateIdChecker(email)
        if is_unique == True:
            return make_response(json.jsonify(
                email=email
              , message="You may use the ID"
              ), 200)
        else:
            return make_response(json.jsonify(
                message="Duplicated ID"
                ), 417)

    def createRecoveryCode(self):
        """
        비밀번호 복구 코드

        **Parameters**
          #. "email": String email

        **Response**
          #. **200**: 복구 메일 발송 성공
          #. **405**: 복구 코드 생성 에러
          #. **406**: 메일 시스템 에러

        """
        userControlObj = UserControl(g.db)
        parameters = ciceron_lib.parse_request(request)
        email = parameters['email']

        try:
            is_produced, recovery_code = userControlObj.createRecoveryCode(email)
            is_mail_sent = userControlObj.sendRecoveryCode(email, recovery_code)
        except:
            traceback.print_exc()

        if is_produced == False:
            g.db.rollback()
            return make_response(json.jsonify(
                message="Recovery code generation error"
                ), 405)
        elif is_mail_sent == False:
            g.db.rollback()
            return make_response(json.jsonify(
                message="Mail system error"
                ), 406)
        else:
            g.db.commit()
            return make_response(json.jsonify(
                message="Recovery code is generated and sent to your mail"
                ), 200)

    def recoverPassword(self):
        """
        비밀번호 복구하기

        **Parameters**
          #. "email": String email
          #. "code": sha256(recovery_code)
          #. "new_password": sha256(new_password)

        **Response**
          #. **200**: 복구 성공
          #. **405**: 패스워드 필드 빈칸
          #. **403**: 보안코드 불일치
          #. **502**: DB 에러

        """
        userControlObj = UserControl(g.db)
        parameters = ciceron_lib.parse_request(request)
        email = parameters['email']
        hashed_code = parameters['code']
        hashed_new_password = parameters['new_password']
        resp_code, message = userControlObj.recoverPassword(email, hashed_code, hashed_new_password)

        if resp_code == 200:
            g.db.commit()
            return make_response(json.jsonify(
                message=message), resp_code)
        else:
            return make_response(json.jsonify(
                message=message), resp_code)

    @login_required
    def changePassword(self):
        """
        비밀번호 변경

        **Parameters**
          #. "email": String email
          #. "old_password": sha256(old_password)
          #. "new_password": sha256(new_password)

        **Response**
          #. **200**: 변경 성공
          #. **405**: 패스워드 필드 빈칸
          #. **403**: 이전 패스워드 불일치
          #. **502**: DB 에러

        """
        userControlObj = UserControl(g.db)
        parameters = ciceron_lib.parse_request(request)
        email = session['useremail']
        hashed_old_password = parameters['old_password']
        hashed_new_password = parameters['new_password']
        resp_code, message = userControlObj.changePassword(email, hashed_old_password, hashed_new_password)

        if resp_code == 200:
            g.db.commit()
            return make_response(json.jsonify(
                message=message), resp_code)
        else:
            return make_response(json.jsonify(
                message=message), resp_code)

    @login_required
    def profileCheck(self):
        """
        프로필 열람

        **Parameters**
          #. user_email: (OPTIONAL) 조회하고픈 유저의 메일.
            (DEFAULT: 로그인 한 본인의 이메일)
         
        **Response**
          **200**

            .. code-block:: json
               :linenos:

               {
                 "id": 4, // Integer User Id
                 "email": "admin@ciceron.me", // E-Mail
                 "name": "Admin", // User Name
                 "mother_language_id": 1, // User's mother language
                 "is_translator": true, // Boolean, 번역가 여부
                 "other_language_list_id": null, // 필요없음
                 "profile_pic_path": "profile_pic/4/20160426033806110457.png", // 프로필사진 주소
                 "numofrequestpending": 0, // 번역 대기중인 의뢰수
                 "numofrequestongoing": 0, // 번역 진행중인 의뢰수
                 "numofrequestcompleted": 0, // 의뢰 완료 건수
                 "numoftranslationpending": 0, // (Useless) 번역 장바구니에 넣은 수
                 "numoftranslationongoing": 5, // 진행중인 번역 작업물 수
                 "numoftranslationcompleted": 7, // 번역 완료한 수
                 "badgelist_id": null, // (Useless) String 형태의 뱃지 ID 리스트들. ','로 갈라 Array로 사용할 수 있다.
                 "profile_text": "Admin of CICERON", // 프로필 글귀
                 "trans_request_state": 2, // (Useless) 번역 권한 상태
                 "nationality": null, // 국적
                 "residence": null, // 거주지
                 "translatableLang": "2", // 번역 가능한 언어
                 "badgeList": "", // (Useless) 뱃지 리스느
                 "keywords": "", // String 형태의 리스트. 자신을 표현할 수 있는 키워드 추가/수정/삽입
                 "user_point": 0 // 번역가에겐 출금할 수 있는 돈, 의뢰인에게는 사이버머니
               }

        """
        userControlObj = UserControl(g.db)
        email = request.args.get('user_email', session['useremail'])
        is_same = (email == session['useremail'])
        resp_code, profile_ret = userControlObj.profile(email, is_my_profile=is_same)
        return make_response(json.jsonify(**profile_ret), resp_code)

    @login_required
    def profileRevise(self):
        """
        프로필 정보 수정

        **Parameters**
          #. "profileText": (OPTIONAL) 수정하고픈 프로필 문구
          #. "profilePic": (OPTIONAL) 수정하고픈 프로필 사진 바이너리

        **Response**
          #. **200**: OK
          #. **405**: Fail

        """
        userControlObj = UserControl(g.db)
        parameters = ciceron_lib.parse_request(request)
        profile_text = parameters.get('profileText', None)
        profile_pic = request.files.get('profilePic', None)
        is_updated = userControlObj.changeProfileInfo(session['useremail'], profile_text=profile_text, profile_pic=profile_pic)
        if is_updated == True:
            g.db.commit()
            return make_response(json.jsonify(
                message="Updated Successfully"
                ), 200)

        else:
            g.db.rollback()
            return make_response(json.jsonify(
                message="Something wrong"
                ), 405)

    @login_required
    def profilePic(self, user_id, fake_filename):
        """
        프로필 사진 받기

        **Parameters**
          #. **"user_id"**: User ID (Integer), URL에 직접 삽입
          #. **"fake_filename"**: 프로필 사진 이름

        **Response**
          **200**: 프로필 사진 전송

          **404**: 등록된 사진 없음
        """
        userControlObj = UserControl(g.db)
        profile_pic = userControlObj.profilePic(user_id)
        if profile_pic is None:
            return make_response(json.jsonify(message="No profile pic"), 404)
        else:
            return send_file(profile_pic, attachment_filename=fake_filename)






    @admin_required
    def adminUserLists(self):
        """
        Admin: 관리를 위한 유저 리스트

        **Parameters**
          #. **"page"**: (OPTIONAL) 다음 페이지

        **Response**
          **200**

            .. code-block:: json
               :linenos:

               {
                 "data": [
                   {
                     "id": 4, // Integer User Id
                     "name": "Mark", // 이름
                     "email": "admin@ciceron.me", // E-Mail
                     "permission_id": 0, // 권한 레벨 0: 회원 1: 번역가 2: 관리자
                     "recent_work_timestamp": "Tue 24.07.2017 ...", // 최근 작업 시간
                     "activity_id": 0 // 활동상황 0: 활동중 1: 중단
                   },
                   ...
                 ]
               }
        """
        userControlObj = UserControl(g.db)
        page = request.args.get(page, 1)
        ret = userControlObj.userLists(page=page)
        return make_response(json.jsonify(data=ret), 200)

    @admin_required
    def adminPermissionChange(self, user_id, status):
        """
        Admin: 회원 권한 설정

        **Parameters**
          #. **"user_id"**: URL에 삽입, User ID
          #. **"status"**: URL에 삽입, 활동여부
            #. "normal": 보통 회원
            #. "admin": Admin(관리자)

        **Response**
          **200**: OK
          **410**: Fail
        """
        userControlObj = UserControl(g.db)
        is_ok = userControlObj.permissionChange(user_id, status)
        if is_ok == True:
            g.db.commit()
            return make_response("OK", 200)
        else:
            g.db.rollback()
            return make_response("Fail", 410)

    @admin_required
    def adminActiveStatusChange(self, user_id, status):
        """
        Admin: 회원 권한 설정

        **Parameters**
          #. **"user_id"**: URL에 삽입, User ID
          #. **"status"**: URL에 삽입, 활동여부
            #. "active": 활동으로 설정
            #. "deactive": 중단으로 설정

        **Response**
          **200**: OK
          **410**: Fail
        """
        userControlObj = UserControl(g.db)
        is_ok = userControlObj.activeStatusChange(user_id, status)
        if is_ok == True:
            g.db.commit()
            return make_response("OK", 200)
        else:
            g.db.rollback()
            return make_response("Fail", 410)

    @admin_required
    def adminAssignLanguage(self, user_id):
        """
        Admin: 회원 권한 설정

        **Parameters**
          #. **"user_id"**: URL에 삽입, User ID
          #. **"language_id[]"**: Integer array
            #.  1: 한국어
            #.  2: 영어/미국
            #.  3: 영어/영국
            #.  4: 중국/보통어
            #.  5: 중국/광동어
            #.  6: 태국어
            #.  7: 중국/대만어
            #.  8: 일본어
            #.  9: 스페인어
            #. 10: 포르투갈어
            #. 11: 독일어
            #. 12: 프랑스어

        **Response**
          **200**: OK
          **410**: Fail
        """
        userControlObj = UserControl(g.db)
        parameters = ciceron_lib.parse_request(request)
        language_id_list = request.form.getlist("language_id[]")
        is_ok = userControlObj.langaugeAssigner(user_id, language_id_list)
        if is_ok == True:
            g.db.commit()
            return make_response("OK", 200)
        else:
            g.db.rollback()
            return make_response("Fail", 410)
            

    def fakeLoginAdmin(self):
        session['useremail'] = 'admin@ciceron.me'
        session['logged_in'] = True
        session['isTranslator'] = True
        return make_response("OK", 200)

    def fakeLoginUser(self):
        session['useremail'] = 'psy2848048@nate.com'
        session['logged_in'] = True
        session['isTranslator'] = False
        return make_response("OK", 200)

if __name__ == "__main__":
    pass
