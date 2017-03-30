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
    '''
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
    '''

    def test_dataImport_OK(self):
        """
        성공 1. 모든 값이 제대로 들어갔을 때 
        """
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
        """
        실패 1. original_sentece가 없는 경우
        """
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
        self.assertEqual(res.status_code, 210)
    
    def test_dataImport_Fail2(self):
        """
        실패 2. translated_sentence가 없는 경우
        """
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
                                    "original_sentence" : "파싱이 잘 됩니다!~",
                                    "translated_sentence" : "Testing."
                                },
                                {
                                    "sentence_id" : 2,
                                    "original_sentence" : "파싱이 잘 됩니다!~",
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
        self.assertEqual(res.status_code, 210)

    '''
    def test_dataImport_Fail3(self):
        """
        실패 3. parameter 중 다 입력되지 않았을 때 
       필수 요소 없으면 에러 처리 안되있음 - 처리 필요
        """
        res = self.app.post('/api/v2/admin/dataManager/import',
                data = json.dumps(dict(
                    original_language_id = 1,
                    target_language_id = 2,
                    subject_id = 3,
                    format_id = 3,
                    tone_id = 2
                    )),
                content_type = 'application/json')
        self.assertEqual(res.resp_code, 410)
    '''

    def test_dataImport_Fail4(self):
        """
        실패 4. 입력된 값의 DataType이 맞지 않을 때
        """
        res = self.app.post('/api/v2/admin/dataManager/import',
                data = json.dumps(dict(
                    original_language_id = 'a',
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
                                    "original_sentence" : "파싱이 잘 됩니다!~",
                                    "translated_sentence" : "Testing."
                                },
                                {
                                    "sentence_id" : 2,
                                    "original_sentence" : "파싱이 잘 됩니다!~",
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
        self.assertEqual(res.status_code, 410)
                              
    def test_dataImport_Fail5(self):
        """
        실패 5. 데이터 길이가 초과됐을 때 
        """
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
                                    "original_sentence" : "파싱이 잘 됩니다!~",
                                    "translated_sentence" : "Testing.가나다라마바상ㄹ;ㅁ냐ㅐㅇ풍ㄴㄴㅁ유ㅏㄴㅁ오ㅠ참ㄴ옻판오마혀됸로ㅓㅠㅊ나 마너ㅠㅊ마ㅕ너ㅠ와ㅗㅓㄴㅇ퐌,ㅠㅓ츄ㅗㅁ넠유ㅗㅊㅁㄴㅇㄹ미냥카ㅓㅊㅍㅁ ㅠㅓ퓸ㄴㅇㅊ니먀ㅕ아ㅓㅊㅁ픂미쟈다넝츄미ㅑㄴ아ㅓㅁ니려마ㅓㄴㅍ ㅟㅁ여ㅏ퓸냐ㅕㅇ파ㅠㅁㅇㅍ미냐ㅕㄹ유ㅓㅍ 미아퍼ㅠㅣ냐여ㅏㅊㅁㄴ아ㅓㅠㅍ미유ㅏㅓㄴ아ㅓㅠ미ㅑ녀롣ㅈㅁ러나ㅓㅠㅁㄴ퓸니ㅑㅕ핀먀ㅕ율ㄴ마ㅓ유핌퓨ㅣ먀ㅕㅍ ㅚㅑㄴ피뉴피먀ㅕ뉴잎먀ㅕㅠaaaaaaaaaaaaaasdfjasdlfijalsdkfaljvnalksdjalsdhbasjdbfasdkjansldkjvnaldfkjvnsdkjansdlkjansdlfjknflaskjdnflasdkjvnalkdjvnalsdkjvnalsdkjnflakjdsnflkajfdnlakdsjnflakjsdnflkajsdnfkjasdnlkfjnasldkjfndsajnflaksjdnflkajsdnlfkjsavnlkjdsnlvkjansldkfnalweiuf;svnjkbnalbskdfjsdkfnavkjndlkvjnasldfanslvkjfblhbsdlasjdbhakjbdlehslwefbsjdvldjnvldkjsnfalfbfbdslbflsadjlvbhsdskdlfjnalsdkjfblsdhbsdbdkjfnalksjdbfkljsdbfklsjabfdklsabfklsablksdjfnalksdjflkajsdfbsalkjdfbaklsjdbfkljtranslated_sentencTesting.aaaaaaaaaaaaaasdfjasdlfijalsdkfaljvnalksdjalsdhbasjdbfasdkjansldkjvnaldfkjvnsdkjansdlkjansdlfjknflaskjdnflasdkjvnalkdjvnalsdkjvnalsdkjnflakjdsnflkajfdnlakdsjnflakjsdnflkajsdnfkjasdnlkfjnasldkjfndsajnflaksjdnflkajsdnlfkjsavnlkjdsnlvkjansldkfnalweiuf;svnjkbnalbskdfjsdkfnavkjndlkvjnasldfanslvkjfblhbsdlasjdbhakjbdlehslwefbsjdvldjnvldkjsnfalfbfbdslbflsadjlvbhsdskdlfjnalsdkjfblsdhbsdbdkjfnalksjdbfkljsdbfklsjabfdklsabfklsablksdjfnalksdjflkajsdfbsalkjdfbaklsjdbfkljdsabtranslated_sentencesting.aaaaaaaaaaaaaasdfjasdlfijalsdkfaljvnalksdjalsdhbasjdbfasdkjansldkjvnaldfkjvnsdkjansdlkjansdlfjknflaskjdnflasdkjvnalkdjvnalsdkjvnalsdkjnflakjdsnflkajfdnlakdsjnflakjsdnflkajsdnfkjasdnlkfjnasldkjfndsajnflaksjdnflkajsdnlfkjsavnlkjdsnlvkjansldkfnalweiuf;svnjkbnalbskdfjsdkfnavkjndlkvjnasldfanslvkjfblhbsdlasjdbhakjbdlehslwefbsjdvldjnvldkjsnfalfbfbdslbflsadjlvbhsdskdlfjnalsdkjfblsdhbsdbdkjfnalksjdbfkljsdbfklsjabfdklsabfklsablksdjfnalksdjflkajsdfbsalkjdfbaklsjdbfkljtranslated_sentencTesting.aaaaaaaaaaaaaasdfjasdlfijalsdkfaljvnalksdjalsdhbasjdbfasdkjansldkjvnaldfkjvnsdkjansdlkjansdlfjknflaskjdnflasdkjvnalkdjvnalsdkjvnalsdkjnflakjdsnflkajfdnlakdsjnflakjsdnflkajsdnfkjasdnlkfjnasldkjfndsajnflaksjdnflkajsdnlfkjsavnlkjdsnlvkjansldkfnalweiuf;svnjkbnalbskdfjsdkfnavkjndlkvjnasldfanslvkjfblhbsdlasjdbhakjbdlehslwefbsjdvldjnvldkjsnfalfbfbdslbflsadjlvbhsdskdlfjnalsdkjfblsdhbsdbdkjfnalksjdbfkljsdbfklsjabfdklsabfklsablksdjfnalksdjflkajsdfbsalkjdfbaklsjdbfkljdsabfl"
                                },
                                {
                                    "sentence_id" : 2,
                                    "original_sentence" : "파싱이 잘 됩니다!~",
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
        self.assertEqual(res.status_code, 410)


    def test_dataExport(self):
        pass                  
    #    res = self.app.post('/api/v2/admin/dataManager/export',
    #            data = {} )  
                              
                              
    def test_dataCounter_OK1(self):
        """
        성공 1. 모든 값이 들어갔을 때
        """
        res = self.app.get('/api/v2/admin/dataManager/dataCounter',
                data = json.dumps(dict(
                    original_language_id = 1, 
                    target_language_id = 2,
                    subject_id = 3,
                    format_id = 4,
                    tone_id = 2
                    )))
        self.assertEqual(res.status_code, 200)

    def test_dataCounter_OK2(self):
        """
        성공 2. parameter 중 하나의 값이 없을 때
        """
        res = self.app.get('/api/v2/admin/dataManager/dataCounter',
                data = json.dumps(dict(
                    original_language_id = 1, 
                    format_id = 4,
                    tone_id = 2
                    )))
        self.assertEqual(res.status_code, 200)
    '''
    def test_dataCounter_Fail1(self):
        """
        실패 1. DATATYPE이 다른 경우
        int로 설정되어 있는데 문자로 들어가도 200처리 된다 - 처리 필요
        """
        res = self.app.get('/api/v2/admin/dataManager/dataCounter',
                data = json.dumps(dict(
                   original_language_id = 1, 
                    target_language_id = 2,
                    subject_id = 'A',
                    format_id = 4,
                    tone_id = 2
                    )))
        self.assertEqual(res.status_code, 410)
    '''
