# -*- coding: utf-8 -*-
from translator import Translator
from ciceron_lib import get_new_id


class Warehousing:

    def __init__(self, conn):
        self.conn = conn

    def __parse(self, strings):
        return strings.split('\n')

    def __unitOriginalDataInsertByParagragh(self, idx, paragragh):
        cursor = self.conn.cursor()

        query = """INSERT INTO CICERON.D_REQUEST_TEXTS
                       (id, seq, path, text, hit)
                   VALUES
                       (%s, %s, %s, %s, %s) """
