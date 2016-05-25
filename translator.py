# -*- coding: utf-8 -*-

from __future__ import print_function
from googleapiclient.discovery import build
from microsofttranslator import Translator as Bing_Translator
from yandex_translate import YandexTranslate
import psycopg2
import os
import traceback


class Translator:
    def __init__(self, developerKey='AIzaSyD-S4_2g1SRp4jucHpdLSBBq6xWhOsHcSI'):
        self.googleAPI = build('translate', 'v2',
                                developerKey=developerKey)
        self.yandexAPI = YandexTranslate('trnsl.1.1.20160423T052231Z.a28f67a8074f04f8.0a0282fad14a1dfd13d21ed6ab55f0a0a61c2d3f')
        self.bingAPI = Bing_Translator('welcome_ciceron', 'VL9isREJUILWMCLE2hr75xVaePRof6kuGkCM+r9oTb0=')

    def _googleTranslate(self, source_lang, target_lang, sentences):
        if (source_lang == 'ko' and target_lang == 'en') or \
           (source_lang == 'en' and target_lang == 'ko'):
            result_google_jp = self.googleAPI.translations().list(
                                                    source=source_lang,
                                                    target='jp',
                                                         q=sentences
                    ).execute()
            if result_google_jp.get('translations') != None:
                inter_text = result_google_jp['translations'][0]['translatedText']
            else:
                return False

            result_google = self.googleAPI.translations().list(
                                                    source='jp',
                                                    target=target_lang,
                                                         q=sentences
                    ).execute()
            if result_google.get('translations') != None:
                result_text = result_google['translations'][0]['translatedText']
                return result_text
            else:
                return False

        else:
            result_google = self.googleAPI.translations().list(
                                                    source=source_lang,
                                                    target=target_lang,
                                                         q=sentences
                    ).execute()
            if result_google.get('translations') != None:
                result_text = result_google['translations'][0]['translatedText']
                return result_text
            else:
                return None

    def _bingTranslate(self, source_lang, target_lang, sentences):
        try:
            result_bing = self.bingAPI.translate(sentences, target_lang)
            return result_bing
        except Exception:
            traceback.print_exc()
            return None

    def _yandexTranslate(self, source_lang, target_lang, sentences):
        lang_FromTo = '%s-%s' % (source_lang, target_lang)
        result_yandex = self.yandexAPI.translate(sentences, lang_FromTo)
        if result_yandex.get('text') != None:
            return result_yandex['text'][0]
        else:
            return None

    def getCountryCode(self, country_id):
        if os.environ.get('PURPOSE') == 'PROD':
            DATABASE = "host=ciceronprod.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"
        else:
            DATABASE = "host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!"

        conn = psycopg2.connect(DATABASE)
        cursor = conn.cursor()

        query = """SELECT google_code, yandex_code, bing_code FROM CICERON.D_LANGUAGES
                      WHERE id = %s """
        cursor.execute(query, (country_id, ))
        res = cursor.fetchone()
        if res is None or len(res) == 0:
            return False, None

        return True, {'google': res[0], 'yandex': res[1], 'bing': res[2]}

    def doWork(self, source_lang_id, target_lang_id, sentences):
        if len(sentences.decode('utf-8') ) > 1000:
            result_text = u"한 문장에 1000글자가 넘어가면 초벌 번역이 불가능합니다. / It is imposiible to initial-translate if the length of the sentence is over 1000 characters."
            return True, {'google': result_text, 'bing': result_text, 'yandex': result_text}

        is_sourceId_OK, source_langCodeDict = self.getCountryCode(source_lang_id)
        is_targetId_OK, target_langCodeDict = self.getCountryCode(target_lang_id)

        if is_sourceId_OK == False or is_targetId_OK == False:
            return False, None

        result_google = self._googleTranslate(source_langCodeDict['google'], target_langCodeDict['google'], sentences)
        result_bing = self._bingTranslate(source_langCodeDict['bing'], target_langCodeDict['bing'], sentences)
        result_yandex = self._yandexTranslate(source_langCodeDict['yandex'], target_langCodeDict['yandex'], sentences)

        return True, {'google': result_google, 'bing': result_bing, 'yandex': result_yandex}

if __name__ == '__main__':
    translator = Translator()
    requests = u"""논문의 평균 분량은 분야마다 다 다르다. 수학 같은 경우는 정말 A4용지 반 장 분량(…)의 논문이라고 하더라도 그 내용이 어떠한가에 따라서 세계를 발칵 뒤집는 불후의 논문이 될 수도 있다.[2] 사회과학은 그보다는 좀 더 길어진다. 대개의 심리학 논문은 20~30장 선에서 어지간하면 글이 끝나고, 정치학은 비슷하거나 그보다는 좀 더 긴 편이다. 논문의 방대함으로는 (연구주제에 따라서는) 행정학이 유명한데, 이 분야는 나랏님 하시는 일을 다루는지라 일단 데이터 양부터가 장난이 아니다. 오죽하면 행정학자들끼리 "우리는 학회를 한번 갔다오면 왜 연구실에 전화번호부 두께의 학회지가 너댓 편씩 쌓이지?"(…) 같은 농담을 주고받을 정도이니...[3] 그 외에도 논문 분량이 당연히 백여 페이지를 한참 넘을 것으로 기대되는 분야들은 꽤 있다. 단, 학술지 논문에 비해 우리 위키러들이 정말로 궁금할 학위논문의 경우 분량이 그 5~10배 가량 육박하는 경우가 많으니 참고. 일부 박사논문은 납본되는 걸 보면 정말로 책 한 권이 나온다.(...)  좀 심하게 말하면, 어떤 학술적인 글을 쓰는데 분량을 신경쓰는 것은 레포트 쓰는 학부생들의 수준에서 바라보는 시각일 수 있다. (굳이 좋게 평하자면, 최소한의 논문다운 논문을 쓰기 위한 휴리스틱이다.) 학계에서 논문의 가치는 그 논문의 양이 얼마나 방대한지는 전혀 상관없다. 일부 사회과학 분야 논문들은 가설을 한번에 30개 이상씩(!) 검증하기도 하나, 그런 논문이 가설 하나 검증하는 논문, 아니 아무도 신경쓰지 않은 문제를 최초로 제기하느라 가설은 아예 검증하지도 못하고 제안하기만 한 논문보다 우월하다고 취급되지는 않는다. 가설을 많이 검증한다고 해도 그 검증과정이나 논리적 차원에서 결함이나 비약이 있다면 가차없이 탈탈 털릴 뿐이다. 원론적으로, 인문학이나 예술분야라고 해도 자신의 독창적 생각을 타인에게 설득력 있게 전달하는 과정이 중요하게 취급되는 것은 당연하다.  공연히 분량을 늘린답시고 논문에서 논거를 질질 끌거나 쓸데없는 데이터를 넣거나 하면 당연히 또 탈탈 털린다. 애초에 학계라는 곳은 타인의 언급을 인용하는 것조차도 논리적 전개에 불필요해 보인다 싶으면 가차없이 불벼락을 내리는 바닥이다.[4] 필요한 말을 안 써서 까이기도 하지만, 쓸데없는 말이 너무 많다고 까이기도 하니, 논문을 준비하는 연구자는 이래저래 피곤하다. 게다가 교수들도 긴 글 읽기는 싫어하는 경우가 많다.(…)[5] """
    is_ok, result = translator.doWork(1, 2, requests)
    print (result)
