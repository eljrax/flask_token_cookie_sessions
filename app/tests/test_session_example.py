import json
import unittest
import session_example.app as app


class SessionExampleTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(SessionExampleTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.app_sess1 = app.app.test_client()
        self.app_sess2 = app.app.test_client()

    def test_new_session_no_cookie(self):
        """ Test that we get a new cookie if we send a new, bare request """

        with self.app_sess1 as c:
            ret = c.get('/')
            self.assertIn('Set-Cookie', ret.headers)

    def test_existing_session_cookie(self):
        """ Test that two requests in the same session has the same session data """

        with self.app_sess1 as c:
            ret1 = c.get('/')
            ret2 = c.get('/')
            self.assertEqual(ret1.data, ret2.data)

    def test_distinct_sessions_cookie(self):
        """ Test that two distinct requests are distinct sessions """

        sess1 = None
        sess2 = None
        with self.app_sess1 as c:
            sess1 = c.get('/').data

        with self.app_sess2 as c:
            sess2 = c.get('/').data

        self.assertNotEqual(sess1, sess2)

    def test_new_session_no_cookie_auth_token(self):
        """ Test that no cookie is sent back in the response when x-auth-token header is set """

        with self.app_sess1 as c:
            ret = c.get('/', headers={'X-Auth-Token': 'pretend_token'})
            self.assertNotIn('Set-Cookie', ret.headers)

    def test_new_session_created_with_auth_json_no_cookie(self):
        """ Test that no cookie is sent with the response if a new session is created with a "token"
            key present in a JSON request.
        """

        with self.app_sess1 as c:
            data = {
                "token": "pretend_token"
            }
            ret = c.post('/', data=json.dumps(data), headers={'Content-Type': 'application/json'})
            self.assertNotIn('Set-Cookie', ret.headers)

    def test_new_session_create_with_auth_json(self):
        """ Test that a new session is created when a "token" key is present in a JSON request
            body.
        """

        with self.app_sess1 as c:
            data = {
                "token": "pretend_token"
            }
            ret1 = c.post('/', data=json.dumps(data), headers={'Content-Type': 'application/json'})
            ret2 = c.get('/', headers={'X-Auth-Token': 'pretend_token'})

            self.assertEqual(ret1.data, ret2.data)

    def test_session_auth_token(self):
        """ Test that sending a token in x-auth-token creates a session """

        sess1 = None
        sess2 = None
        test_header = {'X-Auth-Token': 'pretend_token'}

        with self.app_sess1 as c:
            ret = c.get('/', headers=test_header)
            sess1 = ret.data

        with self.app_sess2 as c:
            ret = c.get('/', headers=test_header)
            sess2 = ret.data

        self.assertEqual(sess1, sess2)

    def test_distinct_sessions_auth_token(self):
        """ Test that two distinct auth tokens result in distinct sessions """

        sess1 = None
        sess2 = None

        with self.app_sess1 as c:
            ret = c.get('/', headers={'X-Auth-Token': 'pretend_token'})
            sess1 = ret.data

        with self.app_sess2 as c:
            ret = c.get('/', headers={'X-Auth-Token': 'another_pretend_token'})
            sess2 = ret.data

        self.assertNotEqual(sess1, sess2)

    def test_existing_session_auth_token(self):
        """ Test that two requests in the same session has the same session data (using token) """

        test_header = {'X-Auth-Token': 'pretend_token'}

        with self.app_sess1 as c:
            ret1 = c.get('/', headers=test_header)
            ret2 = c.get('/', headers=test_header)
            self.assertEqual(ret1.data, ret2.data)
