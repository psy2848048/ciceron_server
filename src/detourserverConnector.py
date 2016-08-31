# -*- coding: utf-8 -*-

import requests
import json
import ciceron_lib
from multiprocessing import Process
from copy import deepcopy
import psycopg2


class Connector:
    def getTranslatedData(self, sentence, source_lang_id, target_lang_id):
        payload = {
                 'user_email':'admin@sexycookie.com'
               , 'sentence': sentence
               , 'source_lang_id': source_lang_id
               , 'target_lang_id': target_lang_id
               , 'where': 'somewhere'
               }
        response = requests.post('http://52.196.164.64/translate', data=payload)
        result = json.loads(response.text)

        # {'google': --text--, 'bing': --text--, 'yandex': --text}
        return result

    def getTranslatedDataInternal(self, conn, user_id, request_id, sentence, source_lang_id, target_lang_id):
        is_real_translator = ciceron_lib.strict_translator_checker(conn, user_id, request_id)
        payload = {
                 'user_email':'admin@sexycookie.com'
               , 'sentence': sentence
               , 'source_lang_id': source_lang_id
               , 'target_lang_id': target_lang_id
               , 'where': 'somewhere'
               }
        response = requests.post('http://52.196.164.64/translate', data=payload)
        result = json.loads(response.text)

        # {'google': --text--, 'bing': --text--, 'yandex': --text}
        return result

    def getTranslatedDataParallel(self, conn, user_id, request_id, raw_sentences, source_lang_id, target_lang_id):
        sentences = eval(raw_sentences)
        is_real_translator = ciceron_lib.strict_translator_checker(conn, user_id, request_id)
        translation_number = ciceron_lib.get_new_id(conn, 'INIT_TRANSLATION_TEMP')

        def parallelJob(conn, trans_num, idx, unit_sentence, lang_id1, lang_id2):
            conn_inside = psycopg2.connect("host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!")
            cursor_inside = conn_inside.cursor()

            payload = {
                     'user_email':'admin@sexycookie.com'
                   , 'sentence': unit_sentence
                   , 'source_lang_id': lang_id1
                   , 'target_lang_id': lang_id2
                   , 'where': 'somewhere'
                   }
            response = requests.post('http://52.196.164.64/translate', data=payload)
            parsed_response = json.loads(response.text)

            query_insert = """
                INSERT INTO CICERON.INIT_TRANSLATION_TEMP
                    (id, sequence, org, sentence)
                VALUES
                    (%s, %s, %s, %s)
            """
            cursor_inside.execute(query_insert, (trans_num, idx, 'google', parsed_response.get('google'), ))
            cursor_inside.execute(query_insert, (trans_num, idx, 'bing', parsed_response.get('bing'), ))
            cursor_inside.execute(query_insert, (trans_num, idx, 'yandex', parsed_response.get('yandex'), ))
            conn_inside.commit()

        job_storage = []
        for idx, sentence in enumerate(sentences):
            job_storage.append( Process(target=parallelJob, args=(conn, translation_number, idx, sentence, source_lang_id, target_lang_id, )) )

        for proc in job_storage:
            proc.start()

        for proc in job_storage:
            proc.join()

        cursor = conn.cursor()
        result = {
                'google': []
              , 'bing': []
              , 'yandex': []
                }
        for org in ['google', 'bing', 'yandex']:
            query_select = """
                SELECT sequence, sentence FROM CICERON.INIT_TRANSLATION_TEMP
                WHERE id = %s AND org = %s
                ORDER BY sequence
            """
            cursor.execute(query_select, (translation_number, org, ))
            ret = cursor.fetchall()
            for seq, sent in ret:
                result[org].append(sent)

        query_delete = """
            DELETE FROM CICERON.INIT_TRANSLATION_TEMP
            WHERE id = %s
        """
        cursor.execute(query_delete, (translation_number, ))
        conn.commit()

        return result

