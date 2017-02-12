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
        params['register_timestamp'] = datetime.utcnow()
        print(params['register_timestamp'])

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
        params['register_timestamp'] = datetime.utcnow()
        print(params['register_timestamp'])

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

    def _hrefTagMaker(self, links):
        base_link = """<br><a href="{downloadable_link}">{downloadable_link}</a> [{idx}]"""
        link_list = []
        for idx, link in enumerate(links):
            link_list.append(base_link.format(downloadable_link=link, idx=idx+1))

        return link_list

    def calcUnitChecksumForEmailParams(self, resource_id, file_id, email):
        cursor = self.conn.cursor()

        query = """
            SELECT file_name, checksum
            FROM CICERON.F_PRETRANSLATED_RESULT_FILE
            WHERE id = %s
        """
        cursor.execute(query, (file_id, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False, None

        hashed_result = ciceron_lib.calculateChecksum(resource_id, ret[0], email, ret[1])
        return True, hashed_result

    def calcChecksumForEmailParams(self, resource_id, email):
        cursor = self.conn.cursor()

        query = """
            SELECT id
            FROM CICERON.F_PRETRANSLATED_RESULT_FILE
            WHERE resource_id = %s
        """
        cursor.execute(query, (resource_id, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False, None

        hashed_result_list = []
        for file_id in ret:
            _, hashed_result = self.calcUnitChecksumForEmailParams(resource_id, file_id, email)
            hashed_result_list.append(
                    {
                        "file_id": file_id,
                        "checksum": hashed_result
                    }
                )

        return True, hashed_result_list

    def generateDownloadableLink(self, endpoint, resource_id, file_id, email, checksum):
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
            , 'file_id={}'.format(file_id)
            ])
        link = '/'.join([HOST, endpoint[1:], 'user', 'pretranslated', 'download', params])
        return link

    def checkChecksumFromEmailParams(self, resource_id, file_id, email, checksum_from_param):
        can_get, hashed_internal = self.calcUnitChecksumForEmailParams(resource_id, file_id, email)
        if hashed_internal == checksum_from_param:
            return True
        else:
            return False

    def checkIsPaid(self, resource_id, email):
        cursor = self.conn.cursor()
        query = """
            SELECT CASE 
                     WHEN is_paid = true THEN true
                     WHEN is_paid = false AND (SELECT price FROM CICERON.F_PRETRANSLATED_RESOURCES WHERE id = %s) > 0 THEN false
                     ELSE true END as is_paid
            FROM CICERON.F_PRETRANSLATED_DOWNLOADED_USER
            WHERE resource_id = %s
              AND email = %s
        """
        cursor.execute(query, (resource_id, resource_id, email, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return 2

        is_paid = ret[0]
        print(is_paid)
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

    def provideFile(self, resource_id, file_id):
        cursor = self.conn.cursor()
        query = """
            SELECT
                file_name
              , file_binary
            FROM CICERON.F_PRETRANSLATED_RESULT_FILE
            WHERE id = %s AND resource_id = %s
        """
        cursor.execute(query, (file_id, resource_id, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False, None, None

        return True, ret[0], ret[1]

    def provideFileListOfResource(self, resource_id, endpoint):
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
            can_get, file_name, _ = self.provideFile(item['resource_id'], item['id'])
            item['file_url'] = endpoint + '/pretranslated/project/{}/resources/{}/file/{}/{}'.format(item['project_id'], item['resource_id'], item['id'], file_name)

        return file_list

    def provideRequesterList(self, project_id, resource_id):
        cursor = self.conn.cursor()
        query = """
	    SELECT *
	    FROM CICERON.V_PRETRANSLATED_REQUESTER
	    WHERE project_id = %s AND resource_id = %s
	"""
        cursor.execute(query, (project_id, resource_id, ))
        column = [col[0] for col in cursor.description]
        ret = cursor.fetchall()
        requester_list = ciceron_lib.dbToDict(column, ret)

        return requester_list

    def provideTranslatorList(self, project_id, resource_id):
        cursor = self.conn.cursor()
        query = """
            SELECT *
            FROM CICERON.V_PRETRANSLATED_TRANSLATOR
            WHERE project_id = %s AND resource_id = %s
	"""
        cursor.execute(query, (project_id, resource_id, ))
        column = [col[0] for col in cursor.description]
        ret = cursor.fetchall()
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

    def pretranslatedProjectList(self, endpoint, page=1):
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
            item['cover_photo_url'] = endpoint + '/user/pretranslated/project/{}/coverPhoto/{}'.format(item['id'], file_name)

        return project_list

    def pretranslatedResourceList(self, project_id, endpoint):
        cursor = self.conn.cursor()
        query = """
            SELECT *
            FROM CICERON.V_PRETRANSLATED_RESOURCES
            WHERE project_id = %s
            ORDER BY id ASC
        """
        cursor.execute(query, (project_id, ))
        columns = [desc[0] for desc in cursor.description]
        ret = cursor.fetchall()

        resource_list = ciceron_lib.dbToDict(columns, ret)
        for item in resource_list:
            file_list_of_resource = self.provideFileListOfResource(item['id'], endpoint)
            item['resorce_info'] = file_list_of_resource
            item['requester_list'] = self.provideRequesterList(project_id, item['id'])
            item['translator_list'] = self.provideTranslatorList(project_id, item['id'])

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
            FROM CICERON.F_PRETRANSLATED_DOWNLOADED_USER
            WHERE resource_id = %s AND email = %s
        """
        cursor.execute(query_checkCount, (resource_id, email, ))
        cnt = cursor.fetchone()[0]
        if cnt > 0:
            # 같은 유저가 같은 번역물 다운로드 권한을
            # 여러번 Call하는 상황을 막아야 한다.
            return 2

        query_addUser = """
            INSERT INTO CICERON.F_PRETRANSLATED_DOWNLOADED_USER
            (id, resource_id, is_user, email, is_paid, is_sent, is_downloaded, request_timestamp)
            VALUES
            (%s, %s, %s, %s, false, false, false, CURRENT_TIMESTAMP)
        """
        user_id = ciceron_lib.get_user_id(self.conn, email)
        is_user = False if user_id == -1 else True
        new_downloader_id = ciceron_lib.get_new_id(self.conn, "F_PRETRANSLATED_DOWNLOADED_USER")

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

    def markAsDownloaded(self, resource_id, email):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_PRETRANSLATED_DOWNLOADED_USER
            SET is_downloaded = true
            WHERE resource_id = %s AND email = %s
        """
        try:
            cursor.execute(query, (resource_id, email, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def markAsPaid(self, resource_id, email):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_PRETRANSLATED_DOWNLOADED_USER
            SET is_paid = true
            WHERE resource_id = %s AND email = %s
        """
        try:
            cursor.execute(query, (resource_id, email, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def rateTranslatedResult(self, resource_id, email, score):
        cursor = self.conn.cursor()

        query = """
            UPDATE CICERON.F_PRETRANSLATED_DOWNLOADED_USER
            SET feedback_score = %s
            WHERE resource_id = %s AND email = %s
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
            self.app.add_url_rule('{}/admin/pretranslated/project'.format(endpoint), view_func=self.pretranslatedCreateProject, methods=["POST"])
            self.app.add_url_rule('{}/admin/pretranslated/project/<int:project_id>/resource'.format(endpoint), view_func=self.pretranslatedCreateResource, methods=["POST"])
            self.app.add_url_rule('{}/admin/pretranslated/project/<int:project_id>/resource/<int:resource_id>/file'.format(endpoint), view_func=self.pretranslatedCreateFile, methods=["POST"])

            self.app.add_url_rule('{}/admin/pretranslated/project/<int:project_id>'.format(endpoint), view_func=self.pretranslatedUpdateProjectInfo, methods=["PUT"])
            self.app.add_url_rule('{}/admin/pretranslated/project/<int:project_id>/resource/<int:resource_id>'.format(endpoint), view_func=self.pretranslatedUpdateResourceInfo, methods=["PUT"])
            self.app.add_url_rule('{}/admin/pretranslated/project/<int:project_id>/resource/<int:resource_id>/file/<int:file_id>'.format(endpoint), view_func=self.pretranslatedUpdateFileInfo, methods=["PUT"])

            self.app.add_url_rule('{}/admin/pretranslated/project/<int:project_id>'.format(endpoint), view_func=self.pretranslatedDeleteProject, methods=["DELETE"])
            self.app.add_url_rule('{}/admin/pretranslated/project/<int:project_id>/resource/<int:resource_id>'.format(endpoint), view_func=self.pretranslatedDeleteResource, methods=["DELETE"])
            self.app.add_url_rule('{}/admin/pretranslated/project/<int:project_id>/resource/<int:resource_id>/file/<int:file_id>'.format(endpoint), view_func=self.pretranslatedDeleteFile, methods=["DELETE"])






            self.app.add_url_rule('{}/user/pretranslated/project'.format(endpoint), view_func=self.pretranslatedList, methods=["GET"])
            self.app.add_url_rule('{}/user/pretranslated/project/<int:project_id>/coverPhoto/<filename>'.format(endpoint), view_func=self.pretranslatedProvideCoverPhoto, methods=["GET"])
            self.app.add_url_rule('{}/user/pretranslated/project/<int:project_id>/resource'.format(endpoint), view_func=self.pretranslatedProvideResource, methods=["GET"])
            self.app.add_url_rule('{}/user/pretranslated/project/<int:project_id>/resource/<int:resource_id>/request'.format(endpoint), view_func=self.addUserForDownload, methods=["POST"])
            self.app.add_url_rule('{}/user/pretranslated/project/<int:project_id>/resource/<int:resource_id>/markAsPaid'.format(endpoint), view_func=self.pretranslatedMarkAsPaid, methods=["GET"])
            self.app.add_url_rule('{}/user/pretranslated/project/<int:project_id>/resource/<int:resource_id>/sendMail'.format(endpoint), view_func=self.pretranslatedSendToMail, methods=["POST"])
            self.app.add_url_rule('{}/user/pretranslated/download/'.format(endpoint), view_func=self.download, methods=["GET"])
            self.app.add_url_rule('{}/user/pretranslated/project/<int:project_id>/resource/<int:resource_id>/rate'.format(endpoint), view_func=self.pretranslatedRateResult, methods=["POST"])
            self.app.add_url_rule('{}/user/pretranslated/mine'.format(endpoint), view_func=self.pretranslatedMyDownloadedList, methods=["GET"])

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
        #parameters.pop('cover_photo')
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
    def pretranslatedCreateResource(self, project_id):
        """
        번역물 리소스 생성 API

        **Parameters**
          #. **"project_id"**: 프로젝트 ID (URL)
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
            if key not in ['target_language_id', 'theme', 'description', 'tone_id', 'read_permission_level', 'price', 'is_original']:
                return make_response("Bad request", 400)
        is_original = parameters['is_original']
        parameters['project_id'] = project_id
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

        g.db.commit()
        return make_response(json.jsonify(
            resource_id=resource_id
          , message="OK"), 200)

    @admin_required
    def pretranslatedCreateFile(self, project_id, resource_id):
        """
        파일 업로드 API

        **Parameters**
          #. **"project_id"**: 프로젝트 ID (URL)
          #. **"resource_id"**: Resource ID (URL)
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
        parameters['project_id'] = project_id
        parameters['resource_id'] = resource_id

        for upload_file in upload_files:
            parameters['file_name'] = upload_file.filename
            parameters['file_binary'] = upload_file.read()
            is_ok, file_id = pretranslatedObj.createFile(**parameters)
            if is_ok == False:
                g.db.rollback()
                return make_response("Fail", 410)

        else:
            g.db.commit()
            return make_response("OK", 200)

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
            return make_response("OK", 200)

        else:
            g.db.rollback()
            return make_response("Fail", 410)

    @admin_required
    def pretranslatedUpdateResourceInfo(self, project_id, resource_id):
        """
        번역물 리소스 수정 API

        **Parameters** (All OPTIONAL)
          #. **"resource_id"**: 프로젝트 ID (URL)
          #. **"target_language_id"**: 번역 타겟 언어 ID (원 언어일수도 있음)
          #. **"theme"**: 제목
          #. **"description"**: 번역물 설명
          #. **"tone_id"**: 번역물 톤 ID
          #. **"read_permission_level"**: 접근 레벨
          #. **"price"**: 가격 in USD

        **Response**
          #. **200**: 업데이트 성공
            .. code-block:: json
               :linenos:

               {
                 "message": "OK" // Request ID
               }

           #. **410**: 업데이트 실패 

        """
        pretranslatedObj = Pretranslated(g.db)
        parameters = ciceron_lib.parse_request(request)
        is_ok = pretranslatedObj.updateResource(resource_id, **parameters)
        if is_ok == True:
            g.db.commit()
            return make_response("OK", 200)

        else:
            g.db.rollback()
            return make_response("Fail", 410)

    @admin_required
    def pretranslatedUpdateFileInfo(self, project_id, resource_id, file_id):
        """
        파일 수정 API

        **Parameters**
          #. **"file_id"**: 파일 ID (URL)
          #. **"preview_permission"**: 미리보기 권한
          #. **"file"**: 파일

        **Response**
          #. **200**: 업데이트 성공
            .. code-block:: json
               :linenos:

               {
                 "message": "OK" // Request ID
               }

           #. **410**: 게시 실패 

        """
        pretranslatedObj = Pretranslated(g.db)
        parameters = ciceron_lib.parse_request(request)
        if "file" in request:
            file_obj = request.files['file']
            parameters['file_name'] = file_obj.filename
            parameters['file_binary'] = file_obj.read()
            parameters.pop('file')

        is_ok = pretranslatedObj.updateFile(file_id, **parameters)
        if is_ok == True:
            g.db.commit()
            return make_response("OK", 200)

        else:
            g.db.rollback()
            return make_response("Fail", 410)

    @admin_required
    def pretranslatedDeleteProject(self, project_id):
        """
        프로젝트 삭제
        **Parameters**
          #. **"project_id"**: 프로젝트 ID (URL)

        **Response**
          #. **200**: OK
          #. **410**: Fail

        """
        pretranslatedObj = Pretranslated(g.db)
        is_ok = pretranslatedObj.deleteProject(project_id)
        if is_ok == True:
            g.db.commit()
            return make_response("OK", 200)

        else:
            g.db.rollback()
            return make_response("Fail", 410)

    @admin_required
    def pretranslatedDeleteResource(self, project_id, resource_id):
        """
        리소스 삭제
        **Parameters**
          #. **"resource_id"**: Resource ID (URL)

        **Response**
          #. **200**: OK
          #. **410**: Fail

        """
        pretranslatedObj = Pretranslated(g.db)
        is_ok = pretranslatedObj.deleteResource(resource_id)
        if is_ok == True:
            g.db.commit()
            return make_response("OK", 200)

        else:
            g.db.rollback()
            return make_response("Fail", 410)

    @admin_required
    def pretranslatedDeleteFile(self, project_id, resource_id, file_id):
        """
        파일 삭제
        **Parameters**
          #. **"file_id"**: File ID (URL)

        **Response**
          #. **200**: OK
          #. **410**: Fail

        """
        pretranslatedObj = Pretranslated(g.db)
        is_ok = pretranslatedObj.deleteResultFile(file_id)
        if is_ok == True:
            g.db.commit()
            return make_response("OK", 200)

        else:
            g.db.rollback()
            return make_response("Fail", 410)

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
                       "id": 2,
                       "original_resource_id": 4,
                       "original_lang_id": 1,
                       "original_lang": "Korean",
                       "target_language_id": 1,
                       "target_language": "Korean",
                       "format_id": 1,
                       "format": null,
                       "subject_id": 1,
                       "subject": null,
                       "author": "이준행",
                       "project_register_timestamp": "Sun, 12 Feb 2017 08:58:34 GMT",
                       "original_theme": "테스트",
                       "description": "테스트의 한 일환입니다",
                       "resource_register_timestamp": "Sun, 12 Feb 2017 09:10:04 GMT",
                       "cover_photo_url": "/api/v2/user/pretranslated/project/2/coverPhoto/preview.png"
                     }
                   ]
                 }
        """
        pretranslatedObj = Pretranslated(g.db)
        page = int(request.args.get('page', 1))
        result = pretranslatedObj.pretranslatedProjectList(self.endpoints[-1], page)
        return make_response(json.jsonify(data=result), 200)

    def pretranslatedProvideCoverPhoto(self, project_id, filename):
        """
        커버사진 다운로드

        **Response**
          #. **200**: 파일 다운로드
          #. **404**: 파일 없음

        """
        pretranslatedObj = Pretranslated(g.db)
        is_ok, _filename, binary = pretranslatedObj.provideCoverPhoto(project_id)
        if is_ok == True:
            return send_file(io.BytesIO(binary), attachment_filename=_filename)
        else:
            return make_response("Fail", 404)

    def pretranslatedProvideResource(self, project_id):
        """
        리소스 정보 보여주기
        **Parameters**
          #. **"project_id"**: 프로젝트 ID (URL)

        **Response**
          #. **200**
            .. code-block:: json
              :linenos:

                {
                  "data": [
                    {
                      "id": 4,
                      "project_id": 2,
                      "target_language_id": 1,
                      "target_language": "Korean",
                      "theme": "테스트",
                      "description": "테스트의 한 일환입니다",
                      "tone_id": 1,
                      "read_permission_level": 1,
                      "price": 0,
                      "register_timestamp": "Sun, 12 Feb 2017 09:10:04 GMT",
                      "resorce_info": [
                        {
                          "id": 1,
                          "project_id": 2,
                          "resource_id": 4,
                          "preview_permission": 1,
                          "file_url": "/api/v2/pretranslated/project/2/resources/4/file/1/swsx.png"
                        }
                      ],
                      "requester_list": [
                        {
                          "requester_id": 2,
                          "resource_id": 4,
                          "project_id": 2,
                          "id": 2,
                          "email": "pjh0308@gmail.com",
                          "name": "박박박",
                          "mother_language_id": 1,
                          "is_translator": false,
                          "other_language_list_id": null,
                          "profile_pic_path": "profile_pic/2/20151127104901114524.png",
                          "numofrequestpending": 0,
                          "numofrequestongoing": 0,
                          "numofrequestcompleted": 0,
                          "numoftranslationpending": 0,
                          "numoftranslationongoing": 0,
                          "numoftranslationcompleted": 0,
                          "badgelist_id": null,
                          "profile_text": "Translation license",
                          "trans_request_state": 1,
                          "nationality": null,
                          "residence": null,
                          "return_rate": 0.7,
                          "member_since": null
                        }
                      ],
                      "translator_list": [
                        {
                          "translator_id": 1,
                          "resource_id": 4,
                          "project_id": 2,
                          "id": 1,
                          "email": "psy2848048@gmail.com",
                          "name": "Bryan",
                          "mother_language_id": 1,
                          "is_translator": true,
                          "other_language_list_id": null,
                          "profile_pic_path": "profile_pic/1/20151126160851584724.jpg",
                          "numofrequestpending": 0,
                          "numofrequestongoing": 0,
                          "numofrequestcompleted": 0,
                          "numoftranslationpending": 0,
                          "numoftranslationongoing": 0,
                          "numoftranslationcompleted": 1,
                          "badgelist_id": null,
                          "profile_text": "Test",
                          "trans_request_state": 2,
                          "nationality": null,
                          "residence": null,
                          "return_rate": 0.7,
                          "member_since": null
                        }
                      ]
                    }
                  ]
                }

        """
        pretranslatedObj = Pretranslated(g.db)
        resource_list = pretranslatedObj.pretranslatedResourceList(project_id, self.endpoints[-1])
        return make_response(json.jsonify(data=resource_list), 200)

    def addUserForDownload(self, project_id, resource_id):
        """
        **Parameters**
          #. **"email"**: 이메일. 프론트에서는 로그인되어 있다면 세션의 'useremail'을 따 와서 자동으로 입력했으면 하는 소망이 있음.
          #. **"project_id"**: 프로젝트 ID. URL에 직접 삽입
          #. **"resource_id"**: 구매한 번역물의 ID. URL에 직접 삽입

        **Response**
          **200**: 성공

          **410**: 똑같은 번역물 중복구매시도
          
          **411**: DB Error

        """
        pretranslatedObj = Pretranslated(g.db)
        parameters = ciceron_lib.parse_request(request)
        email = parameters['email']
        # 다운로드한 유저 목록에 추가
        is_added = pretranslatedObj.addUserAsDownloader(resource_id, email)
        if is_added == 2:
            g.db.rollback()
            return make_response(json.jsonify(message="Multiple request in one request_id"), 410)
        elif is_added == 1:
            g.db.rollback()
            return make_response(json.jsonify(message="DB error"), 411)
        else:
            g.db.commit()
            return make_response("OK", 200)

    @login_required
    def pretranslatedMarkAsPaid(self, project_id, resource_id):
        """
        유저 가격 지불 후 지불처리 하는 함수
        
        **Parameters**
          #. **"resource_id"**: Request ID. URL에 직접 삽입
        
        **Response**
          #. **200**: OK
          #. **405**: Fail

        """
        pretranslatedObj = Pretranslated(g.db)
        email = session['useremail']

        is_marked = pretranslatedObj.markAsPaid(resource_id, email)

        if is_marked == True:
            g.db.commit()
            return redirect('{}/user/pretranslated/project'.format(self.endpoints[-1]), 302)

        else:
            g.db.rollback()
            return make_response(json.jsonify(
                message="Fail"),
                405)

    def pretranslatedSendToMail(self, project_id, resource_id):
        """
        구매한 번역 메일로 링크 전송

        **Parameters**
          #. **"project_id"**: Project ID. (URL)
          #. **"resource_id"**: 구매한 번역물의 ID. (URL)
          #. **"email"**: 이메일. 프론트에서는 로그인되어 있다면 세션의 'useremail'을 따 와서 자동으로 입력했으면 하는 소망이 있음.

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
        is_issued, checksums_and_fileId = pretranslatedObj.calcChecksumForEmailParams(resource_id, email)
        if is_issued == False:
            g.db.rollback()
            return make_response(json.jsonify(
                message="No pretranslated result by given request_id")
                , 412)

        # 지불여부 체크
        is_paid = pretranslatedObj.checkIsPaid(resource_id, email)
        if is_paid > 0:
            return make_response(json.jsonify(message="Need payment"), 411)

        # 링크 제작하고 메일로 전송
        downloadable_links = []
        for item in checksums_and_fileId:
            file_id = item['file_id']
            checksum = item['checksum']
            downloadable_link = pretranslatedObj.generateDownloadableLink(self.endpoints[-1], resource_id, file_id, email, checksum)
            downloadable_links.append(downloadable_link)

        href_part = pretranslatedObj._hrefTagMaker(downloadable_links)

        f = open('templates/pretranslatedDownloadMail.html', 'r')
        mail_content = f.read().format(href_part='\n'.join(href_part))
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
          #. **"resource_id"**: Resource ID
          #. **"file_id"**: File ID
          #. **"token"**: 정당한 의뢰인지 알아보는 Token

        **Response**
          **200**: 다운로드 실행

          **410**: Checksum 에러

          **411**: 다운로드 완료 마킹 실패

        """
        pretranslatedObj = Pretranslated(g.db)
        email = request.args['email']
        resource_id = request.args['resource_id']
        file_id = request.args['file_id']
        checksum_from_param = request.args['token']

        is_ok = pretranslatedObj.checkChecksumFromEmailParams(resource_id, file_id, email, checksum_from_param)
        if is_ok == False:
            g.db.rollback()
            return make_response(json.jsonify(message="Auth error"), 410)

        else:
            is_marked = pretranslatedObj.markAsDownloaded(resource_id, email)
            if is_marked == True:
                g.db.commit()
                can_provide, filename, binary = pretranslatedObj.provideFile(resource_id, file_id)
                return send_file(io.BytesIO(binary), attachment_filename=filename)
            else:
                g.db.rollback()
                return make_response(json.jsonify(message="DB error"), 411)

    @login_required
    def pretranslatedRateResult(self, project_id, resource_id):
        """
        번역물 평점 먹이기

        **Parameters**
          #. **"project_id"**: 프로젝트 ID (URL)
          #. **"resource_id"**: 리소스 ID (URL)
          #. **"score"**: 1-5점까지의 피드백 점수
        
        **Response**
          #. **200**: OK
          #. **405**: Fail

        """
        pretranslatedObj = Pretranslated(g.db)
        email = session['useremail']
        parameters = ciceron_lib.parse_request(request)
        score = parameters['score']

        is_rated = pretranslatedObj.rateTranslatedResult(resource_id, email, score)

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

    @login_required
    def pretranslatedMyDownloadedList(self):
        """
        내가 구매한 다운로드 목록 리스트

        **Parameters**
          #. **"page"**: 페이지 (OPTIONAL)

        **Response**
          #. **200**
            .. code-block:: json
               :linenos:

                 {
                   "data": [
                     {
                       "id": 3,
                       "resource_id": 4,
                       "is_paid": false,
                       "is_sent": false,
                       "is_downloaded": false,
                       "feedback_score": null,
                       "request_timestamp": "Sun, 12 Feb 2017 19:40:45 GMT"
                     }
                   ]
                 }

        """
        pretranslatedObj = Pretranslated(g.db)
        user_id = ciceron_lib.get_user_id(g.db, session['useremail'])
        result = pretranslatedObj.getMyDownloadList(user_id)
        return make_response(json.jsonify(data=result), 200)

