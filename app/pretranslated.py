# -*- coding: utf-8 -*-

import psycopg2
import io
import traceback
try:
    from .ciceron_lib import *
except:
    from ciceron_lib import *

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
        #  , filename
        #  , theme_text
        #  , description
        #  , checksum=[check_inside]
        #  , tone_id
        #  , file_binary
        #  , preview_binary

        params = kwargs
        params['id'] = ciceron_lib.get_new_id(self.conn, "F_PRETRANSLATED")
        params['registered_time'] = 'CURRENT_TIMESTAMP'
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

    def uploadPretranslatedResult(self, **kwargs):
        cursor = self.conn.cursor()
        query_tmpl = """
            INSERT INTO CICERON.F_PRETRANSLATED
            ({columns})
            VALUES
            ({prepared_statements})
        """
        params = self,_organizeParameters(**kwargs)
        columns = ','.join( list( params.keys() ) )
        prepared_statements = ','.join( ['%s' for _ in columns] )
        query = query_tmpl.format(
                    columns=columns
                  , prepared_statements=prepared_statements
                  )

        try:
            cursor.execute(query, list( kwargs.values() ))
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
        if ret is None of len(ret) == 0:
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
        if ret is None of len(ret) == 0:
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
            self.conn.cursor()
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
            self.conn.cursor()
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

