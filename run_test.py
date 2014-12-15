import os, run, unittest, tempfile
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

if __name__ == "__main__":
    unittest.main()
