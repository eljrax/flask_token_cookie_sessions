import json
import time
import pylibmc
from uuid import uuid4
from werkzeug.datastructures import CallbackDict
from werkzeug.exceptions import BadRequest
from flask.sessions import SessionInterface, SessionMixin
from hashlib import md5


class ExampleSession(CallbackDict, SessionMixin):

    def __init__(self, initial=None, sid=None, new=False, needs_cookie=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False
        self.destroy = False
        self.needs_cookie = needs_cookie

    def delete(self):
        self.destroy = True


class ExampleSessionInterface(SessionInterface):
    serializer = json
    session_class = ExampleSession

    def __init__(self, session_opts, datastore_client=None):
        self.session_opts = session_opts
        self.token_header = session_opts['token_header']
        self.prefix = self.session_opts.get('cache_key_prefix', 'session_')
        self.datastore_client = datastore_client

        if datastore_client is None:
            # This should be fairly straight forward to replace with another datastore.
            self.datastore_client = pylibmc.Client(session_opts['session.url'], binary=True)

    def generate_sid(self):
        return str(uuid4())

    def get_expiration_time(self, session):
        """ The session defaults to lasting 10 hours.
            You can optionally set a date manually in the session wherever you want, to a new
            expiry date using the 'valid_until' key.

            Return a timestamp for when the session (and therefore cookie) should expire
        """
        default_expiry = time.time() + int(self.session_opts.get('session.cookie_expires', 36000))
        valid_until = session.get('valid_until', None)
        return valid_until or default_expiry

    def needs_cookie(self, request):
        """ Determines whether we should send a cookie or not with our response, based on whether
            the request looks like an API request or not.

            We only send cookies to browsers - not API clients
        """

        needs_cookie = True

        try:
            if self.token_header in request.headers or 'token' in request.get_json():
                needs_cookie = False
        except Exception:
            pass

        return needs_cookie

    def get_session_id(self, request, app):
        """ We can get a session either through the user sending a cookie (the normal case when
            app is used in a browser, OR someone can be using the API functionality, in
            which case the rackertoken is the session identifier.
            If both are present, cookie wins so that requests' (or other libraries')
            sessions can be used.

            If this is the auth request for API, there's also a JSON body which may contain
            a token.
        """

        cookie = request.cookies.get(app.session_cookie_name)
        if cookie:
            return cookie

        try:
            return md5(request.headers[self.session_opts['token_header']]).hexdigest()
        except KeyError:
            pass

        try:
            # You may want to modify this, depending on how you want the JSON you'll accept
            # to look like. In this example, simply: { "token": "token_goes_here" } suffices.
            return md5(request.get_json()['token']).hexdigest()
        except (TypeError, KeyError, BadRequest):
            pass

        """ No session identifiers sent with the request - it's a new session """
        return None

    def open_session(self, app, request):
        sid = self.get_session_id(request, app)
        needs_cookie = self.needs_cookie(request)

        if not sid:
            """ New session never seen before """
            sid = self.generate_sid()
            return self.session_class(sid=sid, new=True, needs_cookie=needs_cookie)

        key = str(self.prefix + sid)
        val = None
        try:
            val = self.datastore_client.get(key)
        except Exception as ex:
            # Handle as you see fit
            print("MEMCACHED CLIENT GET ERROR: %s" % ex)

        if val is not None:
            data = self.serializer.loads(val)
            return self.session_class(data, sid=sid, needs_cookie=needs_cookie)

        return self.session_class(sid=sid, new=True, needs_cookie=needs_cookie)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        key = str(self.prefix + session.sid)

        if not session or session.destroy:
            try:
                self.datastore_client.delete(key)
            except Exception as ex:
                # Handle as you see fit
                print("MEMCACHED CLIENT DELETE ERROR: %s" % ex)

            if session.modified:
                response.delete_cookie(app.session_cookie_name, domain=domain)
            return

        expires = self.get_expiration_time(session)
        session_ttl = int(expires - time.time())
        if session_ttl <= 0:
            """ Token *just* expired """
            return

        val = self.serializer.dumps(dict(session))

        try:
            self.datastore_client.set(key, val, time=session_ttl)
        except Exception as ex:
            # Handle as you see fit
            print("MEMCACHED CLIENT WRITE ERROR: %s" % ex)

        if session.needs_cookie:
            response.set_cookie(app.session_cookie_name, session.sid,
                                expires=expires, httponly=True,
                                domain=domain)
