# -*- coding: utf-8 -*-

from flask import Flask, session, request, g, make_response
from datetime import datetime, timedelta
import os
import requests
import io, sys
sys.path.append( os.path.dirname(os.path.abspath(os.path.dirname(__file__))) )

import psycopg2
from flask_cache import Cache

try:
    import ciceron_lib
except:
    from . import ciceron_lib


class UserControl(object):
    def __init__(self, conn):
        self.conn = conn


class UserControlAPI(object):
    def __init__(self, app, cache=None):
        self.app = app
        self.cache = cache
        self.add_api(self.app)
        self.endpoints = endpoints

    def add_api(self, app):
        for endpoint in self.endpoint:
            self.app.add_url_rule('{}'.format(endpoint), view_func=self.loginCheck, methods=["GET"])

    @self.cache.cached(timeout=50, key_prefix='loginStatusCheck')
    def loginCheck(self):
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
            .. code-block:: json
                {
                    "useremail": "blahblah@gmail.com" // 로그인한 유저의 이메일주소. 로그인 상태 아니면 null
                    "isLoggedIn": true // 로그인 여부 True/False
                    "isTranslator" : false  //로그인한 유저의 번역가여부 True/False
                }
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
    
