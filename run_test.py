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

	rv = self.app.post('/post', data=dict(
			from_lang="Korean",
			to_lang="English",
			is_SOS=0,
			main_text="English is too difficult to learn and use properly. I really need your help",
			format="Formal",
			subject="Announcement",
			price=0.50
			))
	print rv.data
	assert "Posted" in rv.data

	rv = self.app.post('/post', data=dict(
			from_lang="Korean",
			to_lang="English",
			is_SOS=1,
			main_text="English is too difficult to learn and use properly. I really need your help",
			format="Thesis",
			subject="Scholar",
			price=0.50
			))
	print rv.data
	assert "Posted" in rv.data

        rv = self.app.get('/post_list')
	print "Posted list"
	print rv.data

        rv = self.app.get('/post_list?last_post_time=%f' % time.time())
	print "Posted list with last_post_time"
	print rv.data

        rv = self.app.get('/history')
        print "History of psy2848048@gmail.com"
	print rv.data

        rv = self.app.get('/history?last_post_time=%f' % time.time())
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

        rv = self.app.get('/history')
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
	print rv.data
	assert "Posted" in rv.data

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
	print rv.data
	assert "Posted" in rv.data

        print "Try to pickl"
	rv = self.app.get('/pick_request/1')
	print rv.data
	assert "You cannot translate"

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
	print rv.data
	assert "Post 1 is picked" in rv.data

        rv = self.app.get('/post_list')
	print rv.data

if __name__ == "__main__":
    unittest.main()
