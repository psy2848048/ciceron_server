# -*- coding: utf-8 -*-
from flask import Flask, request, g, make_response, json, session
from datetime import datetime, timedelta
import os
import requests
import io

import psycopg2
from flask_cache import Cache

try:
    import ciceron_lib
except:
    from . import ciceron_lib


class UserControl(object):
    def __init__(self, conn):
        self.conn = conn

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
        cursor.execute("""
            INSERT INTO CICERON.D_USERS
            VALUES (
              %s,%s,%s,%s,%s,
              %s,%s,%s,%s,%s,
              %s,%s,%s,%s,%s,
              %s,%s,%s,%s,CURRENT_TIMESTAMP
            )""",
                (
              user_id, email, name, mother_language_id, False,
              None, None, 0, 0, 0,
              0, 0, 0, None, "nothing",
              0, nationality_id, residence_id, 0.7)
            )
    
        cursor.execute("INSERT INTO CICERON.PASSWORDS VALUES (%s,%s)",
            (user_id, hashed_password))
        # 번역가의 매출
        cursor.execute("INSERT INTO CICERON.REVENUE VALUES (%s,%s)",
            (user_id, 0))
        # 의뢰인의 소지 포인트
        cursor.execute("INSERT INTO CICERON.RETURN_POINT VALUES (%s,%s)",
            (user_id, 0))
    
        #if 'facebook' in external_service_provider:
        #    new_facebook_id = get_new_id(conn, "D_FACEBOOK_USERS")
        #    cursor.execute("INSERT INTO CICERON.D_FACEBOOK_USERS VALUES (%s,%s,%s) ",
        #            (new_facebook_id, email, user_id))

        return 200


class UserControlAPI(object):
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}'.format(endpoint), view_func=self.loginCheck, methods=["GET"])
            self.app.add_url_rule('{}/login'.format(endpoint), view_func=self.login, methods=["GET", "POST"])
            self.app.add_url_rule('{}/logout'.format(endpoint), view_func=self.logout, methods=["GET"])

    def loginCheck(self):
        """
        해당 API
          #. GET /api
          #. GET /api/v2

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
                 "isTranslator" : false  //로그인한 유저의 번역가여부 True/False
               }

          **403**
            로그인되지 않았음

        """
        if 'useremail' in session:
            client_os = request.args.get('client_os', None)
            isTranslator = ciceron_lib.translator_checker_plain(g.db, session['useremail'])
            #if client_os is not None and registration_id is not None:
            #    check_and_update_reg_key(g.db, client_os, registration_id)
            #    g.db.coomit()

            return make_response(json.jsonify(
                useremail=session['useremail'],
                isLoggedIn = True,
                isTranslator=isTranslator,
                message="User %s is logged in" % session['useremail'])
                , 200)
        else:
            return make_response(json.jsonify(
                useremail=None,
                isLoggedIn=False,
                isTranslator=False,
                message="No user is logged in")
                , 403)

    def login(self):
        """
        해당 API
          #. 토큰 따기
            #. GET /api/login
            #. GET /api/v2/login

          #. 로그인하기
            #. POST /api/login
            #. POST /api/v2/login

        로그인 로직
          #. GET /api/v2/login에 접속
          #. 로그인 Salt를 받는다.
          #. 클라이언트에서는 sha256(salt + sha256(password) + salt) 값을 만들어 서버에 전송한다.
          #. Password 테이블 값과 비교하여 일치하면 session 값들을 고쳐준다.

        GET /api/login or /api/v2/login
          **Parameters**
            Nothing

          **Response**
            **200**
              .. code-block:: json
                 :linenos:

                 {
                   "identifier": "a3Bd1g", // Password Salt
                 }

        POST /api/login or /api/v2/login
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

        else:
            salt = ciceron_lib.random_string_gen()
            session['salt'] = salt
            return make_response(json.jsonify(identifier=salt), 200)

    def logout(self):
        """
        로그아웃 함수
          #. GET /api/logout
          #. GET /api/v2/logout

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
          #. POST /api/signup
          #. POST /api/v2/signup

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

        resp_code = userControlObj.signUp


if __name__ == "__main__":
    pass
