# -*- coding: utf-8 -*-

import psycopg2
import os
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
        #  , status_id=0
        #  , format_id
        #  , subject_id
        #  , registered_time=CURRENTD_TIMESTAMP
        #  , points
        #  , theme_text
        #  , description
        #  , checksum=[check_inside]
        #  , tone_id
        #  , file_binary
        #  , preview_binary

        return params

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
