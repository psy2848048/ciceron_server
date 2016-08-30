# -*- coding: utf-8 -*-

import requests
import json
import ciceron_lib
from multiprocessing import Process
from copy import deepcopy


class Connector:
    def __init__(self):
        self.tempTranslatedData = {}

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

    def getTranslatedDataParallel(self, conn, user_id, request_id, sentences, source_lang_id, target_lang_id):
        is_real_translator = ciceron_lib.strict_translator_checker(conn, user_id, request_id)

        def parallelJob(arr, idx, unit_sentence, lang_id1, lang_id2):
            payload = {
                     'user_email':'admin@sexycookie.com'
                   , 'sentence': unit_sentence
                   , 'source_lang_id': lang_id1
                   , 'target_lang_id': lang_id2
                   , 'where': 'somewhere'
                   }
            response = requests.post('http://52.196.164.64/translate', data=payload)
            self.tempTranslatedData[ "%d" % idx ] = deepcopy(json.loads(response.text))

        job_storage = []
        for idx, sentence in enumerate(sentences):
            job_storage.append( Process(target=parallelJob, args=(sharedArray, idx, sentence, source_lang_id, target_lang_id, )) )

        for proc in job_storage:
            proc.start()

        for proc in job_storage:
            proc.join()

        print self.tempTranslatedData

        result = {
                'google': []
              , 'bing': []
              , 'yandex': []
                }
        for idx in xrange(len(self.tempTranslatedData)):
            result['google'].append(self.tempTranslatedData["%d" % idx]['google'])
            result['bing'].append(self.tempTranslatedData["%d" % idx]['bing'])
            result['yandex'].append(self.tempTranslatedData["%d" % idx]['yandex'])

        return result
