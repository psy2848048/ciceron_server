# -*- coding: utf-8 -*-
import os, application, unittest, tempfile, datetime, time, json, hashlib, io
from flask import url_for

class CiceronTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, application.app.config['DATABASE'] = tempfile.mkstemp()
        application.app.config['TESTING'] = True
        self.app = application.app.test_client()
        application.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(application.app.config['DATABASE'])

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

    def login(self, email, password):
        rv = self.app.get('/api/login')
        salt = json.loads(rv.data)['identifier']
        salt = salt.encode('utf-8')

        hasher = hashlib.sha256()
        hasher.update(password)
        temp_pass = hasher.hexdigest()

        hasher2 = hashlib.sha256()
        hasher2.update(salt + temp_pass + salt)
        value = hasher2.hexdigest()
        return self.app.post('/api/login', data=dict(
               email=email,
               password=value
           ), follow_redirects=True)

    def test_login(self):
        print ("=============test_login==============")

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
        assert 'You may use' in  rv.data
        
        self.signUp(email="psy2848048@gmail.com",
        	    password="ciceron!",
        	    name="CiceronMaster",
        	    mother_language_id=0)
        
        rv = self.app.post('/api/idCheck', data=dict(email='psy2848048@gmail.com'))
        print rv.data
        assert 'Duplicated' in  rv.data

    def test_login_decorator(self):
        print ("==============test-login-req-decorator==============")
        rv = self.app.get("/api/user/profile")
        print (rv)
        print (rv.data)
        assert 'Login required' in rv.data

        self.signUp(email="psy2848048@gmail.com",
        	    password="ciceron!",
        	    name="CiceronMaster",
        	    mother_language_id=0)
        rv = self.login(email="psy2848048@gmail.com",
        	    password="ciceron!"
        	    )

        print ("Login complete")

        rv = self.app.get("/api/user/profile")
        print (rv)
        print (rv.data)

        rv = self.app.post("/api/user/profile",
                data=dict(
                    user_profileText="Test"
                    )
                )

        rv = self.app.get("/api/user/profile")
        print (rv.data)

    def test_request(self):
        print ("=============test-request===================")
        self.signUp(email="psy2848048@gmail.com",
        	    password="ciceron!",
        	    name="CiceronMaster",
        	    mother_language_id=0)
        self.login(email="psy2848048@gmail.com",
        	    password="ciceron!"
        	    )
        
        text = "This is test text\nAnd I donno how to deal with"
        print ("Post normal request without money")
        rv = self.app.post('/api/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=1,
                request_isSos=True,
                request_format=0,
                request_subject=0,
                request_isText=True,
                request_text = text,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_deltaFromDue=3600,
        		request_points=0.50,
                request_context=""
        		))

        try:
            assert "Request ID" in rv.data
        except:
            print (rv.data)
            raise AssertionError

        print ("Pass step 1")

        text2 = "testtesttest\nChinese\n안녕하세요,おはようございます"
        #text2 = "testtesttest\nChinese\\"
        
        rv = self.app.post('/api/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=2,
                request_isSos=True,
                request_format=0,
                request_subject=0,
                request_isText=True,
                request_text = text2,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_words=len(text.split(' ')),
                request_deltaFromDue=5500,
        		request_points=0,
                request_context="Wow!"
        		))
        try:
            assert "Request ID" in rv.data
        except:
            print rv.data
            raise AssertionError

        print "Passed step 2"
        
        rv = self.app.get('/api/requests')
        print "Posted list"
        print rv.data
        
        rv = self.app.get('/api/requests?since=%s' % time.time())
        print "Posted list with last_post_time"
        print rv.data
        
        print "Test with different user"
        self.signUp(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!",
        	    name="CiceronUser",
        	    mother_language_id=2)
        self.login(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!"
        	    )
        
        rv = self.app.get('/api/requests')
        print "Posted list"
        print rv.data

    def test_pick_request(self):
        print "================test-pick-request=============="
        self.signUp(email="psy2848048@gmail.com",
        	    password="ciceron!",
        	    name="CiceronMaster",
        	    mother_language_id=0)
        self.login(email="psy2848048@gmail.com",
        	    password="ciceron!"
        	    )
        
        text = "This is test text\nAnd I donno how to deal with"
        rv = self.app.post('/api/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=1,
                request_isSos=True,
                request_format=0,
                request_subject=0,
                request_isText=True,
                request_text = text,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_words=len(text),
        		request_points=0.50,
                request_context=""
        		))
        text2 = "testtesttest\nChinese\na;eoifja;ef"
        rv = self.app.post('/api/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=2,
                request_isSos=False,
                request_format=0,
                request_subject=0,
                request_deltaFromDue=15020,
                request_isText=True,
                request_text = text2,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_words=len(text),
        		request_points=0,
                request_context="Wow!"
        		))
        
        rv = self.app.get('/api/requests')
        print "Posted list"
        print rv.data

        print "Attempt to translate what he/she requested"

        rv = self.app.post('/api/user/translations/pending', data=dict(request_id=0))
        print rv.data
        
        self.signUp(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!",
        	    name="CiceronUser",
        	    mother_language_id=1)

        self.signUp(email="admin@ciceron.me",
        	    password="!master@Of#Ciceron$",
        	    name="AdminCiceron",
        	    mother_language_id=0)
        self.login(email="admin@ciceron.me",
        	    password="!master@Of#Ciceron$"
        	    )
        rv = self.app.post('/api/admin/language_assigner', data=dict(email='jun.hang.lee@sap.com', language_id=0))
        print rv.data
        self.app.get('/api/logout')

        self.login(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!"
        	    )

        rv = self.app.post('/api/user/translations/pending', data=dict(
            request_id=0
            ))
        
        print "Queue list"
        print rv.data

        rv = self.app.get('/api/user/translations/pending')
        print "Posted list"
        print rv.data

    def test_translate(self):
        print "================test-translate=============="
        self.signUp(email="happyhj@gmail.com",
        	    password="ciceron!",
        	    name="CiceronMaster",
        	    mother_language_id=0)
        self.login(email="happyhj@gmail.com",
        	    password="ciceron!"
        	    )
        
        text = "This is test text\nAnd I donno how to deal with"
        rv = self.app.post('/api/requests', data=dict(
        		request_clientId="happyhj@gmail.com",
                request_originalLang=0,
                request_targetLang=1,
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
        print rv.data
        text2 = "testtesttest\nChinese\na;eoifja;ef"
        rv = self.app.post('/api/requests', data=dict(
        		request_clientId="happyhj@gmail.com",
                request_originalLang=0,
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
        		request_points=0,
                request_context="Wow!"
        		))
        print rv.data

        rv = self.app.get('/api/requests')
        print rv.data

        print "Unicode test"
        text3 = "Who somebody can test it?\n한국어\tsiol"
        rv = self.app.post('/api/requests', data=dict(
        		request_clientId="happyhj@gmail.com",
                request_originalLang=0,
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

        rv = self.app.get('/api/requests')
        print rv.data

        print "Delete request"
        rv = self.app.delete('/api/requests/2')
        rv = self.app.get('/api/requests')
        print rv.data

        print "Attempt to translate what he/she requested"

        rv = self.app.post('/api/user/translations/pending', data=dict(request_id=0))
        print rv.data

        rv = self.app.get('/api/user/requests/pending')
        print rv.data

        rv = self.app.get('/api/user/requests/pending/0')
        print rv.data
        
        self.signUp(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!",
        	    name="CiceronUser",
        	    mother_language_id=1)
        self.signUp(email="admin@ciceron.me",
        	    password="!master@Of#Ciceron$",
        	    name="AdminCiceron",
        	    mother_language_id=0)
        self.login(email="admin@ciceron.me",
        	    password="!master@Of#Ciceron$"
        	    )
        rv = self.app.post('/api/admin/language_assigner', data=dict(email='jun.hang.lee@sap.com', language_id=0))
        print rv.data
        self.login(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!"
        	    )

        print "Line in the queue"
        rv = self.app.post('/api/user/translations/pending', data=dict(request_id=0))
        print rv.data

        print "Try to line in the double-queue"
        rv = self.app.post('/api/user/translations/pending', data=dict(request_id=0))
        print rv.data

        print "Another user queuing"
        self.signUp(email="jae.hong.park@sap.com",
        	    password="meeToo",
        	    name="CiceronUser2",
        	    mother_language_id=1)
        self.login(email="admin@ciceron.me",
        	    password="!master@Of#Ciceron$"
        	    )
        rv = self.app.post('/api/admin/language_assigner', data=dict(email='jae.hong.park@sap.com', language_id=0))
        self.login(email="jae.hong.park@sap.com",
        	    password="meeToo"
        	    )
        rv = self.app.post('/api/user/translations/pending', data=dict(request_id=0))
        print rv.data

        print "Re-login"
        self.login(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!"
        	    )

        print "Dequeue"
        rv = self.app.delete('/api/user/translations/pending/0')
        print rv.data
        
        print "Queue list"
        rv = self.app.get('/api/user/translations/pending')
        print rv.data

        print "Line in the queue"
        rv = self.app.post('/api/user/translations/pending', data=dict(request_id=0))
        print rv.data

        print "Queue list"
        rv = self.app.get('/api/user/translations/pending')
        print rv.data

        rv = self.app.get('/api/user/translations/pending')
        print "Posted list"
        print rv.data

        print "Take a request"
        rv = self.app.post('/api/user/translations/ongoing', data=dict(request_id=0))
        print rv.data

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
        rv = self.app.get('/requests')
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

        self.app.post('/user/profile', data=dict(
            user_isTranslator=1))

        self.app.post('/user/translations/ongoing', data=dict(request_id=0))
        self.app.post('/user/translations/ongoing', data=dict(request_id=1))
        print "Preparation done"

        print "1. Set expected time"
        rv = self.app.get('/user/translations/ongoing/0/expected')
        rv = self.app.post('/user/translations/ongoing/0/expected',data=dict(
            expectedTime=datetime.datetime.now() + datetime.timedelta(days=5)))
        print rv.data

        print "2. Give up translating"
        rv = self.app.delete('/user/translations/ongoing/1/expected')
        print rv.data

        print "Check the result"
        print "1) My current job"
        rv = self.app.get('/user/translations/ongoing')
        print rv.data

        print "2) Current newsfeed"
        rv = self.app.get('/requests')
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

if __name__ == "__main__":
    unittest.main()
