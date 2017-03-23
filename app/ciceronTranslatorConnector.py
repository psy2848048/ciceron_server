# -*- coding: utf-8 -*-
from flask import Flask, session, request, g, json, make_response, render_template
import requests
import json as jsonNav
import nltk


try:
    import ciceron_lib
except:
    from . import ciceron_lib

class CiceronTranslator(object):
    def __init__(self):
        self.ciceronAPI = "http://221.142.31.56:{port}/translator/translate"
        self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    def _ciceronTranslate(self, source_lang, target_lang, sentences):
        headers = {'content-type': 'application/json'}
        payload = {'src': sentences}
        if source_lang == '2' and target_lang == '1':
            response = requests.post(self.ciceronAPI.format(port=7700), data=jsonNav.dumps(payload), headers=headers)
        elif source_lang == '1' and target_lang == '2':
            response = requests.post(self.ciceronAPI.format(port=7710), data=jsonNav.dumps(payload), headers=headers)
        else:
            return None

        data = response.json()
        return data[0][0]['tgt']

    def ciceronTranslate(self, source_lang, target_lang, sentences):
        splitted_sentences = self.tokenizer.tokenize(sentences)
        result = []
        for sentence in splitted_sentences:
            unit_result = self._ciceronTranslate(source_lang, target_lang, sentence)
            result.append(unit_result)

        return ' '.join(result)

class CiceronTranslatorAPI(object):
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}/user/translator'.format(endpoint), view_func=self.translator, methods=["POST"])

    def translator(self):
        """
        CICERON 내부 번역기 API

        **Parameters**
          #. **"source_lang_id"**: Int, 원문의 언어 ID
          #. **"target_lang_id"**: Int, 번역문의 언어 ID
          #. **"sentence"**: String, 원어

        **Response**
          #. 200

            .. code-block:: json
               :linenos:

               {
                 "result": "Blahblah" // Request ID
               }

        """
        #client_ip = request.environ.get('REMOTE_ADDR')
        #if client_ip not in ['52.196.144.144', '121.128.220.114']:
        #    return make_response(json.jsonify(
        #        message='Unauthorized'), 401)

        translateObj = CiceronTranslator()
        parameters = ciceron_lib.parse_request(request)
        source_lang = parameters['source_lang_id']
        target_lang = parameters['target_lang_id']
        sentence = parameters['sentence']

        result = translateObj.ciceronTranslate(source_lang, target_lang, sentence)
        return make_response(json.jsonify(result=result), 200)

