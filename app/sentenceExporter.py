# -*- coding: utf-8 -*-

import psycopg2
import io
import os
import traceback
from flask import Flask, request, g, make_response, json, session, redirect, render_template, send_file
from datetime import datetime
import nltk

try:
    import ciceron_lib
except:
    from . import ciceron_lib

try:
    from ciceron_lib import login_required, admin_required
except:
    from .ciceron_lib import login_required, admin_required

class SentenceExporter(object):
    def __init__(self, conn):
        self.conn = conn
    
    def parseSentences(self, whole_paragraph):
        pass

    def importSentence(self,
            original_language_id, target_language_id,
            subject_id, format_id, tone_id,
            original_sentence, translated_sentence):
        pass

    def exportSentence(self,
            original_language_id=None,
            target_language_id=None,
            subject_id=None,
            format_id=None,
            tone_id=None):
        pass

    def dataCounter(self,
            original_language_id=None,
            target_language_id=None,
            subject_id=None,
            format_id=None,
            tone_id=None):
        pass

class SentenceExporterAPI(object):
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints
        #self.tokenizer = nltk.pickl

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}/admin/dataManager/parseSentence'.format(endpoint), view_func=self.parseSentence, methods=["POST"])
            self.app.add_url_rule('{}/admin/dataManager/import'.format(endpoint), view_func=self.dataImport, methods=["POST"])
            self.app.add_url_rule('{}/admin/dataManager/export'.format(endpoint), view_func=self.dataExport, methods=["POST"])
            self.app.add_url_rule('{}/admin/dataManager/dataCounter'.format(endpoint), view_func=self.dataCounter, methods=["GET"])

    def parseSentence(self):
        """
        문장 분해 API

        **Parameters**
          #. **"original_string"**: String. 원문의 문장쌍
          #. **"translated_string"**: String, 번역문의 문장쌍

        **Response**
          #. **200**

            .. code-block:: json
               :linenos:

                 {
                   "original_string": [
                     {
                       "paragraph_id": 1,
                       "sentences": [
                         {
                           "sentence_id": 1,
                           "sentence": "우앙 ㅋ 굿 ㅋ"
                         },
                         {
                           "sentence_id": 2,
                           "sentence": "파싱이 잘 됩니다!~"
                         }
                       ]
                     },
                     {
                       "paragraph_id": 2,
                       "sentences": [
                         {
                           "sentence_id": 1,
                           "sentence": "그냥 그렇다"
                         }
                       ]
                     }
                   ],

                   "translated_string": [
                     {
                       "paragraph_id": 1,
                       "sentences": [
                         {
                           "sentence_id": 1,
                           "sentence": "Wow, fuck yeh!"
                         },
                         {
                           "sentence_id": 2,
                           "sentence": "Parser works well!"
                         }
                       ]
                     },
                     {
                       "paragraph_id": 2,
                       "sentences": [
                         {
                           "sentence_id": 1,
                           "sentence": "So so"
                         }
                       ]
                     }
                   ]
                 }

          
        """
        pass

    def dataImport(self):
        """
        데이터 입력
          #. **이 정보는 formdata로 넣기에는 구조가 매우 복잡하니 여기만은 Content-Type: application/json으로 넣도록 한다!**
          #. **Parameters**

            .. code-block:: json
               :linenos:

                 {
                   "original_string": [
                     {
                       "paragraph_id": 1,
                       "sentences": [
                         {
                           "sentence_id": 1,
                           "sentence": "우앙 ㅋ 굿 ㅋ"
                         },
                         {
                           "sentence_id": 2,
                           "sentence": "파싱이 잘 됩니다!~"
                         }
                       ]
                     },
                     {
                       "paragraph_id": 2,
                       "sentences": [
                         {
                           "sentence_id": 1,
                           "sentence": "그냥 그렇다"
                         }
                       ]
                     }
                   ],

                   "translated_string": [
                     {
                       "paragraph_id": 1,
                       "sentences": [
                         {
                           "sentence_id": 1,
                           "sentence": "Wow, fuck yeh!"
                         },
                         {
                           "sentence_id": 2,
                           "sentence": "Parser works well!"
                         }
                       ]
                     },
                     {
                       "paragraph_id": 2,
                       "sentences": [
                         {
                           "sentence_id": 1,
                           "sentence": "So so"
                         }
                       ]
                     }
                   ]
                 }

          #. **Response**
            #. **200**: OK
            #. **210**: Fail, pair missmatch

              .. code-block:: json
                 :linenos:

                 {
                   "paragraph_id": 2,
                   "sentence_id": 3
                 }

            #. **410**: Fail, DB Error

        """
        pass

    def dataCounter(self):
        """
        데이터 통계 파악
          #. **Parameters**
            #. **"original_language_id"**: OPTIONAL, Int, 원어 ID
            #, **"target_language_id"**: OPTIONAL, Int, 번역문 ID
            #. **"subject_id"**: OPTIONAL, Int
            #. **"format_id"**: OPTIONAL, Int
            #. **"tone_id"**: OPTIONAL, Int

          #. **Response**
            #. **200**

              .. code-block:: json
                 :linenos:

                 {
                   "number": 1234
                 }

            #. **410**: Fail
        """
        pass

    def dataExport(self):
        """
        데이터 다운로드
          #. **Parameters**
            #. **"original_language_id"**: OPTIONAL, Int, 원어 ID
            #, **"target_language_id"**: OPTIONAL, Int, 번역문 ID
            #. **"subject_id"**: OPTIONAL, Int
            #. **"format_id"**: OPTIONAL, Int
            #. **"tone_id"**: OPTIONAL, Int

          #. **Response**
            #. **200**: 해당 CSV 다운로드
            #. **410**: 실패

        """
        pass
