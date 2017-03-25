# -*- coding: utf-8 -*-

import psycopg2
import io
import os
import traceback
from flask import Flask, request, g, make_response, json, session, redirect, render_template, send_file
from datetime import datetime
try:
    import ciceron_lib
except:
    from . import ciceron_lib

try:
    from ciceron_lib import login_required, admin_required
except:
    from .ciceron_lib import login_required, admin_required


class AdminStats(object):
    def __init__(self, conn):
        self.conn = conn

    def statOverview(self):
        cursor = self.conn.cursor()
        # Currently, no data for displaying...

    def aboutDeadline(self):
        pass

    def checkRequests(self):
        pass


class AdminStatsAPI(object):
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}/admin/stats/overview'.format(endpoint), view_func=self.adminStatsOverview, methods=["GET"])
            self.app.add_url_rule('{}/admin/stats/aboutDeadline'.format(endpoint), view_func=self.adminAboutDeadline, methods=["GET"])

            self.app.add_url_rule('{}/admin/requests'.format(endpoint), view_func=self.adminCheckRequests, methods=["GET"])
            self.app.add_url_rule('{}/admin/requests/<int:request_id>/status/<status_name>'.format(endpoint), view_func=self.adminChangeStatus, methods=["PUT"])

    def adminStatsOverview(self):
        """
        Admin 첫 페이지 Dashboard에 보여주는 통계자료

        **Parameters**: Nothing

        **Response**
          #. **200**

            .. code-block:: json
               :linenos:

               {
                 "total_requests": 3, // 총 건수
                 "pendings": 1, // 의뢰건수
                 "ongoings": 1, // 진행중
                 "completes": 1 // 완료
               }

        """
        pass

    def adminAboutDeadline(self):
        """
        Admin 첫 페이지 마감임박에 보여주는 통계자료

        **Parameters**: Nothing

        **Response**
          #. **200**

            .. code-block:: json
               :linenos:

               {
                 "data": [
                   {
                     "id": 4, // ID
                     "theme": "블라블라", // 의뢰명
                     "requester_name": "Otto", // 의뢰인명
                     "translator_name": "mdo", // 번역가명
                     "deadline": "2017. 11. 12. 08:00 KST" // 마감시간
                   },
                   ...
                 ]
               }

        """
        pass

    def adminCheckRequests(self):
        """
        Admin 페이지: 의뢰 목록 열람

        **Parameters**: Nothing

        **Response**
          #. **200**

            .. code-block:: json
               :linenos:

               {
                 "data": [
                   {
                     "id": 4, // ID
                     "requester_name": "Otto", // 의뢰건수
                     "requester_email": "Otto@naver.com", // 의뢰인 E-mail
                     "subject_id": 1, // 종류
                     "original_lang_id": 1, // 원 언어
                     "target_lang_id": 2, // 타겟 언어
                     "request_time": "2017. 11. 12. 08:00 KST", // 요청일
                     "order_number": "2017HQ20301" // 주문번호
                     "status": 0 // 상태 := 0 -> 진행 1 -> 완료 2 -> 중지 3 -> 숨김
                   },
                   ...
                 ]
               }

        """
        pass

    def adminChangeStatus(self, request_id, status_name):
        """
        Admin 페이지: 의뢰물 상태변경

        **Parameters**
          #. **"request_id"**: URL 직접삽입, 의뢰물 ID
          #. **"status_name"**: URL 직접삽입
            #. "ongoing": 진행
            #. "complete": 완료
            #. "hide": 숨기기
            #. "stop": 중지

        **Response**
          #. **200**: OK
          #. **410**: Fail

        """
        pass

