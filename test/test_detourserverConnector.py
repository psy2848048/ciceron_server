#-*- coding: utf-8 -*-

import psycopg2
from unittest import TestCase
import sys
sys.path.append('./src')

from detourserverConnector import Connector
import ciceron_lib

class ConnectorTestCase(TestCase):
    def setUp(self):
        self.connector = Connector()
        self.conn = psycopg2.connect("host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!")

    def test_getTranslatedData(self):
        result = self.connector.getTranslatedData(
                "나는 이제서야 조금 살 만 해서 좋다."
              , 1
              , 2
                )
        self.assertEqual('google' in result, True)
        self.assertEqual('bing' in result, True)
        self.assertEqual('yandex' in result, True)

    def test_getTranslatedDataInternal(self):
        ciceron_lib.strict_translator_checker = lambda x, y, z: True
        result = self.connector.getTranslatedDataInternal(
                self.conn
              , 1
              , 360
              , "나는 이제서야 조금 살 만 해서 좋다."
              , 1
              , 2
                )
        self.assertEqual('google' in result, True)
        self.assertEqual('bing' in result, True)
        self.assertEqual('yandex' in result, True)

    def test_getTranslatedDataParallel(self):
        ciceron_lib.strict_translator_checker = lambda x, y, z: True
        result = self.connector.getTranslatedDataParallel(
                self.conn
              , 1
              , 360
              , [  "나는 이제서야 조금 살 만 해서 좋다."
                 , "완성되어 가는 모습을 보니 마음이 안정되어 간다."
                 , "기쁜 마음으로 다음 스텝으로 나아간다."
                 , "우리는 테크크런치에서 대박이 난다."
                ]
              , 1
              , 2
                )

        print result['google']
        print result['bing']
        print result['yandex']

        self.assertEqual('google' in result and len(result['google']) == 4, True)
        self.assertEqual('bing' in result and len(result['bing']) == 4, True)
        self.assertEqual('yandex' in result and len(result['yandex']) == 4, True)

