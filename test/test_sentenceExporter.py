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
        pass
    #    res = self.app.post('/api/v2/admin/dataManager/parseSentence',
    #            data = {
    #                'orifinal_string': [
    #                    {
    #                        'paragraph_id': 1,
    #                        'sentences': [
    #                            {
    #                                'sentence_id': 1,
    #                                'sentence': '가나다라마바사'
    #                            },
    #                            {
    #                                'sentence_id': 2,
    #                                'sentence': '파싱되고 있습니까?'
    #                            }
    #                        ]
    #                    },
    #                    {
    #                        'paragraph_id': 2,
    #                        'sentences': [
    #                            {
    #                                'sentence_id': 1,
    #                                'sentence': '안녕하세요'
    #                            }
    #                        ]
    #                    }
    #                ],
    #                'translated_string': [
    #                    {
    #                        'paragraph_id': 1,
    #                        'sentences': [
    #                            {
    #                                'sentence_id': 1,
    #                                'sentence': 'GANADARAMABASA'
    #                            },
    #                            {
    #                                'sentence_id': 2,
    #                                'sentence': 'Are you parsing?'
    #                            }
    #                        ]
    #                    },
    #                    {
    #                        'paragraph_id': 2,
    #                        'sentences': [
    #                            {
    #                                'sentence_id': 1,
    #                                'sentence': 'Hello'
    #                            }
    #                        ]
    #                    }
    #                ]
    #            })
    #    self.assertEqual(res.code, 200)

    def test_dataImport_OK(self):
        res = self.app.post('/api/v2/admin/dataManager/import',
                data = json.dumps(dict(
                    original_language_id = 1,
                    target_language_id = 2,
                    subject_id = 3,
                    format_id = 3,
                    tone_id = 2,
                    data = [
                        {
                            "paragraph_id": 1,
                            "sentences": [
                                {
                                    "sentence_id" : 1,
                                    "original_sentence" : "테스트중입니다.",
                                    "translated_sentence" : "Testing."
                                },
                                {
                                    "sentence_id" : 2,
                                    "original_sentence" : "파싱이 잘 됩니다!~",
                                    "translated_sentence" : "Wow, fuck yeh!"
                                }
                            ]
                        },
                        {
                            "paragraph_id" : 2,
                            "sentences" : [
                                {
                                    "sentence_id" : 1,
                                    "original_sentence" : "그냥 그렇다",
                                    "translated_sentence" : "So so"
                                }
                            ]
                        }
                    ])),
                content_type = 'application/json')
        self.assertEqual(res.status_code, 200)
    
    def test_dataImport_Fail1(self):
        res = self.app.post('/api/v2/admin/dataManager/import',
                data = json.dumps(dict(
                    original_language_id = 1,
                    target_language_id = 2,
                    subject_id = 3,
                    format_id = 3,
                    tone_id = 2,
                    data = [
                        {
                            "paragraph_id": 1,
                            "sentences": [
                                {
                                    "sentence_id" : 1,
                                    "original_sentence" : "테스트중입니다.",
                                    "translated_sentence" : "Testing."
                                },
                                {
                                    "sentence_id" : 2,
                                    "original_sentence" : "파싱이 잘 됩니다!~",
                                    "translated_sentence" : "Wow, fuck yeh!"
                                }
                            ]
                        },
                        {
                            "paragraph_id" : 2,
                            "sentences" : [
                                {
                                    "sentence_id" : 1,
                                    "original_sentence" : "그냥 그렇다",
                                    "translated_sentence" : "So so"
                                }
                            ]
                        }
                    ])),
                content_type = 'application/json')
        self.assertEqual(res.status_code, 200)
                              
    def test_dataExport(self):
        pass                  
    #    res = self.app.post('/api/v2/admin/dataManager/export',
    #            data = {} )  
                              
                              
    def test_dataCounter(self):
        pass
    #    res = self.app.get('/api/v2/admin/dataManager/dataCounter')
