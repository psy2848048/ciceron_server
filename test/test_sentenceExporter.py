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

    def test_dataCounter_OK1(self):
        """
        성공 1. 모든 값이 들어갔을 때
        """
        res = self.app.get('/api/v2/admin/dataManager/dataCounter',
                query_string = {
                    'original_language_id' : 1, 
                    'target_language_id' : 2,
                    'subject_id' : 3,
                    'format_id' : 4,
                    'tone_id' : 2
                    })
        self.assertEqual(res.status_code, 200)

    def test_dataCounter_OK2(self):
        """
        성공 2. parameter 중 하나의 값이 없을 때
        """
        res = self.app.get('/api/v2/admin/dataManager/dataCounter',
                query_string = {
                    'original_language_id' : 1, 
                    'subject_id' : 3,
                    'format_id' : 4,
                    'tone_id' : 2
                    })
        self.assertEqual(res.status_code, 200)

    def test_dataCounter_Fail1(self):
        """
        실패 1. DATATYPE이 다른 경우
        int로 설정되어 있는데 문자로 들어가도 200처리 된다 - 처리 필요
        """
        res = self.app.get('/api/v2/admin/dataManager/dataCounter',
                query_string = {
                    'original_language_id' : 1, 
                    'target_language_id' : 2,
                    'subject_id' : 'a',
                    'format_id' : 4,
                    'tone_id' : 2
                    })
        self.assertEqual(res.status_code, 410)


###########################################################################################


    def test_dataExport_OK1(self):
        """
        성공 1. 모든 값이 제대로 들어갔을 때
        """
        res = self.app.get('/api/v2/admin/dataManager/export',
                query_string = {
                    'original_language_id' : 1, 
                    'target_language_id' : 2,
                    'subject_id' : 3,
                    'format_id' : 4,
                    'tone_id' : 2
                    })
        self.assertEqual(res.status_code, 200)
                              
    def test_dataExport_OK2(self):
        """
        성공 2. optional 값 중에 하나가 안들어갔을 때 
        """
        res = self.app.get('/api/v2/admin/dataManager/export',
                query_string = {
                    'original_language_id' : 1, 
                    'target_language_id' : 2,
                    'subject_id' : 3,
                    'tone_id' : 2
                    })
        self.assertEqual(res.status_code, 200)

#    def test_dataExport_Fail1(self):
#        """
#        실패 1. 없는 값을 요청했을 때
#        """
#        res = self.app.get('/api/v2/admin/dataManager/export',
#                query_string = {
#                    'original_language_id' : 1, 
#                    'target_language_id' : 200,
#                    'subject_id' : 3,
#                    'format_id' : 4,
#                    'tone_id' : 2
#                    })
#        self.assertEqual(res.status_code, 410)

    def test_dataExport_Fail2(self):
        """
        실패 2. 데이터 타입이 다른 경우
        """
        res = self.app.get('/api/v2/admin/dataManager/export',
                query_string = {
                    'original_language_id' : 1, 
                    'target_language_id' : 'aaa',
                    'subject_id' : 3,
                    'format_id' : 4,
                    'tone_id' : 2
                    })
        self.assertEqual(res.status_code, 410)


###########################################################################################


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


###########################################################################################


    def test_parseSentence_OK1(self):
        """
        성공 1. 모든 값이 제대로 들어갔을 경우
        """
        res = self.app.post('/api/v2/admin/dataManager/parseSentence',
                data = dict(
                    original_string = "테스트 중입니다. 만나서 반갑습니다.",
                    translated_string = "Testing. Nice to meet you."))
        self.assertEqual(res.status_code, 200)
    
    def test_parseSentence_Fail1(self):
        """
        실패 1. translated_string 값이 안들어 갔을 때
        """
        res = self.app.post('/api/v2/admin/dataManager/parseSentence',
                data = dict(
                    original_string = "테스트 중입니다. 만나서 반갑습니다."))
        self.assertEqual(res.status_code, 400)
   
#    def test_parseSentence_Fail2(self):
#         """
#         실패 2. 파라미터안에 값이 안들어간 경우
#         """
#         res = self.app.post('/api/v2/admin/dataManager/parseSentence',
#                 data = dict(
#                     original_string = "",
#                     translated_string = "Testing. Nice to meet you."))
#         self.assertEqual(res.status_code, 400)


