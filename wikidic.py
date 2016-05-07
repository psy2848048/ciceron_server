"""
Class for internal wiki dictionary
"""

import traceback
import psycopg2
import ciceron_lib as lib


class WikiDic(object):
    def __init__(self, conn=None, dbinfo=None):
        self.conn = None

        if conn is not None:
            self.conn = conn
        elif dbinfo is not None:
            self.conn = psycopg2.connect(dbinfo)

    def _addUnitUDFDic(self, request_id, meaning_id, language_id, category, word, added_user_id):
        cursor = self.conn.cursor()

        udfDic_id = lib.get_new_id(self.conn, "USER_DEFINED_DICTIONARY")

        query_insert = """
            INSERT INTO CICERON.USER_DEFINED_DICTIONARY
                (id, request_id, meaning_id, language_id, category, word, added_user_id, added_ts)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """
        try:
            cursor.execute(query_insert, (udfDic_id, request_id, meaning_id, language_id, category, word, added_user_id, ))

        except Exception:
            print traceback.print_exc()
            self.conn.rollback()
            return False

        return True

    def _getNewMeaningIdFromUDFDic(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT nextval('CICERON.SEQ_USER_DEFINED_DICTIONARY_MEANING') ")
        return int(cursor.fetchone()[0])

    def _getLangIdFromRequestId(self, request_id):
        cursor = self.conn.cursor()
        query_getLang = """
            SELECT original_lang_id, target_lang_id FROM CICERON.F_REQUESTS
            WHERE id = %s
        """
        cursor.execute(query_getLang, (request_id, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) == 0:
            return False, None, None

        return True, ret[0], ret[1]

    def _listMaker(self, source_lang_id, target_lang_id, ret):
        lang_list = []
        words_list = []
        cur_meaning_id = None
        temp_item = {}

        for meaning_id, laguage_id, word, category in ret:
            if cur_meaning_id != meaning_id:
                cur_meaning_id = meaning_id
                words_list.append(temp_item)
                temp_item = {}

            if laguage_id == source_lang_id:
                temp_item["source_word"] = word
            elif laguage_id == target_lang_id:
                temp_item['target_word'] = word

            temp_item['category'] = category

        else:
            words_list.append(temp_item)

        return {"lang_list": lang_list, "words_list": words_list}

    def addWordToUDFDic(self, request_id, category, source_lang_word, target_lang_word, added_user_id):
        is_success, source_lang_id, target_lang_id = self._getLangIdFromRequestId(request_id)
        if is_success is False:
            return False

        new_meaning_id = self._getNewMeaningIdFromUDFDic()
        is_success_source = self._addUnitUDFDic(request_id, new_meaning_id, source_lang_id, category, source_lang_word, added_user_id)
        is_success_target = self._addUnitUDFDic(request_id, new_meaning_id, target_lang_id, category, target_lang_word, added_user_id)
        if is_success_source is True and is_success_target is True:
            self.conn.commit()
        else:
            self.conn.rollback()

    def getUDFListForRequest(self, request_id):
        cursor = self.conn.cursor()
        is_success, source_lang_id, target_lang_id = self._getLangIdFromRequestId(request_id)
        query_getWordListByRequest = """
            SELECT meaning_id, language_id, word, category
            FROM CICERON.USER_DEFINED_DICTIONARY
            WHERE request_id = %s
            ORDER BY meaning_id, language_id, word
        """
        cursor.execute(query_getWordListByRequest, (request_id, ))
        ret = cursor.fetchall()
        result = self._listMaker(source_lang_id, target_lang_id, ret)
        return result

    def getUDFListForRequestByWord(self, request_id, word):
        cursor = self.conn.cursor()
        is_success, source_lang_id, target_lang_id = self._getLangIdFromRequestId(request_id)
        query_getMeaningIdByWord = """
            SELECT meaning_id
            FROM CICERON.USER_DEFINED_DICTIONARY
            WHERE request_id = %s AND word = %s
            ORDER BY meaning_id, language_id, word
        """
        cursor.execute(query_getMeaningIdByWord, (request_id, word, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            # Return empty list
            return self._listMaker(source_lang_id, target_lang_id, res)
        meaning_id = res[0]

        query_getWordListByRequest = """
            SELECT meaning_id, language_id, word, category
            FROM CICERON.USER_DEFINED_DICTIONARY
            WHERE request_id = %s AND meaning_id = %s
            ORDER BY meaning_id, language_id, word
        """

        cursor.execute(query_getWordListByRequest, (request_id, meaning_id, ))
        ret = cursor.fetchall()
        result = self._listMaker(source_lang_id, target_lang_id, ret)
        return result

    def getUDFListForRequestiByCategory(self, request_id, category):
        cursor = self.conn.cursor()
        is_success, source_lang_id, target_lang_id = self._getLangIdFromRequestId(request_id)
        query_getWordListByRequest = """
            SELECT meaning_id, language_id, word, category
            FROM CICERON.USER_DEFINED_DICTIONARY
            WHERE request_id = %s AND category = %s
            ORDER BY meaning_id, language_id, word, category
        """
        cursor.execute(query_getWordListByRequest, (request_id, category, ))
        ret = cursor.fetchall()
        result = self._listMaker(source_lang_id, target_lang_id, ret)
        return result

    def getUDFListForRequestiByWordAndCategory(self, request_id, category, word):
        cursor = self.conn.cursor()
        is_success, source_lang_id, target_lang_id = self._getLangIdFromRequestId(request_id)
        query_getMeaningIdByWord = """
            SELECT meaning_id
            FROM CICERON.USER_DEFINED_DICTIONARY
            WHERE request_id = %s AND category = %s AND word = %s
            ORDER BY meaning_id, language_id, word
        """
        cursor.execute(query_getMeaningIdByWord, (request_id, category, word, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            # Return empty list
            return self._listMaker(source_lang_id, target_lang_id, res)
        meaning_id = res[0]

        query_getWordListByRequest = """
            SELECT meaning_id, language_id, word, category
            FROM CICERON.USER_DEFINED_DICTIONARY
            WHERE request_id = %s AND meaning_id = %s AND category = %s
            ORDER BY meaning_id, language_id, word
        """

        cursor.execute(query_getWordListByRequest, (request_id, meaning_id, category, ))
        ret = cursor.fetchall()
        result = self._listMaker(source_lang_id, target_lang_id, ret)
        return result
