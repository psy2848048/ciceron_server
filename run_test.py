# -*- coding: utf-8 -*-
import os, run, unittest, tempfile, datetime, time, json, hashlib, io
from flask import url_for

class CiceronTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, run.app.config['DATABASE'] = tempfile.mkstemp()
        run.app.config['TESTING'] = True
        self.app = run.app.test_client()
        run.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(run.app.config['DATABASE'])

    def signUp(self, email, password, name, mother_language_id):
        hasher = hashlib.sha256()
        hasher.update(password)
        password = hasher.hexdigest()
        return self.app.post('/signup', data=dict(
                email=email,
                password=password,
                name=name,
                mother_language_id=mother_language_id
                ), follow_redirects=True)

    def login(self, email, password):
        rv = self.app.get('/login')
        salt = json.loads(rv.data)['identifier']
        salt = salt.encode('utf-8')

        hasher = hashlib.sha256()
        hasher.update(password)
        temp_pass = hasher.hexdigest()

        hasher2 = hashlib.sha256()
        hasher2.update(salt + temp_pass + salt)
        value = hasher2.hexdigest()
        return self.app.post('/login', data=dict(
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
        rv = self.app.get('/')
        print (rv.data)
        
        print ("Step 3: attempt to login with registered user, correct password")
        rv = self.login(email="psy2848048@gmail.com",
        	    password="ciceron!"
        	    )
        print (rv.data)
        assert 'You\'re logged with user' in rv.data
        rv = self.app.get('/')
        print (rv.data)

    def test_idChecker(self):
        print ("=================test-nickchecker====================")
        
        rv = self.app.get('/idCheck?email=psy2848048@gmail.com')
        print (rv)
        assert 'You may use' in  rv.data
        
        self.signUp(email="psy2848048@gmail.com",
        	    password="ciceron!",
        	    name="CiceronMaster",
        	    mother_language_id=0)
        
        rv = self.app.get('/idCheck?email=psy2848048@gmail.com')
        print (rv)
        assert 'Duplicated' in  rv.data

    def test_login_decorator(self):
        print ("==============test-login-req-decorator==============")
        rv = self.app.get("/user/profile")
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

        rv = self.app.get("/user/profile")
        print (rv)
        print (rv.data)

        rv = self.app.post("/user/profile",
                data=dict(
                    user_profileText="Test"
                    )
                )

        rv = self.app.get("/user/profile")
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
                request_dueTime=datetime.datetime.now(),
        		request_points=0.50,
                request_context=""
        		))

        try:
            assert "Request ID" in rv.data
        except:
            print (rv.data)
            raise AssertionError

        print ("Pass step 1")

        text2 = "testtesttest\nChinese\na;eoifja;ef"
        
        rv = self.app.post('/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=2,
                request_isSos=False,
                request_format=0,
                request_subject=0,
                request_registeredTime=datetime.datetime.now(),
                request_isText=True,
                request_text = text2,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_words=len(text.split(' ')),
                request_dueTime=datetime.datetime.now(),
        		request_points=0,
                request_context="Wow!"
        		))
        try:
            assert "Request ID" in rv.data
        except:
            print rv.data
            raise AssertionError

        print "Passed step 2"
        
        rv = self.app.get('/requests')
        print "Posted list"
        print rv.data
        
        rv = self.app.get('/requests?since=%f' % time.time())
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
        
        rv = self.app.get('/requests')
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
                request_dueTime=datetime.datetime.now(),
        		request_points=0.50,
                request_context=""
        		))
        text2 = "testtesttest\nChinese\na;eoifja;ef"
        rv = self.app.post('/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=2,
                request_isSos=False,
                request_format=0,
                request_subject=0,
                request_registeredTime=datetime.datetime.now(),
                request_isText=True,
                request_text = text2,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_words=len(text.split(' ')),
                request_dueTime=datetime.datetime.now(),
        		request_points=0,
                request_context="Wow!"
        		))
        
        rv = self.app.get('/requests')
        print "Posted list"
        print rv.data

        print "Attempt to translate what he/she requested"

        rv = self.app.post('/user/translations/pending', data=dict(request_id=0))
        print rv.data
        
        self.signUp(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!",
        	    name="CiceronUser",
        	    mother_language_id=2)
        self.login(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!"
        	    )

        rv = self.app.post('/user/translations/pending', data=dict(
            request_id=0
            ))
        
        print "Queue list"
        print rv.data

        rv = self.app.get('/user/translations/pending')
        print "Posted list"
        print rv.data

    def test_translate(self):
        print "================test-translate=============="
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
                request_dueTime=datetime.datetime.now(),
        		request_points=0.50,
                request_context=""
        		))
        text2 = "testtesttest\nChinese\na;eoifja;ef"
        rv = self.app.post('/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=2,
                request_isSos=False,
                request_format=0,
                request_subject=0,
                request_registeredTime=datetime.datetime.now(),
                request_isText=True,
                request_text = text2,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_words=len(text2.split(' ')),
                request_dueTime=datetime.datetime.now(),
        		request_points=0,
                request_context="Wow!"
        		))

        rv = self.app.get('/requests')
        print rv.data

        print "Unicode test"
        text3 = u"Who somebody can test it?\n한국어\tsiol"
        rv = self.app.post('/requests', data=dict(
        		request_clientId="psy2848048@gmail.com",
                request_originalLang=0,
                request_targetLang=2,
                request_isSos=True,
                request_format=0,
                request_subject=0,
                request_registeredTime=datetime.datetime.now(),
                request_isText=True,
                request_text = text3,
                request_isPhoto=False,
                request_isSound=False,
                request_isFile=False,
                request_words=len(text3.split(' ')),
                request_dueTime=datetime.datetime.now(),
        		request_points=0,
                request_context="Korean request test"
        		))

        rv = self.app.get('/requests')
        print rv.data

        print "Delete request"
        rv = self.app.delete('/requests/2')
        rv = self.app.get('/requests')
        print rv.data

        print "Attempt to translate what he/she requested"

        rv = self.app.post('/user/translations/pending/0')
        print rv.data
        
        self.signUp(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!",
        	    name="CiceronUser",
        	    mother_language_id=2)
        self.login(email="jun.hang.lee@sap.com",
        	    password="IWantToExitw/SAPLabsKoreaFucking!!!"
        	    )

        self.app.post('/user/profile', data=dict(
            user_isTranslator=1))

        print "Line in the queue"
        rv = self.app.post('/user/translations/pending/0')
        print rv.data

        print "Try to line in the double-queue"
        rv = self.app.post('/user/translations/pending/0')
        print rv.data

        print "Dequeue"
        rv = self.app.delete('/user/translations/pending/0')
        print rv.data
        
        print "Queue list"
        rv = self.app.get('/user/translations/pending')
        print rv.data

        print "Line in the queue"
        rv = self.app.post('/user/translations/pending/0')
        print rv.data

        print "Queue list"
        rv = self.app.get('/user/translations/pending')
        print rv.data

        rv = self.app.get('/user/translations/pending')
        print "Posted list"
        print rv.data

        print "Take a request"
        rv = self.app.post('/user/translations/ongoing', data=dict(request_id=0))
        print rv.data

        print "Check change"
        rv = self.app.get('/requests')
        print rv.data

        print "My translation list"
        rv = self.app.get('/user/translations/ongoing')
        print rv.data

        print "Check my work"
        rv = self.app.get('/user/translations/ongoing/0')
        print rv.data

        print "Working/Auto save"
        rv = self.app.put('/user/translations/ongoing/0',
                data=dict(
                    request_translatedText="This is result\nCheck it!",
                    request_comment="Comment",
                    request_tone="Tone"
                    ))
        print rv.data

        print "Check my work 2"
        rv = self.app.get('/user/translations/ongoing/0')
        print rv.data

        print "Post"
        rv = self.app.post('/user/translations/complete/0',
                data=dict(
                    request_translatedText="This is second result\nCheck it again, please!",
                    request_comment="Comment2",
                    request_tone="Tone2"
                    ))
        print rv.data

        print "This request doesn't ongoing anymore"
        rv = self.app.get('/user/translations/ongoing/0')
        print rv.data

        print "Check complete"
        rv = self.app.get('/user/translations/complete/0')
        print rv.data

        print "Check group list: translators"
        rv = self.app.get('/user/translations/complete/groups')
        print rv.data

        print "Check itmes in group: translators"
        rv = self.app.get('/user/translations/complete/groups/0')
        print rv.data

        print "Create one group: translators"
        rv = self.app.post('/user/translations/complete/groups', data=dict(
            group_name="Another"))

        rv = self.app.get('/user/translations/complete/groups')
        print rv.data

        print "Change request #0 to group #1"
        rv = self.app.post('/user/translations/complete/groups/1', data=dict(
                request_id=0))

        rv = self.app.get('/user/translations/complete/groups/1')
        print rv.data

        print "No request in group #0"
        rv = self.app.get('/user/translations/complete/groups/0')
        print rv.data

        print "Set title for request #0"
        rv = self.app.post('/user/translations/complete/0/title', data=dict(
            title_text = "Test"))

        rv = self.app.get('/user/translations/complete/groups/1')
        print rv.data

        print "Switch request user"
        self.login(email="psy2848048@gmail.com",
        	    password="ciceron!"
        	    )

        print "Check complete"
        rv = self.app.get('/user/requests/complete/0')
        print rv.data

        print "Check group: client"
        rv = self.app.get('/user/requests/complete/groups')
        print rv.data

        print "Create group #1: Client"
        rv = self.app.post('/user/requests/complete/groups', data=dict(
            group_name="Another client"))
        rv = self.app.get('/user/requests/complete/groups')
        print rv.data
        
        print "Change request #0 to group #1"
        rv = self.app.post('/user/requests/complete/groups/1', data=dict(
                request_id=0))

        rv = self.app.get('/user/requests/complete/groups/1')
        print rv.data

        print "No item in group #0: Client"
        rv = self.app.get('/user/requests/complete/groups/0')
        print rv.data

if __name__ == "__main__":
    unittest.main()
