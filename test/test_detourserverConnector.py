=#-*- coding: utf-8 -*-

from unittest import TestCase
import sys
sys.path.append('./src')

from detourserverConnector import Connector

class ConnectorTestCase(TestCase):
    def setUp(self):
        self.connector = Connector()

    def test_getTranslatedData(self):
        result = self.connector(
                "나는 이제서야 조금 살 만 해서 좋다."
              , 1
              , 2
                )
        self.assertEqual('google' in result, True)
        self.assertEqual('bing' in result, True)
        self.assertEqual('yandex' in result, True)
