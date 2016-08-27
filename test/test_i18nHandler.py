# -*- coding: utf-8 -*-

import psycopg2
from unittest import TestCase
import sys
sys.path.append('./src')

from i18nHandler import I18nHandler


class I18nHanlderTestCase(TestCase):
    def setUp(self):
        self.conn = psycopg2.connect("host=cicerontest.cng6yzqtxqhh.ap-northeast-1.rds.amazonaws.com port=5432 dbname=ciceron user=ciceron_web password=noSecret01!")
        self.i18nHandlerObj = I18nHandler(self.conn)

    def tearDown(self):
        self.conn.rollback()
        self.conn.close()

    def test_assert(self):
        self.assertEqual(True, True)
        
    def test_jsonResponse(self):
        pass

    def test_androidToDict(self):
        f = open('test/testdata/string.xml')
        xmlText = f.read()
        f.close()

        result = self.i18nHandlerObj._androidToDict(xmlText)
        
    def test_androidToDb(self):
        f = open('test/testdata/string.xml')
        xmlText = f.read()
        f.close()

        self.i18nHandlerObj.androidToDb(360, 1, 2, xmlText)

    def test_jsonToDb(self):
        f = open('test/testdata/i18n.json')
        jsonText = f.read()
        f.close()

        self.i18nHandlerObj.jsonToDb(360, 1, 2, jsonText)
    
    def test_iosToDb(self):
        f = open('test/testdata/Localizable.strings')
        iosText = f.read()
        f.close()

        self.i18nHandlerObj.iosToDb(360, 1, 2, iosText)

    def test_xamarinToDb(self):
        f = open('test/testdata/AppResources.ko.resx')
        xamarinText = f.read()
        f.close()

        self.i18nHandlerObj.xamarinToDb(360, 1, 2, xamarinText)
