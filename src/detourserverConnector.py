# -*- coding: utf-8 -*-

import requests
import json
import ciceron_lib


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
