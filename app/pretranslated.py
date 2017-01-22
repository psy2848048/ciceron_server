# -*- coding: utf-8 -*-

import psycopg2
import io
import traceback
from flask import Flask, request, g, make_response, json, session, redirect, render_template
from datetime import datetime
try:
    import ciceron_lib
except:
    from . import ciceron_lib

try:
    from ciceron_lib import login_required, admin_required
except:
    from .ciceron_lib import login_required, admin_required

class Pretranslated(object):
    def __init__(self, conn):
        self.conn = conn

    def _organizeParameters(self, **kwargs):
        # Current parameters
        #    id
        #  , translator_id
        #  , original_lang_id
        #  , target_lang_id
        #  , format_id
        #  , subject_id
        #  , registered_time=CURRENTD_TIMESTAMP
        #  , points
        #  , filename -> Catch from upload request
        #  , theme_text
        #  , description
        #  , checksum=[check_inside]
        #  , tone_id
        #  , file_binary
        #  , preview_binary

        params = kwargs
        params['id'] = ciceron_lib.get_new_id(self.conn, "F_PRETRANSLATED")
        params['registered_time'] = datetime.utcnow()
        print(params['registered_time'])
        params['checksum'] = ciceron_lib.calculateChecksum(kwargs['file_binary'])

        return params

    def calcChecksumForEmailParams(self, request_id, email):
        cursor = self.conn.cursor()

        query = """
            SELECT filename, checksum
            FROM CICERON.F_PRETRANSLATED
            WHERE id = %s
        """
        cursor.execute(query, (request_id, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False, None

        filename, checksum = ret
        hashed_result = ciceron_lib.calculateChecksum(filename, email, checksum)
        return hashed_result

    def checkChecksumFromEmailParams(self, request_id, email, checksum_from_param):
        hashed_internal = self._calcChecksumForEmailParams(request_id, email)
        if hashed_internal == checksum_from_param:
            return True
        else:
            return False

    def pretranslatedList(self, page=1):
        cursor = self.conn.cursor()
        query = """
            SELECT 
                id
              , translator_id
              , translator_email
              , original_lang_id
              , original_lang
              , target_lang_id
              , target_lang
              , format_id
              , format
              , subject_id
              , subject
              , tone_id
              , tone
              , registered_time
              , points
              , theme_text
              , filename
              , description
            FROM CICERON.V_PRETRANSLATED
            ORDER BY registered_time
            LIMIT 10
            OFFSET 10 * {}
        """
        cursor.execute(query.format((page-1) * 10))
        columns = [desc[0] for desc in cursor.description]
        ret = cursor.fetchall()
        pretranslated_list = ciceron_lib.dbToDict(columns, ret)
        return pretranslated_list

    def uploadPretranslatedResult(self, **kwargs):
        cursor = self.conn.cursor()
        query_tmpl = """
            INSERT INTO CICERON.F_PRETRANSLATED
            ({columns})
            VALUES
            ({prepared_statements})
        """
        params = self._organizeParameters(**kwargs)
        columns = ','.join( list( params.keys() ) )
        prepared_statements = ','.join( ['%s' for _ in list(params.keys())] )
        query = query_tmpl.format(
                    columns=columns
                  , prepared_statements=prepared_statements
                  )

        try:
            cursor.execute(query, list( params.values() ) )
        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False, None

        return True, kwargs.get('id')

    def provideBinary(self, request_id):
        cursor = self.conn.cursor()

        query = """
            SELECT filename, file_binary
            FROM CICERON.F_PRETRANSLATED
            WHERE id = %s
        """
        cursor.execute(query, (request_id, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False, None, None

        filename, binary = ret
        return True, filename, io.BytesIO(binary)

    def providePreview(self, request_id):
        cursor = self.conn.cursor()

        query = """
            SELECT filename, preview_binary
            FROM CICERON.F_PRETRANSLATED
            WHERE id = %s
        """
        cursor.execute(query, (request_id, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False, None, None

        filename, binary = ret
        return True, filename, io.BytesIO(binary)

    def addUserAsDownloader(self, request_id, email):
        cursor = self.conn.cursor()
        query_checkCount = """
            SELECT count(*)
            FROM CICERON.F_DOWNLOAD_USERS_PRETRANSLATED
            WHERE request_id = %s AND email = %s
        """
        cursor.execute(query_checkCount, (request_id, email, ))
        cnt = cursor.fetchone()[0]
        if cnt > 0:
            # 같은 유저가 같은 번역물 다운로드 권한을
            # 여러번 Call하는 상황을 막아야 한다.
            return 2

        query_addUser = """
            INSERT INTO CICERON.F_DOWNLOAD_USERS_PRETRANSLATED
            (request_id, email, is_paid, is_downloaded)
            VALUES
            (%s, %s, false, false)
        """
        try:
            cursor.execute(query_addUser, (request_id, email, ))

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return 1

        return 0

    def markAsDownloaded(self, request_id, email):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_DOWNLOAD_USERS_PRETRANSLATED
            SET is_downloaded = true
            WHERE request_id = %s AND email = %s
        """
        try:
            cursor.execute(query, (request_id, email, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def markAsPaid(self, request_id, email):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_DOWNLOAD_USERS_PRETRANSLATED
            SET is_paid = true
            WHERE request_id = %s AND email = %s
        """
        try:
            cursor.execute(query, (request_id, email, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def rateTranslatedResult(self, request_id, email, score):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_DOWNLOAD_USERS_PRETRANSLATED
            SET feedback_score = %s
            WHERE request_id = %s AND email = %s
        """
        try:
            cursor.execute(query, (score, request_id, email, ))
        except:
            traceback.print_exc()
            self.conn.cursor()
            return False

        return True


class PretranslatedAPI(object):
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}/admin/pretranslated/uploadPretranslated'.format(endpoint), view_func=self.uploadPretranslation, methods=["POST"])
            self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/marAsPaid'.format(endpoint), view_func=self.pretranslatedMarkAsPaid, methods=["GET"])
            self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/rate'.format(endpoint), view_func=self.pretranslatedRateResult, methods=["POST"])
            self.app.add_url_rule('{}/user/pretranslated/upload'.format(endpoint), view_func=self.uploadPretranslationPage)
            self.app.add_url_rule('{}/user/pretranslated/stoa'.format(endpoint), view_func=self.pretranslatedList)

    @admin_required
    def uploadPretranslation(self):
        """
        미리 번역해놓은 결과물 업로드 API

        **Parameters**
          #. **"translator_email"**: 작업한 번역가 이메일
          #. **"original_lang_id"**: 원 언어 ID
          #. **"target_lang_id"**: 타겟 언어 ID
          #. **"format_id"**: 포멧 ID
          #. **"subject_id"**: 주제 ID
          #. **"points"**: 판매할 가격. 0이면 프로모션
          #. **"file"**: 업로드할 파일 파이너리
          #. **"previewFile"**: 미리보기 파일 바이너리
          #. **"theme_text"**: 제목
          #. **"description"**: 번역물 설명
          #. **"tone_id"**: 의뢰물의 대체적 톤 ID

        **Response**
          #. **200**: 게시 성공
            .. code-block:: json
               :linenos:

               {
                 "request_id": 1 // Request ID
               }

           #. **410**: 게시 실패 

        """
        pretranslatedObj = Pretranslated(g.db)
        parameters = ciceron_lib.parse_request(request)

        fileObj = request.files['file']
        filename = fileObj.filename
        file_binary = fileObj.read()

        previewFileObj = request.files['previewFile']
        preview_file_binary = previewFileObj.read()

        request_dict = {
                "translator_id": ciceron_lib.get_user_id(g.db, parameters['translator_email'])
              , "original_lang_id": parameters['original_lang_id']
              , "target_lang_id": parameters['target_lang_id']
              , "format_id": parameters['format_id']
              , "subject_id": parameters['subject_id']
              , "points": float(parameters['points'])
              , "filename": filename
              , "theme_text": parameters['theme_text']
              , "description": parameters['description']
              , "tone_id": parameters['tone_id']
              , "file_binary": file_binary
              , "preview_binary": preview_file_binary
                }
        is_uploaded, request_id = pretranslatedObj.uploadPretranslatedResult(**request_dict)
        if is_uploaded == True:
            g.db.commit()
            return make_response(json.jsonify(
                request_id=request_id
              , message="OK"), 200)

        else:
            g.db.rollback()
            return make_response(json.jsonify(
                request_id=request_id
              , message="Fail"), 410)

    @login_required
    def pretranslatedMarkAsPaid(self, request_id):
        """
        유저 가격 지불 후 지불처리 하는 함수
        
        **Parameters**
          #. **"request_id"**: Request ID. URL에 직접 삽입
        
        **Response**
          #. **200**: OK
          #. **405**: Fail

        """
        pretranslatedObj = Pretranslated(g.db)
        email = session['useremail']

        is_marked = pretranslatedObj.markAsPaid(request_id, email)

        if is_marked == True:
            g.db.commit()
            return redirect('/pretranslated/stoa', 302)

        else:
            g.db.rollback()
            return make_response(json.jsonify(
                message="Fail"),
                405)

    @admin_required
    def uploadPretranslationPage(self):
        return render_template('uploadPretranslated.html')

    @login_required
    def pretranslatedRateResult(self, request_id):
        """
        유저 가격 지불 후 지불처리 하는 함수
        
        **Parameters**
          #. **"score"**: 1-5점까지의 피드백 점수
        
        **Response**
          #. **200**: OK
          #. **405**: Fail

        """
        pretranslatedObj = Pretranslated(g.db)
        email = session['useremail']
        parameters = ciceron_lib.parse_request(request)
        score = parameters['score']

        is_rated = pretranslatedObj.rateTranslatedResult(request_id, email, score)

        if is_rated == True:
            g.db.commit()
            return make_response(json.jsonify(
                message="OK"),
                200)

        else:
            g.db.rollback()
            return make_response(json.jsonify(
                message="Fail"),
                405)

    def pretranslatedList(self):
        """
        리스트

        **Parameters**
          #. **"page"**: 페이지 (OPTIONAL)

        **Response**
          
        """
        pretranslatedObj = Pretranslated(g.db)
        page = int(request.args.get('page', 1))
        result = pretranslatedObj.pretranslatedList(page)
        return make_response(json.jsonify(data=result), 200)

