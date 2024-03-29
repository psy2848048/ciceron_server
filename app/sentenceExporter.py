# -*- coding: utf-8 -*-

import psycopg2
import io
import os
import traceback
from flask import Flask, request, g, make_response, json, session, redirect, render_template, send_file, json
from datetime import datetime
import nltk
import csv

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

        splitted_paragraph = whole_string.split(paragraph_delimeter)


        for paragraph_id, sentences in enumerate(splitted_paragraph):
            paragraph = {}

            paragraph['paragraph_id'] = paragraph_id + 1
            paragraph['sentences'] = []


            splitted_sentences = self.sentence_detector.tokenize(sentences.strip())
            for sentence_id, sentence in enumerate(splitted_sentences):
                dict_sentence = {}

                dict_sentence['sentence_id'] = sentence_id + 1
                dict_sentence['sentence'] = sentence

                paragraph['sentences'].append(dict_sentence)

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
            , paragraph_delimiter="\\n"
            , whole_original_string=None
            , whole_translated_string=None):

        original_string = self._parseUnitSentences(paragraph_delimiter, whole_original_string)
        translated_string = self._parseUnitSentences(paragraph_delimiter, whole_translated_string)
        return 200, {
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

        # default parameter로 None을 넣어준다
        cursor = self.conn.cursor()

        # TODO : None타입이 아닌 것만 리스트 형태로 넣기, 형태는 "변수명 = %s"
        dict_params = {"original_language_id": original_language_id, "target_language_id": target_language_id,
                       "subject_id": subject_id, "format_id": format_id, "tone_id": tone_id}

        list_params = [original_language_id, target_language_id, subject_id, format_id, tone_id]

        list_params = [list_param for list_param in list_params if list_param]

        # params_notNone = { dict_param for dict_param in dict_params if dict_params.items() is not None}

        params_notNone = {k: v for k, v in dict_params.items() if v is not None}
        query_str_list = []
        for dict_key in params_notNone:
            query_str_list.append(str(dict_key) + " = " + "%s")

        query_where = """SELECT * FROM CICERON.SENTENCES WHERE """
        query = """SELECT * FROM CICERON.SENTENCES"""

        query_str = " and ".join(query_str_list)
        """
			for i in range(len(query_str_list)):
			query += query_str_list[i]
		"""
        query_where += query_str

        if (len(list_params) == 0):
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                #str_result = [str(result).strip('[]')]

                """
                # CSV 파일 write
                f_csv = csv.writer(result, delimiter=',')
                for row in result:
                    f_csv.writerow(row)
                """
                output = io.StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerows(result)
                f = output.getvalue()

            except:
                traceback.print_exc()
                self.conn.rollback()
                return 410, None
        else:
            try:
                cursor.execute(query_where, list_params)
                result = cursor.fetchall()

                # CSV 파일 write
                output = io.StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerows(result)
                f = output.getvalue()

            except:
                traceback.print_exc()
                self.conn.rollback()
                return 410, None

        return (200, f)

    def dataCounter(self,
            original_language_id=None,
            target_language_id=None,
            subject_id=None,
            format_id=None,
            tone_id=None):
        # default parameter로 None을 넣어준다
        cursor = self.conn.cursor()

        # TODO : None타입이 아닌 것만 리스트 형태로 넣기, 형태는 "변수명 = %s"
        dict_params = {"original_language_id": original_language_id, "target_language_id": target_language_id,
                  "subject_id": subject_id, "format_id": format_id, "tone_id": tone_id}

        list_params = [original_language_id, target_language_id, subject_id, format_id, tone_id]

        list_params = [ list_param for list_param in list_params if list_param ]

        # params_notNone = { dict_param for dict_param in dict_params if dict_params.items() is not None}

        params_notNone = { k: v for k, v in dict_params.items() if v is not None}
        query_str_list = []
        for dict_key in params_notNone:
            query_str_list.append(str(dict_key) + " = " + "%s")


        query_where = """SELECT * FROM CICERON.SENTENCES WHERE """
        query = """SELECT * FROM CICERON.SENTENCES"""

        query_str = " and ".join(query_str_list)
        """
            for i in range(len(query_str_list)):
            query += query_str_list[i]
        """
        query_where += query_str

        if (len(list_params) == 0):
            try:
                cursor.execute(query)
                number = len(cursor.fetchall())

            except:
                traceback.print_exc()
                self.conn.rollback()
                return 410, None
        else:
            try:
                cursor.execute(query_where, list_params)
                number = len(cursor.fetchall())

            except:
                traceback.print_exc()
                self.conn.rollback()
                return 410, None

        return 200, number

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
            self.app.add_url_rule('{}/admin/dataManager/export'.format(endpoint), view_func=self.dataExport, methods=["GET"])
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
        # SentenceExporter 인스턴스 생성
        sentenceExporter = SentenceExporter(g.db)

        # requedst에서 original과 translated 받기
        """
        parameters = ciceron_lib.parse_request(request)

        original_string = parameters['original_string']
        translated_string = parameters['translated_string']
        """

        original_string = request.form['original_string']
        translated_string = request.form['translated_string']

        resp_code, parsedSentence = sentenceExporter.parseSentences(whole_original_string = original_string,
                                                                    whole_translated_string= translated_string)
        return make_response(json.jsonify(parsedSentence), resp_code)

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
            #. **"target_language_id"**: OPTIONAL, Int, 번역문 ID
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

        # SentenceExporter 인스턴스 생성
        sentenceExporter = SentenceExporter(g.db)

        original_language_id = request.args.get('original_language_id', None)
        target_language_id = request.args.get('target_language_id')
        subject_id = request.args.get('subject_id')
        format_id = request.args.get('format_id')
        tone_id = request.args.get('tone_id')




        resp_code, number = sentenceExporter.dataCounter(original_language_id, target_language_id,
                                                             subject_id, format_id, tone_id)

        if resp_code == 200:
            return make_response(json.jsonify(number=number), resp_code)

        elif resp_code == 410:

            return make_response(json.jsonify(message="Fail"), resp_code)


    def dataExport(self):
        """
        데이터 다운로드
          #. **Parameters**
            #. **"original_language_id"**: OPTIONAL, Int, 원어 ID
            #. **"target_language_id"**: OPTIONAL, Int, 번역문 ID
            #. **"subject_id"**: OPTIONAL, Int
            #. **"format_id"**: OPTIONAL, Int
            #. **"tone_id"**: OPTIONAL, Int

          #. **Response**
            #. **200**: 해당 CSV 다운로드
            #. **410**: 실패

        """
        # SentenceExporter 인스턴스 생성
        sentenceExporter = SentenceExporter(g.db)

        original_language_id = request.args.get('original_language_id', None)
        target_language_id = request.args.get('target_language_id')
        subject_id = request.args.get('subject_id')
        format_id = request.args.get('format_id')
        tone_id = request.args.get('tone_id')

        resp_code, f = sentenceExporter.exportSentence(original_language_id, target_language_id,
                                                            subject_id, format_id, tone_id)

        if resp_code == 200:

            return send_file(io.BytesIO(f.encode('utf-8')), attachment_filename = 'sentences.csv')

        elif resp_code == 410:

            return make_response(json.jsonify(message="Fail"), resp_code)