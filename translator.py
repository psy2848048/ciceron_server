# -*- coding: utf-8 -*-

from __future__ import print_function
from googleapiclient.discovery import build
from microsofttranslator import Translator as Bing_Translator


class Translator:
    def __init__(self):
        self.googleAPI = build('translate', 'v2',
                                developerKey='AIzaSyDIyeO9auTHO6qqciEqsmZLexZtQ9kpey0')
        #self.yandexAPI = ...
        self.bingAPI = Bing_Translator('<Your Client ID>', '<Your Client Secret>')

    def _googleTranslate(self, source_lang, target_lang, sentences):
        result_google = self.googleAPI.translations().list(
                                                source=source_lang,
                                                target=target_lang,
                                                     q=sentences
                ).execute()
        result_array = [ item['translatedText'] for item in result_google ]
        return result_google

    def _bingTranslate(self, source_lang, target_lang, sentences):
        result_bing = self.bingAPI.translate(sentences, target_lang)

        result_array = [ item['TranslatedText'] for item in result_bing ]
        return result_array

    def doWork(self, source_lang, target_lang, sentences):
        result_google = self._googleTranslate(source_lang, target_lang, sentences)
        result_bing = self._bingTranslate(source_lang, target_lang, sentences)

        result = []
        for google, bing in zip(result_google, result_bing):
            item = {}
            item['google'] = google
            item['bing'] = bing

            result.append(item)

        return result

if __name__ == '__main__':
    translator = Translator()
    requests = ["""It went like this: it said, "Hello James Veitch, I have an interesting business proposal I want to share with you, Solomon." Now, my hand was kind of hovering on the delete button, right? I was looking at my phone. I thought, I could just delete this. Or I could do what I think we've all always wanted to do."""]
    result = translator.doWork('en', 'ko', requests)
    print result
