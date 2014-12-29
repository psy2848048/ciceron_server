import os, run, unittest, tempfile, datetime, time
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

    def signUp(self, username, password, nickname, mother_language):
        return self.app.post('/signUp_email', data=dict(
		username=username,
		password=password,
		nickname=nickname,
		mother_language=mother_language
		), follow_redirects=True)

    def login(self, username, password):
        return self.app.post('/login_email', data=dict(
		    username=username,
		    password=password
		), follow_redirects=True)

    def test_login(self):
        print "=============test_login=============="

        self.signUp(username="psy2848048@gmail.com",
		    password="ciceron!",
		    nickname="CiceronMaster",
		    mother_language="Korean")
	print "SignUp complete"

	print "Step 1: attempt to login with non-registered user"
	rv = self.login(username="psy2848048@nate.com",
		    password="wleifasef"
		    )
	print rv.data
        assert 'Not registered' in rv.data

	print "Step 2: attempt to login with registered user but the password is wrong"
	rv = self.login(username="psy2848048@gmail.com",
		    password="wleifasef"
		    )
	print rv.data
        assert 'Please check the password' in rv.data
        rv = self.app.get('/')
	print rv.data

	print "Step 3: attempt to login with registered user, correct password"
	rv = self.login(username="psy2848048@gmail.com",
		    password="ciceron!"
		    )
	print rv.data
        assert 'You\'re logged with user' in rv.data
	rv = self.app.get('/')
	print rv.data

    def test_nickchecker(self):
	print "=================test-nickchecker===================="

	rv = self.app.get('/nickCheck?nickname=psy2848048')
	print rv
	assert 'You may use' in  rv.data

        self.signUp(username="psy2848048@gmail.com",
		    password="ciceron!",
		    nickname="CiceronMaster",
		    mother_language="Korean")

	rv = self.app.get('/nickCheck?nickname=CiceronMaster')
	print rv
	assert 'Duplicated' in  rv.data

    def test_login_decorator(self):
	print "==============test-login-req-decorator=============="
	rv = self.app.get("/pick_request/1")
	print rv
	print rv.data
	assert 'Login required'

    def test_Post(self):
	print "=============test-Post==================="
        self.signUp(username="psy2848048@gmail.com",
		    password="ciceron!",
		    nickname="CiceronMaster",
		    mother_language="Korean")
	self.login(username="psy2848048@gmail.com",
		    password="ciceron!"
		    )

	print "Post normal request without money"
	rv = self.app.post('/post', data=dict(
			from_lang="Korean",
			to_lang="English",
			is_SOS=0,
			main_text="English is too difficult to learn and use properly. I really need your help",
			format="Formal",
			subject="Announcement",
			price=0.50
			))
	try:
	    assert "Not enough money" in rv.data
	except:
	    print rv.data
	    raise AssertionError


	rv = self.app.post('/post', data=dict(
			from_lang="Korean",
			to_lang="English",
			is_SOS=1,
			main_text="English is too difficult to learn and use properly. I really need your help",
			format="Thesis",
			subject="Scholar",
			price=0.50
			))
	try:
	    assert "Posted" in rv.data
	except:
	    print rv.data
	    raise AssertionError

        rv = self.app.get('/post_list')
	print "Posted list"
	print rv.data

        rv = self.app.get('/post_list?last_post_time=%f' % time.time())
	print "Posted list with last_post_time"
	print rv.data

        rv = self.app.get('/history_requester')
        print "History of psy2848048@gmail.com"
	print rv.data

        rv = self.app.get('/history_requester?last_post_time=%f' % time.time())
	print "History with last_post_time"
	print rv.data

        print "Test with different user"
        self.signUp(username="jun.hang.lee@sap.com",
		    password="IWantToExitw/SAPLabsKoreaFucking!!!",
		    nickname="CiceronUser",
		    mother_language="Korean")
	self.login(username="jun.hang.lee@sap.com",
		    password="IWantToExitw/SAPLabsKoreaFucking!!!"
		    )

        rv = self.app.get('/post_list')
	print "Posted list"
	print rv.data

        rv = self.app.get('/history_traslator')
        print "History of jun.hang.lee@sap.com"
	print rv.data

    def test_pick_request(self):
	print "================test-pick-request=============="
        self.signUp(username="psy2848048@gmail.com",
		    password="ciceron!",
		    nickname="CiceronMaster",
		    mother_language="Korean")
	self.login(username="psy2848048@gmail.com",
		    password="ciceron!"
		    )

	rv = self.app.post('/post', data=dict(
			from_lang="Korean",
			to_lang="English",
			is_SOS=0,
			main_text="English is too difficult to learn and use properly. I really need your help",
			format="Formal",
			subject="Announcement",
			price=0.50
			))
	try:
	    assert "Not enough" in rv.data
	except:
            print rv.data
	    raise AssertionError

	print "1. Pick request which you requested. Error expected."

	rv = self.app.post('/post', data=dict(
			from_lang="Korean",
			to_lang="English",
			is_SOS=1,
			main_text="English is too difficult to learn and use properly. I really need your help",
			format="Thesis",
			subject="Scholar",
			price=0.50
			))
        try:
	    assert "Posted" in rv.data
	except:
	    print rv.data
	    raise AssertionError

        print "Try to pick"
	rv = self.app.get('/pick_request/1')
	try:
	    assert "You cannot translate your request"
	except:
	    print rv.data
	    raise AssertionError

        print "Test with different user"
        self.signUp(username="jun.hang.lee@sap.com",
		    password="IWantToExitw/SAPLabsKoreaFucking!!!",
		    nickname="CiceronUser",
		    mother_language="Korean")
	self.login(username="jun.hang.lee@sap.com",
		    password="IWantToExitw/SAPLabsKoreaFucking!!!"
		    )

	print "Try to pick again"
	rv = self.app.get('/pick_request/1')
	try:
	    assert "According to your language" in rv.data
	except:
	    print rv.data
	    raise AssertionError

        rv = self.app.get('/post_list')
	print rv.data

    def test_comment(self):
	print "================test-comment=============="
	print "1. Post SOS request"
        self.signUp(username="psy2848048@gmail.com",
		    password="ciceron!",
		    nickname="CiceronMaster",
		    mother_language="Korean")
	self.login(username="psy2848048@gmail.com",
		    password="ciceron!"
		    )

	rv = self.app.post('/post', data=dict(
			from_lang="Korean",
			to_lang="English",
			is_SOS=1,
			main_text="English is too difficult to learn and use properly. I really need your help",
			format="Formal",
			subject="Announcement",
			price=0
			))

	rv = self.app.get('/post_list')
	print rv.data
        print ""
	print "2. Sign up another user and pick request"
        self.signUp(username="jun.hang.lee@sap.com",
		    password="IWantToExitw/SAPLabsKoreaFucking!!!",
		    nickname="CiceronUser",
		    mother_language="Korean")
	self.login(username="jun.hang.lee@sap.com",
		    password="IWantToExitw/SAPLabsKoreaFucking!!!"
		    )

	print "3. Add English as another language ability"
	rv = self.app.post('/add_language', data=dict(language="English"))
	try:
	    assert "added for user" in rv.data
	except:
	    print rv.data
	    raise AssertionError

        print "4. pick request"
	rv = self.app.get('/pick_request/1')
	try:
	    assert "is picked by" in rv.data
	except:
	    print rv.data
	    raise AssertionError

        rv = self.app.get('/post_list')
	print rv.data

        print "5. Print comment"
	rv = self.app.get('/comment/1')
	print rv.data

	print "6. Add comment"
	rv = self.app.post('/comment/1', data=dict(comment_text="BlahBlah", is_result=0))
	try:
	    assert "is posted in post" in rv.data
	except:
	    print rv.data
	    raise AssertionError

	rv = self.app.get('/comment/1')
	print rv.data

	print "7. Comment from requester"
	self.login(username="psy2848048@gmail.com",
		    password="ciceron!"
		    )
	rv = self.app.post('/comment/1', data=dict(comment_text="It's not enough answer. Could you please check it again?", is_result=0))
	try:
	    assert "is posted in post" in rv.data
	except:
	    print rv.data
	    raise AssertionError

	rv = self.app.get('/comment/1')
	print rv.data

	print ""
	print "8. Post another comment"
	self.login(username="jun.hang.lee@sap.com",
		    password="IWantToExitw/SAPLabsKoreaFucking!!!"
		    )
	rv = self.app.post('/comment/1', data=dict(comment_text="Shut da fuck up", is_result=0))

	rv = self.app.get('/comment/1')
	print rv.data
        print ""
	print "9. Accept translator's result and close the request"
	self.login(username="psy2848048@gmail.com",
		    password="ciceron!"
		    )
	rv = self.app.get('/accept/1', data=dict(comment_text="It's not enough answer. Could you please check it again?", is_result=0))
	print rv.data

    def test_paid_request(self):
	print "================test-paid-request=============="
	print "1. Post SOS request"
        self.signUp(username="psy2848048@gmail.com",
		    password="ciceron!",
		    nickname="CiceronMaster",
		    mother_language="Korean")
	self.login(username="psy2848048@gmail.com",
		    password="ciceron!"
		    )
        print "2. Charge USD 100"
	rv = self.app.post('/charge', data=dict(
		                                username="psy2848048@gmail.com", 
		                                password="ciceron!",
						point=100
						)
			  )

	rv = self.app.post('/post', data=dict(
			from_lang="Korean",
			to_lang="English",
			is_SOS=0,
			main_text="English is too difficult to learn and use properly. I really need your help",
			format="Formal",
			subject="Announcement",
			price=20.3
			))
        print rv.data
	rv = self.app.get('/post_list')
	print rv.data
        print ""
	print "3. Sign up another user and pick request"
        self.signUp(username="jun.hang.lee@sap.com",
		    password="IWantToExitw/SAPLabsKoreaFucking!!!",
		    nickname="CiceronUser",
		    mother_language="Korean")
	self.login(username="jun.hang.lee@sap.com",
		    password="IWantToExitw/SAPLabsKoreaFucking!!!"
		    )

	print "4. Add English as another language ability"
	rv = self.app.post('/add_language', data=dict(language="English"))
	try:
	    assert "added for user" in rv.data
	except:
	    print rv.data
	    raise AssertionError

        print "5. pick request"
	rv = self.app.get('/pick_request/1')
	try:
	    assert "is picked by" in rv.data
	except:
	    print rv.data
	    raise AssertionError

        rv = self.app.get('/post_list')
	print rv.data

        print "6. Print comment"
	rv = self.app.get('/comment/1')
	print rv.data

	print "7. Add comment"
	rv = self.app.post('/comment/1', data=dict(comment_text="BlahBlah", is_result=0))
	try:
	    assert "is posted in post" in rv.data
	except:
	    print rv.data
	    raise AssertionError

	rv = self.app.get('/comment/1')
	print rv.data

	print "8. Comment from requester"
	self.login(username="psy2848048@gmail.com",
		    password="ciceron!"
		    )
	rv = self.app.post('/comment/1', data=dict(comment_text="It's not enough answer. Could you please check it again?", is_result=0))
	try:
	    assert "is posted in post" in rv.data
	except:
	    print rv.data
	    raise AssertionError

	rv = self.app.get('/comment/1')
	print rv.data

	print ""
	print "9. Post another comment"
	self.login(username="jun.hang.lee@sap.com",
		    password="IWantToExitw/SAPLabsKoreaFucking!!!"
		    )
	rv = self.app.post('/comment/1', data=dict(comment_text="Shut da fuck up", is_result=0))

	rv = self.app.get('/comment/1')
	print rv.data
        print ""
	print "10. Accept translator's result and close the request"
	self.login(username="psy2848048@gmail.com",
		    password="ciceron!"
		    )
	rv = self.app.get('/accept/1')
	print rv.data

	rv = self.app.get('/history_requester')
	print rv.data

if __name__ == "__main__":
    unittest.main()
