# -*- coding: utf-8 -*-

from flask import Flask, session, request, g, make_response
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

    def passwordCheck(self, email, password):
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

        elif len(rs) == 1 and get_hashed_password(str(rs[0][0]), session['salt']) == hashed_password:
            # Status code 200 (OK)
            # Description: Success to log in
            return 200, None


class UserControlAPI(object):
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}'.format(endpoint), view_func=self.loginCheck2, methods=["GET"])
            self.app.add_url_rule('{}/login'.format(endpoint), view_func=self.login2, methods=["GET", "POST"])

    def loginCheck2(self):
        """
        GET /api
        GET /api/v2

        해당 세션의 상태를 보여준다.
        아래 return값은 session[var_name]으로 접근 가능하다

        :Parameters: Nothing
    
        :Response
          :200
            .. code-block:: json
              {
                "useremail": "blahblah@gmail.com" // 로그인한 유저의 이메일주소. 로그인 상태 아니면 null
                "isLoggedIn": true // 로그인 여부 True/False
                "isTranslator" : false  //로그인한 유저의 번역가여부 True/False
              }
          :403
            - 로그인되지 않았음
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

    def login2(self):
        """
        GET /api/login
        GET /api/v2/login

        POST /api/login
        POST /api/v2/login
    
        로그인 로직
          1. GET /api/v2/login에 접속
          2. 로그인 Salt를 받는다.
          3. 클라이언트에서는 sha256(salt + sha256(password) + salt) 값을 만들어 서버에 전송한다.
          4. Password 테이블 값과 비교하여 일치하면 session 값들을 고쳐준다.
    
        GET /api/login or /api/v2/login
          :Parameters: Nothing
          :Response
            :200
              .. code-block:: json
                {
                  "logged_in": true, // 로그인 상태
                  "useremail": "blahblah@ciceron.me" // 로그인한 유저 메일
                  "isTranslator": true // 번역가 계정인지 아닌지 확인
                }
    
        POST /api/login or /api/v2/login
          :Parameters
            "email": 유저 email 주소 (ciceron_lib.get_user_id를 통하여 email에서 user_id를 추출할 수 있다.)
            "password": 3번 참조
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

            resp_code, err_msg = userControlObj.passwordCheck(email, hashed_password)
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


if __name__ == "__main__":
    pass
