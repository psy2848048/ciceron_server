# -*- coding: utf-8 -*-

from unittest import TestCase
import sys
sys.path.append('../app')
import psycopg2
import json

import application
from sentenceExporter import SentenceExporter


class SentenceExporterTestCase(TestCase):
    def _sessionMarkedAsLoggedIn(self):
        with self.app.session_transaction() as sess:
            sess['is_loggedIn'] = True
            sess['user_id'] = 1
            sess['user_name'] = u'브라이언'

    def setUp(self):
        application.app.config['TESTING'] = True
        self.app = application.app.test_client()

    def tearDown(self):
        pass


    # ret = json.loads(res.data)
    # 또는 ret = json.loads(res.code)
    # self.assertEqual(ret['is_loggedIn'], True)

    def test_parseSentence(self):
        res = self.app.post('/api/v2/admin/dataManager/parseSentence',
                data = {
                    'orifinal_string': [
                        {
                            'paragraph_id': 1,
                            'sentences': [
                                {
                                    'sentence_id': 1,
                                    'sentence': '가나다라마바사'
                                },
                                {
                                    'sentence_id': 2,
                                    'sentence': '파싱되고 있습니까?'
                                }
                            ]
                        },
                        {
                            'paragraph_id': 2,
                            'sentences': [
                                {
                                    'sentence_id': 1,
                                    'sentence': '안녕하세요'
                                }
                            ]
                        }
                    ],
                    'translated_string': [
                        {
                            'paragraph_id': 1,
                            'sentences': [
                                {
                                    'sentence_id': 1,
                                    'sentence': 'GANADARAMABASA'
                                },
                                {
                                    'sentence_id': 2,
                                    'sentence': 'Are you parsing?'
                                }
                            ]
                        },
                        {
                            'paragraph_id': 2,
                            'sentences': [
                                {
                                    'sentence_id': 1,
                                    'sentence': 'Hello'
                                }
                            ]
                        }
                    ]
                })
        self.assertEqual(res.code, 200)

    def test_dataImport(self):
        pass

    def test_dataCounter(self):
        pass

    def test_dataExport(self):
        pass

