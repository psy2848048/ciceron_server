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

    def _organizeProjectParameters(self, **kwargs):
        # Current parameters
        #    id
        #  , original_resource_id
        #  , original_lang_id
        #  , format_id
        #  , subject_id
        #  , registered_timestamp=CURRENTD_TIMESTAMP
        #  , cover_photo_filename -> Catch from upload request
        #  , cover_photo_binary

        params = kwargs
        params['id'] = ciceron_lib.get_new_id(self.conn, "F_PRETRANSLATED_PROJECT")
        params['registered_timestamp'] = datetime.utcnow()
        print(params['registered_timestamp'])

        return params

    def _organizeResourceParameters(self, **kwargs):
        # Current parameters
        #    id
        #  , project_id
        #  , target_language_id
        #  , theme
        #  , description
        #  , tone_id
        #  , read_permission_level
        #  , price
        #  , register_timestamp=CURRENT_TIMESTAMP

        params = kwargs
        params['id'] = ciceron_lib.get_new_id(self.conn, "F_PRETRANSLATED_RESOURCES")
        params['registered_time'] = datetime.utcnow()
        print(params['registered_timestamp'])

        return params

    def _organizeUploadFileParameters(self, **kwargs):
        # Current parameters
        #    id
        #  , project_id
        #  , resource_id
        #  , preview_permission
        #  , file_name
        #  , file_binary

        params = kwargs
        params['id'] = ciceron_lib.get_new_id(self.conn, "F_PRETRANSLATED_RESULT_FILE")
        params['checksum'] = ciceron_lib.calculateChecksum(params['file_binary'])
        return params

    def _organizeDownloadFileParameters(self, **kwargs):
        # Current parameters
        #    id
        #  , resource_id
        #  , is_user
        #  , email
        #  , is_paid
        #  , is_sent
        #  , token
        #  , is_downloaded
        #  , feedback_score

        params = kwargs
        params['id'] = ciceron_lib.get_new_id(self.conn, "F_PRETRANSLATED_DOWNLOADED_USER")
        return params

    def _insert(self, table, **kwargs):
        cursor = self.conn.cursor()
        query_tmpl = """
            INSERT INTO CICERON.{table}
            ({columns})
            VALUES
            ({prepared_statements})
        """
        columns = ','.join( list( kwargs.keys() ) )
        prepared_statements = ','.join( ['%s' for _ in list(kwargs.keys())] )
        query = query_tmpl.format(
                    table=table
                  , columns=columns
                  , prepared_statements=prepared_statements
                  )

        try:
            cursor.execute(query, list( kwargs.values() ) )
        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def _update(self, table, something_id, **kwargs):
        cursor = self.conn.cursor()
        query = """
            UPDATE CICERON.{table}
            SET {value}
            WHERE id = %s
        """

        params = []
        values = []
        for key, value in kwargs.items():
            params.append("{}=%s".format(key))
            values.append(value)

        try:
            query = query.format(
                      table=table
                    , value=", ".join(param_resource)
                    )
            values.append(something_id)
            cursor.execute(query, value)

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def _delete(self, table, something_id):
        cursor = self.conn.cursor()
        query = """
            DELETE FROM CICERON.{table}
            WHERE id = %s
        """

        try:
            query = query.format(table=table)
            cursor.execute(query, (something_id, ))

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def calcChecksumForEmailParams(self, resource_id, email):
        cursor = self.conn.cursor()

        query = """
            SELECT filename, checksum
            FROM CICERON.F_PRETRANSLATED_RESULT_FILE
            WHERE resource_id = %s
        """
        cursor.execute(query, (resource_id, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False, None

        filename, checksum = ret
        hashed_result = ciceron_lib.calculateChecksum(filename, email, checksum)
        return True, hashed_result

    def generateDownloadableLink(self, endpoint, resource_id, email, checksum):
        HOST = ""
        if os.environ.get('PURPOSE') == 'PROD':
            HOST = 'http://ciceron.me'
            
        elif os.environ.get('PURPOSE') == 'DEV':
            HOST = 'http://ciceron.xyz'
        
        else:
            HOST = 'http://localhost:5000'

        params = "?" + '&'.join([
              'resource_id={}'.format(resource_id)
            , 'email={}'.format(email)
            , 'token={}'.format(checksum)
            ])
        link = '/'.join([HOST, endpoint[1:], 'user', 'pretranslated', 'download', params])
        return link

    def checkChecksumFromEmailParams(self, resource_id, email, checksum_from_param):
        can_get, hashed_internal = self.calcChecksumForEmailParams(resource_id, email)
        if hashed_internal == checksum_from_param:
            return True
        else:
            return False

    def checkIsPaid(self, resource_id, email):
        cursor = self.conn.cursor()
        query = """
            SELECT CASE 
                     WHEN is_paid = true THEN true
                     WHEN is_paid = false AND (SELECT points FROM CICERON.F_PRETRANSLATED_RESOURCES WHERE id = %s) > 0 THEN false
                     ELSE true END as is_paid
            FROM CICERON.F_PRETRANSLATED_DOWNLOADED_USER
            WHERE resource_id = %s
              AND email = %s
        """
        cursor.execute(query, (resource_id, request_id, email, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return 2

        is_paid = ret[0]
        if is_paid == True:
            return 0
        else:
            return 1

    def provideCoverPhoto(self, project_id):
        cursor = self.conn.cursor()
        query = """
            SELECT
                cover_photo_filename
              , cover_photo_binary
            FROM CICERON.F_PRETRANSLATED_PROJECT
            WHERE id = %s
        """
        cursor.execute(query, (project_id, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False, None, None

        return True, ret[0], ret[1]

    def provideFile(self, project_id, resource_id, file_id):
        cursor = self.conn.cursor()
        query = """
            SELECT
                filename
              , file_binary
            FROM CICERON.F_PRETRANSLATED_RESULT_FILE
            WHERE id = %s AND resource_id = %s AND project_id = %s
        """
        cursor.execute(query, (file_id, resource_id, project_id, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False, None, None

        return True, ret[0], ret[1]

    def provideFileListOfResource(self, resource_id):
        cursor = self.conn.cursor()
        query = """
            SELECT
                id
              , project_id
              , resource_id
              , preview_permission
            FROM CICERON.F_PRETRANSLATED_RESULT_FILE
            WHERE resource_id = %s
            ORDER BY id ASC
        """
        cursor.execute(query, (resource_id, ))
        columns = [ desc[0] for desc in cursor.description ]
        ret = cursor.fetchall()
        file_list = ciceron_lib.dbToDict(columns, ret)
        for item in file_list:
            can_get, file_name, _ = self.provideFile(item['project_id'], item['resource_id'], item['id'])
            item['file_url'] = '/pretranslated/project/{}/resources/{}/file/{}/{}'.format(item['project_id'], item['resource_id'], item['id'], file_name)

        return file_list

    def provideRequesterList(self, project_id):
        cursor = self.conn.cursor()
	query = """
	    SELECT *
	    FROM CICERON.V_PRETRANSLATED_REQUESTER
	    WHERE project_id = %s
	"""
	cursor.execute(query, (project_id, ))
	column = [col[0] for col in cursor.description]
	requester_list = ciceron_lib.dbToDict(column, ret)

	return requester_list

    def provideTranslatorList(self, project_id):
        cursor = self.conn.cursor()
	query = """
	    SELECT *
	    FROM CICERON.V_PRETRANSLATED_TRANSLATOR
	    WHERE project_id = %s
	"""
	cursor.execute(query, (project_id, ))
	column = [col[0] for col in cursor.description]
	translator_list = ciceron_lib.dbToDict(column, ret)

	return translator_list

    def updateProjectInfo(self, project_id, **kwargs):
        query_check_resource_id = """
            SELECT original_resource_id
            FROM CICERON. F_PRETRANSLATED_PROJECT
            WHERE id = %s
        """

        cursor = self.conn.cursor()
        cursor.execute(query_check_resource_id, (project_id, ))
        original_resource_id = cursor.fetchone()[0]

        param_project = {}
        param_resource = {}
        for key, value in kwargs.items():
            if key in ["original_lang_id", "format_id", "subject_id", "author", "cover_photo_filename", "cover_photo_binary"]:
                param_project[key] = value
            elif key in ["target_language_id", "theme", "description", "tone_id", "read_permission_level", "price"]:
                param_resource[key] = value

        is_ok1 = True
        is_ok2 = True
        if len(param_project) > 0:
            is_ok1 = self._update("F_PRETRANSLATED_PROJECT", project_id, **param_project)

        if len(param_resource) > 0:
            is_ok2 = self._update("F_PRETRANSLATED_RESOURCES", original_resource_id, **param_resource)

        if is_ok1 == False or is_ok2 == False:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def pretranslatedProjectList(self, page=1):
        cursor = self.conn.cursor()
        query = """
            SELECT *
            FROM CICERON.V_PRETRANSLATED_PROJECT
            ORDER BY id DESC
            LIMIT 10
            OFFSET 10 * {}
        """
        cursor.execute(query.format((page-1) * 10))
        columns = [desc[0] for desc in cursor.description]
        ret = cursor.fetchall()

        project_list = ciceron_lib.dbToDict(columns, ret)
        for item in project_list:
            can_get, file_name, _ = self.provideCoverPhoto(item['id'])
            item['cover_photo_url'] = '/pretranslated/project/{}/coverPhoto/{}'.format(item['id'], file_name)

        return pretranslated_list

    def pretranslatedResourceList(self, project_id):
        cursor = self.conn.cursor()
        query = """
            SELECT *
            FROM CICERON.V_PRETRANSLATED_RESOURCE
            WHERE project_id = %s
            ORDER BY id ASC
        """
        cursor.execute(query, (project_id, ))
        columns = [desc[0] for desc in cursor.description]
        ret = cursor.fetchall()

        resource_list = ciceron_lib.dbToDict(columns, ret)
        for item in resource_list:
            can_get, url, _ = self.provideFile(item['project_id'])
            item['file_url'] = url
	    item['requester_list'] = self.provideRequesterList(project_id)
	    item['translator_list'] = self.provideTranslatorList(project_id)

        return resource_list

    def createProject(self, **kwargs):
        params = self._organizeProjectParameters(**kwargs)
        is_ok = self._insert("F_PRETRANSLATED_PROJECT", **params)
        return is_ok, params.get('id')

    def createResource(self, **kwargs):
        params = self._organizeResourceParameters(**kwargs)
        is_ok = self._insert("F_PRETRANSLATED_RESOURCES", **params)
        return is_ok, params.get('id')

    def linkResourceToProject(self, project_id, resource_id):
        cursor = self.conn.cursor()
        query = """
            UPDATE CICERON.F_PRETRANSLATED_PROJECT
            SET original_resource_id = %s
            WHERE id = %s
        """
        try:
            cursor.execute(query, (resource_id, project_id, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def createFile(self, **kwargs):
        params = self._organizeUploadFileParameters(**kwargs)
        is_ok = self._insert("F_PRETRANSLATED_RESULT_FILE", **params)
        return is_ok, params.get('id')

    def updateResource(self, resource_id, **params):
        is_ok = self._update("F_PRETRANSLATED_RESOURCES", resource_id, **parmas)
        return is_ok

    def updateFile(self, file_id, **params):
        is_ok = self._update("F_PRETRANSLATED_RESULT_FILE", file_id, **parmas)
        return is_ok

    def deleteProject(self, project_id):
        is_ok = self._delete("F_PRETRANSLATED_PROJECT", project_id)
        return is_ok

    def deleteResource(self, resource_id):
        is_ok = self._delete("F_PRETRANSLATED_RESOURCES", resource_id)
        return is_ok

    def deleteResultFile(self, file_id):
        is_ok = self._delete("F_PRETRANSLATED_RESULT_FILE", file_id)
        return is_ok

    def addUserAsDownloader(self, resource_id, email):
        cursor = self.conn.cursor()
        query_checkCount = """
            SELECT count(*)
            FROM CICERON.F_PRETRANSLATED_DOWNLOAD_USER
            WHERE id = %s AND resource_id = %s AND email = %s
        """
        cursor.execute(query_checkCount, (file_id, resource_id, email, ))
        cnt = cursor.fetchone()[0]
        if cnt > 0:
            # 같은 유저가 같은 번역물 다운로드 권한을
            # 여러번 Call하는 상황을 막아야 한다.
            return 2

        query_addUser = """
            INSERT INTO CICERON.F_PRETRANSLATED_DOWNLOAD_USER
            (id, resource_id, is_user, email, is_paid, is_sent, is_downloaded, request_timestamp)
            VALUES
            (%s, %s, %s, %s, false, false, false, CURRENT_TIMESTAMP)
        """
        user_id = ciceron_lib.get_user_id(self.conn, email)
        is_user = True if user_id > 0 else False
        new_downloader_id = ciceron_lib.get_new_id(self.conn, "CICERON.F_PRETRANSLATED_DOWNLOAD_USER")

        try:
            cursor.execute(query_addUser, (new_downloader_id, resource_id, is_user, email, ))

        except Exception:
            traceback.print_exc()
            self.conn.rollback()
            return 1

        return 0

    def markAsSent(self, request_id, email):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_PRETRANSLATED_DOWNLOADED_USER
            SET is_sent = true
            WHERE request_id = %s AND email = %s
        """
        try:
            cursor.execute(query, (request_id, email, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def markAsDownloaded(self, request_id, email):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_PRETRANSLATED_DOWNLOADED_USER
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
            UPDATE CICERON.F_PRETRANSLATED_DOWNLOADED_USER
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
            UPDATE CICERON.F_PRETRANSLATED_DOWNLOADED_USER
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

    def getMyDownloadList(self, user_id):
        cursor = self.conn.cursor()
        query = """
            SELECT
                id
              , resource_id
              , is_paid
              , is_sent
              , is_downloaded
              , feedback_score
              , request_timestamp
            FROM CICERON.V_PRETRANSLATED_MY_DOWNLOAD
            WHERE user_id = %s
            ORDER BY request_timestamp DESC
        """
        cursor.execute(query, (user_id, ))
        column = [ desc[0] for desc in cursor.description ]
        ret = cursor.fetchall()
        return ciceron_lib.dbToDict(column, ret)


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
            self.app.add_url_rule('{}/admin/pretranslated/createProject'.format(endpoint), view_func=self.createProject, methods=["POST"])
            #self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/markAsPaid'.format(endpoint), view_func=self.pretranslatedMarkAsPaid, methods=["GET"])
            #self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/rate'.format(endpoint), view_func=self.pretranslatedRateResult, methods=["POST"])
            #self.app.add_url_rule('{}/user/pretranslated/upload'.format(endpoint), view_func=self.uploadPretranslationPage)
            #self.app.add_url_rule('{}/user/pretranslated/stoa'.format(endpoint), view_func=self.pretranslatedList, methods=["GET"])
            #self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/preview'.format(endpoint), view_func=self.providePreviewBinary)
            #self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/addUserForDownload'.format(endpoint), view_func=self.addUserForDownload, methods=["POST"])
            #self.app.add_url_rule('{}/user/pretranslated/request/<int:request_id>/provideLink'.format(endpoint), view_func=self.issueDownloadableLinkAndSendToMail, methods=["POST"])
            #self.app.add_url_rule('{}/user/pretranslated/download/'.format(endpoint), view_func=self.download, methods=["GET"])

    ########## Admin side ############

    @admin_required
    def pretranslatedCreateProject(self):
        """
        프로젝트 열기

        **Parameters**
          #. **"original_lang_id"**: 원 언어 ID
          #. **"format_id"**: 포맷 ID
          #. **"subject_id"**: 주제 ID
          #. **"author"**: 원작자
          #. **"cover_photo"**: 사진파일

        **Response**
          #. **200**: 추가 성공
            .. code-block:: json
               :linenos:

               {
                 "project_id": 1 // Request ID
               }

           #. **410**: 추가 실패 

        """
        pretranslatedObj = Pretranslated(g.db)
        parameters = ciceron_lib.parse_request(request)
        for key in parameters.keys():
            if key not in ['original_resource_id', 'original_lang_id', 'format_id', 'subject_id', 'author', 'cover_photo']:
                return make_response("Bad request", 400)

        cover_photo_obj = request.files['cover_photo']
        parameters.pop('cover_photo')
        parameters['cover_photo_filename'] = cover_photo_obj.filename
        parameters['cover_photo_binary'] = cover_photo_obj.read()
        is_ok, project_id = pretranslatedObj.createProject(**parameters)
        if is_ok == True:
            g.db.commit()
            return make_response(json.jsonify(
                message="OK", project_id=project_id), 200)

        else:
            g.db.rollback()
            return make_response("Fail", 410)

    @admin_required
    def pretranslatedCreateResource(self):
        """
        번역물 리소스 생성 API

        **Parameters**
          #. **"project_id"**: 프로젝트 ID
          #. **"target_language_id"**: 번역 타겟 언어 ID (원 언어일수도 있음)
          #. **"theme"**: 제목
          #. **"description"**: 번역물 설명
          #. **"tone_id"**: 번역물 톤 ID
          #. **"read_permission_level"**: 접근 레벨
          #. **"price"**: 가격 in USD
          #. **"is_original"**: Boolean

        **Response**
          #. **200**: 게시 성공
            .. code-block:: json
               :linenos:

               {
                 "resource_id": 1 // Request ID
               }

           #. **410**: 게시 실패 

        """
        pretranslatedObj = Pretranslated(g.db)
        parameters = ciceron_lib.parse_request(request)
        for key in parameters.keys():
            if key not in ['project_id', 'target_language_id', 'theme', 'description', 'tone_id', 'read_permission_level', 'price', 'is_original']:
                return make_response("Bad request", 400)
        is_original = parameters['is_original']
        parameters.pop('is_original')
        is_ok, resource_id = pretranslatedObj.createResource(**parameters)

        if is_ok == False:
            g.db.rollback()
            return make_response("Fail", 410)

        if ciceron_lib.parameter_to_bool(is_original) == True:
            is_linked = pretranslatedObj.linkResourceToProject(parameters['project_id'], resource_id)

            if is_linked == False:
                g.db.rollback()
                return make_response("Fail", 410)

        else:
            g.db.commit()
            return make_response(json.jsonify(
                resource_id=resource_id
              , message="OK"), 200)

    @admin_required
    def pretranslatedCreateFile(self):
        """
        파일 업로드 API

        **Parameters**
          #. **"project_id"**: 프로젝트 ID
          #. **"resource_id"**: Resource ID
          #. **"preview_permission"**: 미리보기 권한
          #. **"file_list[]"**: 파일 목록

        **Response**
          #. **200**: 게시 성공
            .. code-block:: json
               :linenos:

               {
                 "resource_id": 1 // Request ID
               }

           #. **410**: 게시 실패 

        """
        pretranslatedObj = Pretranslated(g.db)
        parameters = ciceron_lib.parse_request(request)
        upload_files = request.files.getlist("file_list[]")
        parameters.pop('file_list[]')
        for upload_file in upload_files:
            parameters['file_name'] = upload_file.filename
            parameters['file_binary'] = upload_file.read()
            is_ok, file_id = pretranslatedObj.createFile(**parameters)
            if is_ok == False:
                g.db.rollback()
                return make_response("Fail", 410)

        else:
            g.db.commit()
            return make_response(json.jsonify(
              , message="OK"), 200)

    @admin_required
    def pretranslatedUpdateProjectInfo(self, project_id):
        """
        프로젝트 정보 업데이트
        **Parameters (ALL OPTIONAL)**
          #. **"project_id"**: Project ID (URL)
          #. **"original_lang_id"**: 원문 언어
          #. **"format_id"**: 포맷 ID
          #. **"subject_id"**: 주제 ID
          #. **"author"**: 원작자명
          #. **"cover_photo"**: 커버 사진
          #. **"target_laguage_id"**: 번역문 언어
          #. **"theme"**: 제목
          #. **"description"**: 설명
          #. **"tone_id"**: 톤 ID
          #. **"read_permission_level"**: 권한 ID

        **Response**
          #. **200**: OK
          #. **410**: Fail
          
        """
        pretranslatedObj = Pretranslated(g.db)
        parameters = ciceron_lib.parse_request(request)
        if "cover_photo" in request:
            cover_photo_obj = request.files['cover_photo']
            parameters['cover_photo_filename'] = cover_photo_obj.filename
            parameters['cover_photo_binary'] = cover_photo_obj.read()
            parameters.pop('cover_photo')

        is_ok = pretranslatedObj.updateProjectInfo(project_id, **parameters)
        if is_ok == True:
            g.db.commit()
            return make_response(json.jsonify(
              , message="OK"), 200)

        else:
            g.db.rollback()
            return make_response("Fail", 410)

    @admin_required
    def pretranslatedUpdateResourceInfo(self):
        """
        """
        pass

    @admin_required
    def pretranslatedUpdateFileInfo(self):
        """
        """
        pass

    @admin_required
    def pretranslatedDeleteProject(self, project_id):
        """
        """
        pass

    @admin_required
    def pretranslatedDeleteResource(self, resource_id):
        """
        """
        pass

    @admin_required
    def pretranslatedDeleteFile(self, file_id):
        """
        """
        pass

    @admin_required
    def pretranslatedControlProjectWeb(self):
        return render_template('uploadPretranslated.html')

    @admin_required
    def pretranslatedControlResourceWeb(self):
        return render_template('TBD')

    @admin_required
    def pretranslatedControlFileWeb(self):
        return render_template('TBD')










    ######################## User side #####################

    def addUserForDownload(self, project_id, resource_id):
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

    @login_required
    def pretranslatedMarkAsPaid(self, project_id, request_id):
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

    def pretranslatedMarkAsSent(self, project_id, resource_id):
        """
        """
        pass

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

    def pretranslatedRateResult(self, project_id, resource_id):
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

    @login_required
    def pretranslatedMyDownloadedList(self):
        """
        """
        pass

    @login_required
    def pretranslatedProvideCoverPhoto(self, project_id):
        """
        """
        pass

    @login_required
    def pretranslatedProvideResource(self, project_id, resource_id):
        """
        """
        pass

    @login_required
    def pretranslatedProvideFiles(self, project_id, request_id, file_id):
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

