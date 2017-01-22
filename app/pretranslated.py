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
        return True, hashed_result

    def generateDownloadableLink(self, endpoint, request_id, email, checksum):
        HOST = ""
        if os.environ.get('PURPOSE') == 'PROD':
            HOST = 'http://ciceron.me'
            
        elif os.environ.get('PURPOSE') == 'DEV':
            HOST = 'http://ciceron.xyz'
        
        else:
            HOST = 'http://localhost:5000'

        params = "?" + '&'.join([
              'request_id={}'.format(request_id)
            , 'email={}'.format(email)
            , 'token={}'.format(checksum)
            ])
        link = '/'.join([HOST, endpoint[1:], 'user', 'pretranslated', 'download', params])
        return link

    def checkChecksumFromEmailParams(self, request_id, email, checksum_from_param):
        can_get, hashed_internal = self.calcChecksumForEmailParams(request_id, email)
        if hashed_internal == checksum_from_param:
            return True
        else:
            return False

    def checkIsPaid(self, request_id, email):
        cursor = self.conn.cursor()
        query = """
            SELECT CASE 
                     WHEN is_paid = true THEN true
                     WHEN is_paid = false AND (SELECT points FROM CICERON.F_PRETRANSLATED WHERE id = %s) > 0 THEN false
                     ELSE true END as is_paid
            FROM CICERON.F_DOWNLOAD_USERS_PRETRANSLATED
            WHERE request_id = %s
              AND email = %s
        """
        cursor.execute(query, (request_id, request_id, email, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return 2

        is_paid = ret[0]
        if is_paid == True:
            return 0
        else:
            return 1

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

    def providePreviewBinary(self, request_id):
        cursor = self.conn.cursor()

        query = """
            SELECT preview_filename, preview_binary
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
    """
    addUserForDownload -> (markAsPaid) -> provideLink -> download
    """
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}/admin/pretranslated/uploadPretranslated'.format(endpoint), view_func=self.uploadPretranslation, methods=["POST"])
            self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/markAsPaid'.format(endpoint), view_func=self.pretranslatedMarkAsPaid, methods=["GET"])
            self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/rate'.format(endpoint), view_func=self.pretranslatedRateResult, methods=["POST"])
            self.app.add_url_rule('{}/user/pretranslated/upload'.format(endpoint), view_func=self.uploadPretranslationPage)
            self.app.add_url_rule('{}/user/pretranslated/stoa'.format(endpoint), view_func=self.pretranslatedList, methods=["GET"])
            self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/preview'.format(endpoint), view_func=self.providePreviewBinary)
            self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/addUserForDownload'.format(endpoint), view_func=self.addUserForDownload, methods=["POST"])
            self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/provideLink'.format(endpoint), view_func=self.issueDownloadableLinkAndSendToMail, methods=["POST"])
            self.app.add_url_rule('{}/user/pretranslated/download/'.format(endpoint), view_func=self.download, methods=["GET"])

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
        preview_filename = previewFileObj.filename
        preview_file_binary = previewFileObj.read()

        request_dict = {
                "translator_id": ciceron_lib.get_user_id(g.db, parameters['translator_email'])
              , "original_lang_id": parameters['original_lang_id']
              , "target_lang_id": parameters['target_lang_id']
              , "format_id": parameters['format_id']
              , "subject_id": parameters['subject_id']
              , "points": float(parameters['points'])
              , "filename": filename
              , "preview_filename": preview_filename
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
            return redirect('{}/user/pretranslated/stoa'.format(self.endpoints[-1]), 302)

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
        기 번역된 목록 리스트

        **Parameters**
          #. **"page"**: 페이지 (OPTIONAL)

        **Response**
          **200**
            .. code-block:: json
               :linenos:

               {
                 "data": [
                   {
                     "id": 13,
                     "translator_id": 4,
                     "translator_email": "admin@ciceron.me",
                     "original_lang_id": 1,
                     "original_lang": "Korean",
                     "target_lang_id": 2,
                     "target_lang": "English(USA)",
                     "format_id": 0,
                     "format": null,
                     "subject_id": 0,
                     "subject": null,
                     "tone_id": 0,
                     "tone": null,
                     "registered_time": "Sun, 22 Jan 2017 07:23:47 GMT",
                     "points": 0,
                     "theme_text": "Mail test",
                     "filename": "전문연.pdf",
                     "description": "Mail test"
                   }
                 ]
               }
          
        """
        pretranslatedObj = Pretranslated(g.db)
        page = int(request.args.get('page', 1))
        result = pretranslatedObj.pretranslatedList(page)
        return make_response(json.jsonify(data=result), 200)
    
    def providePreviewBinary(self, request_id):
        """
        번역 파일 다운로드

        **Parameters**
          **"request_id"**: Integer, URL에 직접 입력

        **Response**
          **200**: 다운로드 실행

          **410**: Checksum 에러

          **411**: 다운로드 완료 마킹 실패

        """
        pretranslatedObj = Pretranslated(g.db)

        is_ok, filename, binary = pretranslatedObj.providePreviewBinary(request_id)
        if is_ok == True:
            return send_file(binary, attachment_filename=filename)

        else:
            return make_response(json.jsonify(message="DB error"), 411)

    def addUserForDownload(self, request_id):
        """
        **Parameters**
          #. **"email"**: 이메일. 프론트에서는 로그인되어 있다면 세션의 'useremail'을 따 와서 자동으로 입력했으면 하는 소망이 있음.
          #. **"request_id"**: 구매한 번역물의 ID. URL에 직접 삽입

        **Response**
          **200**: 성공

          **410**: 똑같은 번역물 중복구매시도
          
          **411**: DB Error

        """
        pretranslatedObj = Pretranslated(g.db)
        parameters = ciceron_lib.parse_request(request)
        email = parameters['email']
        # 다운로드한 유저 목록에 추가
        is_added = pretranslatedObj.addUserAsDownloader(request_id, email)
        if is_added == 2:
            g.db.rollback()
            return make_response(json.jsonify(message="Multiple request in one request_id"), 410)
        elif is_added == 1:
            g.db.rollback()
            return make_response(json.jsonify(message="DB error"), 411)
        else:
            g.db.commit()
            return make_response(json.jsonify(message="OK"), 200)

    def issueDownloadableLinkAndSendToMail(self, request_id):
        """
        구매한 번역 메일로 링크 전송

        **Parameters**
          #. **"email"**: 이메일. 프론트에서는 로그인되어 있다면 세션의 'useremail'을 따 와서 자동으로 입력했으면 하는 소망이 있음.
          #. **"request_id"**: 구매한 번역물의 ID. URL에 직접 입력

        **Response**
          **200**: 성공

          **411**: 금액지불요함

          **412**: 주어진 Request_id인 번역물이 존재하지 않음

          **413**: 메일 전송 실패

        """
        pretranslatedObj = Pretranslated(g.db)
        parameters = ciceron_lib.parse_request(request)
        email = parameters['email']

        # 보안을 위하여 Token 제작
        is_issued, checksum = pretranslatedObj.calcChecksumForEmailParams(request_id, email)
        if is_issued == False:
            g.db.rollback()
            return make_response(json.jsonify(
                message="No pretranslated result by given request_id")
                , 412)

        # 지불여부 체크
        is_paid = pretranslatedObj.checkIsPaid(request_id, email)
        if is_paid == False:
            return make_response(json.jsonify(message="Need payment"), 411)

        # 링크 제작하고 메일로 전송
        downloadable_link = pretranslatedObj.generateDownloadableLink(self.endpoints[-1], request_id, email, checksum)
        f = open('templates/pretranslatedDownloadMail.html', 'r')
        mail_content = f.read().format(downloadable_link=downloadable_link)
        f.close()
        try:
            ciceron_lib.send_mail(
                    email
                  , "Here is the link of your download request!"
                  , mail_content
                  )
        except:
            g.db.rollback()
            return make_response(json.jsonify(
                message="Mail send failure")
                , 413)

        g.db.commit()
        return make_response(json.jsonify(message="OK"), 200)

    def download(self):
        """
        번역 파일 다운로드

        **Parameters**
          #. **"email"**: 이메일
          #. **"request_id"**: Request ID
          #. **"token"**: 정당한 의뢰인지 알아보는 Token

        **Response**
          **200**: 다운로드 실행

          **410**: Checksum 에러

          **411**: 다운로드 완료 마킹 실패

        """
        pretranslatedObj = Pretranslated(g.db)
        email = request.args['email']
        request_id = request.args['request_id']
        checksum_from_param = request.args['token']

        is_ok = pretranslatedObj.checkChecksumFromEmailParams(request_id, email, checksum_from_param)
        if is_ok == False:
            g.db.rollback()
            return make_response(json.jsonify(message="Auth error"), 410)

        else:
            is_marked = pretranslatedObj.markAsDownloaded(request_id, email)
            if is_marked == True:
                g.db.commit()
                can_provide, filename, binary = pretranslatedObj.provideBinary(request_id)
                return send_file(binary, attachment_filename=filename)
            else:
                g.db.rollback()
                return make_response(json.jsonify(message="DB error"), 411)

