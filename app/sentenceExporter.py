# -*- coding: utf-8 -*-

import psycopg2
import io
import os
import traceback
from flask import Flask, request, g, make_response, json, session, redirect, render_template, send_file, json
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
        self.sentence_detector = nltk.data.load('tokenizers/punkt/english.pickle')

    def _parseUnitSentences(self, paragraph_delimeter, whole_string):
        result = []

        splitted_paragraph = whole_string.split(paragraph_delimiter)

        for paragraph_id, sentences in enumerate(splitted_paragraph):
            paragraph = {}

            paragraph['paragraph_id'] = paragraph_id
            paragraph['sentences'] = []

            splitted_sentences = self.sentence_detector.tokenize(whole_paragraph.strip())
            for sentence_id, sentence in enumerate(splitted_sentences):
                sentence = {}

                sentence['sentence_id'] = sentence_id
                sentence['sentence'] = sentence

                paragraph['sentences'].append(sentence)

            result.append(paragraph)

        return result

    def _importUnitSentence(self,
            original_language_id, target_language_id,
            subject_id, format_id, tone_id,
            paragraph_id, sentence_id,
            original_sentence, translated_sentence):
        cursor = self.conn.cursor()
        query = """
            INSERT INTO CICERON.SENTENCES
            (
                id,
                original_language_id,
                target_language_id,
                subject_id,
                format_id,

                tone_id,
                paragraph_id,
                sentence_id,
                original_sentence,
                translated_sentence
            )
            VALUES
            (%s, %s, %s, %s, %s,
             %s, %s, %s, %s, %s)
        """
        new_sentence_id = ciceron_lib.get_new_id(self.conn, "SENTENCES")
        try:
            cursor.execute(query, (
                new_sentence_id, original_language_id, target_language_id, subject_id, format_id,
                tone_id, paragraph_id, sentence_id, original_sentence, translated_sentence, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def parseSentences(self
            , paragraph_delimiter
            , whole_original_string
            , whole_translated_string):

        original_string = self._parseUnitSentences(paragraph_delimiter, whole_original_string)
        translated_string = self._parseUnitSentences(paragraph_delimiter, whole_translated_string)
        return {
                    "original_string": original_string
                  , "translated_string": translated_string
                }


    def importSentences(self, jsonData):
        original_language_id = jsonData['original_language_id']
        target_language_id = jsonData['target_language_id']
        subject_id = jsonData['subject_id']
        format_id = jsonData['format_id']
        tone_id = jsonData['tone_id']

        for unitParagraph in jsonData['data']:
            paragraph_id = unitParagraph['paragraph_id']


            for unitSentence in unitParagraph['sentences']:
                # TODO : origin_sentence 와 translated_sentence 존재 여부를 체크하기

                """두가지 방법이 존재
                  1. try ~ exception 으로 처리하거나
                  2. if 문으로 처리

                  try ~ exception으로 처리함
                """

                try:
                    # if 문으로 예외처리 original_sentence나 translated_sentence가 없을 때
                    if unitSentence.get('original_sentence') is None:
                        return 210
                    if unitSentence.get('translated_sentence') is None:
                        return 210

                    sentence_id = unitSentence['sentence_id']
                    original_sentence = unitSentence['original_sentence']
                    translated_sentence = unitSentence['translated_sentence']




                    is_succeeded = self._importUnitSentence(
                                       original_language_id
                                     , target_language_id
                                     , subject_id, format_id, tone_id
                                     , paragraph_id, sentence_id
                                     , original_sentence, translated_sentence)


                    if is_succeeded == False:
                        print('Error!')
                        print('Paragraph ID: {}  |  Sentence ID: {}'.\
                                format(paragraph_id, sentence_id))
                        self.conn.rollback()
                        return 410

                # KeyError 예외처리
                except KeyError:
                    return 210

        return 200

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
                   "original_language_id": 1,
                   "target_language_id": 2,
                   "subject_id": 3,
                   "format_id": 3,
                   "tone_id":2,
                   "data": [
                     {
                       "paragraph_id": 1,
                       "sentences": [
                         {
                           "sentence_id": 1,
                           "original_sentence": "우앙 ㅋ 굿 ㅋ",
                           "translated_sentence": "Wow, fuck yeh!"
                         },
                         {
                           "sentence_id": 2,
                           "original_sentence": "파싱이 잘 됩니다!~",
                           "translated_sentence": "Wow, fuck yeh!"
                         }
                       ]
                     },
                     {
                       "paragraph_id": 2,
                       "sentences": [
                         {
                           "sentence_id": 1,
                           "original_sentence": "그냥 그렇다",
                           "translated_sentence": "So so"
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
        # SentenceExporter 인스턴스 생성
        sentenceExporter = SentenceExporter(g.db)

        # parse_request 함수로 request json 파싱
        jsonParameter = ciceron_lib.parse_request(request)

        resp_code = sentenceExporter.importSentences(jsonParameter)

        if resp_code == 200:
            g.db.commit()
            return make_response("OK", 200)

        elif resp_code == 210:
            return make_response("fail, pair missmatch", 210)

        elif resp_code == 410:
            return make_response("Fail DB error", 410)


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
