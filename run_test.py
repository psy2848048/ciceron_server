# -*- coding: utf-8 -*-
import os, application, unittest, tempfile, datetime, time, json, hashlib, io
from flask import url_for

class CiceronTestCase(unittest.TestCase):
    def setUp(self):
        #self.db_fd, application.app.config['DATABASE'] = tempfile.mkstemp()
        application.app.config['TESTING'] = True
        self.app = application.app.test_client()
        #self.app.g.db = application.connect_db()

    def tearDown(self):
        #os.close(self.db_fd)
        #os.unlink(application.app.config['DATABASE'])
        pass

    def signUp(self, email, password, name, mother_language_id):
        hasher = hashlib.sha256()
        hasher.update(password)
        password = hasher.hexdigest()
        return self.app.post('/api/signup', data=dict(
                email=email,
                password=password,
                name=name,
                mother_language_id=mother_language_id
                ), follow_redirects=True)

    def login(self, email):
        #rv = self.app.get('/api/login')
        #salt = json.loads(rv.data)['identifier']
        #salt = salt.encode('utf-8')

        #hasher = hashlib.sha256()
        #hasher.update(password)
        #temp_pass = hasher.hexdigest()

        #hasher2 = hashlib.sha256()
        #hasher2.update(salt + temp_pass + salt)
        #value = hasher2.hexdigest()
        #return self.app.post('/api/login', data=dict(
        #       email=email,
        #       password=value
        #   ), follow_redirects=True)
        with self.app.session_transaction() as sess:
            sess['useremail'] = email
            sess['logged_in'] = True

    def test_login(self):
        print "=============test_login=============="

        self.signUp(email="psy2848048@gmail.com",
		    password="ciceron!",
		    name="CiceronMaster",
		    mother_language_id=0)
        print ("SignUp complete")

        print ("Step 1: attempt to login with non-registered user")
        rv = self.login(email="psy2848048@nate.com",
        	    password="wleifasef"
        	    )
        print (rv.data)
        assert 'Not registered' in rv.data
        
        print ("Step 2: attempt to login with registered user but the password is wrong")
        rv = self.login(email="psy2848048@gmail.com",
        	    password="wleifasef"
        	    )
        print (rv.data)
        assert 'Please check the password' in rv.data
        rv = self.app.get('/api')
        print (rv.data)
        
        print ("Step 3: attempt to login with registered user, correct password")
        rv = self.login(email="psy2848048@gmail.com",
        	    password="ciceron!"
        	    )
        print (rv.data)
        assert 'You\'re logged with user' in rv.data
        rv = self.app.get('/api')
        print (rv.data)

    def test_idChecker(self):
        print ("=================test-nickchecker====================")
        rv = self.app.post('/api/idCheck', data=dict(email='psy2848048@gmail.com'))
        print rv.data
        assert 'Duplicated' in  rv.data

    def test_profile(self):
        print ("==============test-profile==============")
        rv = self.app.get("/api/user/profile")
        print (rv)
        print (rv.data)
        assert 'Login required' in rv.data
        rv = self.login(email="psy2848048@gmail.com")
        print ("Login complete")

        rv = self.app.get("/api/user/profile")
        print (rv)
        print "////Before prifileTest////"
        print rv.data

        rv = self.app.post("/api/user/profile",
                data=dict(
                    user_profileText="Test"
                    )
                )

        rv = self.app.get("/api/user/profile")
        print (rv.data)

    def test_pendingQueue(self):
        print "================test-pendingQueue=============="

        print "Login.."
        self.login(email="psy2848048@nate.com")

        print "Post SOS"
        text = "테스트테스트! 신나는 테스트.\n어떻게 울궈먹고 놀까나 나도 모르겠다 이히힛ㅋㅋ."
        rv = self.app.post('/api/requests', data=dict(
        		request_clientId="psy2848048@nate.com",
                request_originalLang=1,
                request_targetLang=2,
                request_isSos=True,
                request_format=0,
                request_subject=0,
                request_isText=True,
                request_text = text,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
        		request_points=0.50,
                request_context=""
        		))

        print "Post normal"
        text2 = "난 잘 몰라 암치기나 함 해보지 뭐.\n잘해보셔. 대충 살어. 날라리날라리~."
        rv = self.app.post('/api/requests', data=dict(
        		request_clientId="psy2848048@nate.com",
                request_originalLang=1,
                request_targetLang=2,
                request_isSos=False,
                request_format=0,
                request_subject=0,
                request_isText=True,
                request_text = text2,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_deltaFromDue=7890,
        		request_points=23.0,
                request_context="Wow!"
        		))

        response = json.loads(rv.data)
        sample_request_id = response['request_id']
        rv = self.app.get("/api/user/requests/%d/payment/postprocess?pay_via=alipay&status=success&user_id=%s&pay_amt=%.2f&pay_by=%s&use_point=%.2f&promo_type=%s&promo_code=%s&is_additional=%s" % (
            sample_request_id, 'psy2848048@nate.com', 23.0, 'web', 0, '', '', 'false'))

        self.login(email="psy2848048@gmail.com")
        rv = self.app.get('/api/user/translations/stoa')
        print "    %d tickets are applied." % len(json.loads(rv.data)['data'])

        print "Unicode test"
        self.login(email="psy2848048@nate.com")
        text3 = "스파이더맨, 누가 좀 도와줘요!\n아니면 사이드킥이라도!! 살려줘요!"
        rv = self.app.post('/api/requests', data=dict(
        		request_clientId="psy2848048@nate.com",
                request_originalLang=1,
                request_targetLang=2,
                request_isSos=True,
                request_format=0,
                request_subject=0,
                request_isText=True,
                request_text = text3,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
        		request_points=0,
                request_context="Korean request test"
        		))
        rv = self.app.get('/api/user/requests/stoa')
        requests = json.loads(rv.data)
        print "    Requested text: %s" % requests['data'][0]['request_text']

        meatshield_request_id = requests['data'][0]['request_id']
        print "    meatshield_request_id: %d" % meatshield_request_id
        print "    %d tickets are applied." % len(requests)

        print ""
        print "Delete request"
        rv = self.app.delete('/api/user/requests/pending/%d' % meatshield_request_id)

        self.login(email="psy2848048@gmail.com")
        rv = self.app.get('/api/user/translations/stoa')

        print ""
        print "Try to nego"
        print "    sample_request_id: %d" % sample_request_id
        rv = self.app.post('/api/user/translations/pending',
                data=dict(
                        request_id=sample_request_id,
                        translator_additionalPoint=28.0
                    )
                )
        print rv.data

        print "    Check client's pending"
        self.login(email="psy2848048@nate.com")
        rv = self.app.get('/api/user/requests/pending')
        print rv.data

        rv = self.app.get('/api/user/requests/pending/%d' % sample_request_id)
        requests = json.loads(rv.data)
        print "    %d tickets are applied." % len(requests)

        print "    Try to line in the double-queue"
        self.login(email="psy2848048@gmail.com")
        rv = self.app.post('/api/user/translations/pending',
                data=dict(
                        request_id=sample_request_id,
                        translator_additionalPoint=30.0
                    )
                )
        print rv.data

        print "    Another user queuing"
        self.login(email="admin@ciceron.me")
        rv = self.app.post('/api/user/translations/pending',
                data=dict(
                    request_id=sample_request_id,
                    translator_additionalPoint=31.0
                    )
                )
        print rv.data

        print "    Dequeue"
        self.login(email="admin@ciceron.me")
        rv = self.app.delete('/api/user/translations/pending/%d' % sample_request_id)
        print rv.data
        
        print "    Queue list"
        self.login(email="psy2848048@gmail.com")
        rv = self.app.get('/api/user/translations/pending')
        result = json.loads(rv.data)

        print "    psy2848048@nate.com accepts the nego psy2848048@gmail.com"
        self.login(email="psy2848048@nate.com")
        rv = self.app.post('/api/user/requests/pending',
                data=dict(
                    pay_by='web',
                    pay_via='alipay',
                    request_id=sample_request_id,
                    translator_userEmail='psy2848048@gmail.com'
                    )
                )
        result = json.loads(rv.data)
        print "Provided link from alipay:"
        print result

    def test_translation(self):
        print "Check change"
        rv = self.app.get('/api/requests')
        print rv.data

        print "My translation list"
        rv = self.app.get('/api/user/translations/ongoing')
        print rv.data

        print "Check my work"
        rv = self.app.get('/api/user/translations/ongoing/0')
        print rv.data

        print "Working/Auto save"
        rv = self.app.put('/api/user/translations/ongoing/0',
                data=dict(
                    request_translatedText="This is result\nCheck it!",
                    request_comment="Comment",
                    request_tone="Tone"
                    ))
        print rv.data

        print "Check my work 2"
        rv = self.app.get('/api/user/translations/ongoing/0')
        print rv.data

        print "Post"
        rv = self.app.post('/api/user/translations/complete',
                data=dict(
                    request_id=0,
                    request_translatedText="This is second result\nCheck it again, please!",
                    request_comment="Comment2",
                    request_tone="Tone2"
                    ))
        print rv.data

        print "This request doesn't ongoing anymore"
        rv = self.app.get('/api/user/translations/ongoing/0')
        print rv.data

        print "Check complete"
        rv = self.app.get('/api/user/translations/complete/0')
        print rv.data

        print "Check group list: translators"
        rv = self.app.get('/api/user/translations/complete/groups')
        print rv.data

        print "Check itmes in group: translators"
        rv = self.app.get('/api/user/translations/complete/groups/0')
        print rv.data

        print "Create one group: translators"
        rv = self.app.post('/api/user/translations/complete/groups', data=dict(
            group_name="Another"))

        rv = self.app.get('/api/user/translations/complete/groups')
        print rv.data

        print "Change request #0 to group #1"
        rv = self.app.post('/api/user/translations/complete/groups/1', data=dict(
                request_id=0))

        rv = self.app.get('/api/user/translations/complete/groups/1')
        print rv.data

        print "No request in group #0"
        rv = self.app.get('/api/user/translations/complete/groups/0')
        print rv.data

        print "Set title for request #0"
        rv = self.app.post('/api/user/translations/complete/0/title', data=dict(
            title_text = "Test"))

        rv = self.app.get('/api/user/translations/complete/groups/1')
        print rv.data

        print "Switch request user"
        self.login(email="happyhj@gmail.com",
        	    password="ciceron!"
        	    )

        print "Check complete"
        rv = self.app.get('/api/user/requests/complete/0')
        print rv.data

        print "Check group: client"
        rv = self.app.get('/api/user/requests/complete/groups')
        print rv.data

        print "Create group #1: Client"
        rv = self.app.post('/api/user/requests/complete/groups', data=dict(
            group_name="Another client"))
        rv = self.app.get('/api/user/requests/complete/groups')
        print rv.data
        
        print "Change request #0 to group #1"
        rv = self.app.post('/api/user/requests/complete/groups/1', data=dict(
                request_id=0))

        rv = self.app.get('/api/user/requests/complete/groups/1')
        print rv.data

        print "No item in group #0: Client"
        rv = self.app.get('/api/user/requests/complete/groups/0')
        print rv.data

        print "Delete group #0"
        rv = self.app.delete('/api/user/requests/complete/groups/0')
        print rv.data

        print "Create group #2: Client"
        rv = self.app.post('/api/user/requests/complete/groups', data=dict(
            group_name="안녕?"))
        rv = self.app.get('/api/user/requests/complete/groups')
        print rv.data

        print "Delete group #2"
        rv = self.app.delete('/api/user/requests/complete/groups/2')
        rv = self.app.get('/api/user/requests/complete/groups')
        print rv.data

    def test_expectedDate(self):
        print "================test-expectedDate=============="
        self.signUp(email="psy2848048@gmail.com",
        	    password="ciceron!",
        	    name="CiceronMaster",
        	    mother_language_id=0)
        self.login(email="psy2848048@gmail.com",
        	    password="ciceron!"
        	    )
        
        text = "This is test text\nAnd I donno how to deal with"
        rv = self.app.post('/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=1,
                request_isSos=True,
                request_format=0,
                request_subject=0,
                request_registeredTime=datetime.datetime.now(),
                request_isText=True,
                request_text = text,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_words=len(text.split(' ')),
                request_dueTime=datetime.datetime.now() + datetime.timedelta(days=5),
        		request_points=0.50,
                request_context=""
        		))
        text2 = "testtesttest\nChinese\na;eoifja;ef"
        rv = self.app.post('/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=2,
                request_isSos=True,
                request_format=0,
                request_subject=0,
                request_registeredTime=datetime.datetime.now(),
                request_isText=True,
                request_text = text2,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_words=len(text2.split(' ')),
                request_dueTime=datetime.datetime.now() + datetime.timedelta(days=5),
        		request_points=0,
                request_context="Wow!"
        		))
        rv = self.app.get('/api/requests')
        print rv.data

        self.signUp(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!",
        	    name="CiceronUser",
        	    mother_language_id=2)
        self.signUp(email="admin@ciceron.me",
        	    password="!master@Of#Ciceron$",
        	    name="AdminCiceron",
        	    mother_language_id=0)
        self.login(email="admin@ciceron.me",
        	    password="!master@Of#Ciceron$"
        	    )
        rv = self.app.post('/language_assigner', data=dict(email='jun.hang.lee@sap.com', language=0))
        self.login(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!"
        	    )

        self.app.post('/api/user/profile', data=dict(
            user_isTranslator=1))

        self.app.post('/api/user/translations/ongoing', data=dict(request_id=0))
        self.app.post('/api/user/translations/ongoing', data=dict(request_id=1))
        print "Preparation done"

        print "1. Set expected time"
        rv = self.app.get('/api/user/translations/ongoing/0/expected')
        rv = self.app.post('/api/user/translations/ongoing/0/expected',data=dict(
            expectedTime=datetime.datetime.now() + datetime.timedelta(days=5)))
        print rv.data

        print "2. Give up translating"
        rv = self.app.delete('/api/user/translations/ongoing/1/expected')
        print rv.data

        print "Check the result"
        print "1) My current job"
        rv = self.app.get('/api/user/translations/ongoing')
        print rv.data

        print "2) Current newsfeed"
        rv = self.app.get('/api/requests')
        print rv.data

    def test_paypal(self):
        self.signUp(email="psy2848048@gmail.com",
        	    password="ciceron!",
        	    name="CiceronMaster",
        	    mother_language_id=0)
        self.login(email="psy2848048@gmail.com",
        	    password="ciceron!"
        	    )
        text = "This is test text\nAnd I donno how to deal with"
        rv = self.app.post('/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=1,
                request_isSos=False,
                request_format=0,
                request_subject=0,
                request_registeredTime=datetime.datetime.now(),
                request_isText=True,
                request_text = text,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_words=len(text.split(' ')),
                request_dueTime=datetime.datetime.now() + datetime.timedelta(days=5),
        		request_points=0.50,
                request_context=""
        		))
        print "Before payment"
        rv = self.app.get('/requests')
        print rv.data

        rv = self.app.post('/user/requests/0/payment/start',
                data=dict(
                    pay_amount=1.32,                   # Amount
                    pay_via='paypal'
                    ))
        print rv.data
        response_temp = json.loads(rv.data)

        print response_temp['redirect_url']

        rv = self.app.get(response_temp['redirect_url'])
        rv = self.app.get('/requests')
        print rv.data

    def test_logWrite(self):
        rv = self.app.get('/api/scheduler/log_transfer')
        print rv.data

if __name__ == "__main__":
    unittest.main()
