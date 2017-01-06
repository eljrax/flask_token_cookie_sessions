from flask import Flask
from flask import session
from session_example import sessions
import os
import uuid

app = Flask(__name__)
app.secret_key = 'not_so_secret'

datastore_uri = os.getenv('SESSION_EXAMPLE_DATASTORE_URI', '127.0.0.1:11211')
session_opts = {
    'session.url': [datastore_uri],
    'session.cookie_expires': 30,
    'session.timeout': 30,
    'cache_key_prefix': 'session_',
    'token_header': 'X-Auth-Token',
}

app.session_interface = sessions.ExampleSessionInterface(session_opts)


@app.before_request
def before_request():
    if 'identifier' not in session:
        print "Previously unseen session... Setting identifier"
        session['identifier'] = str(uuid.uuid4())


@app.route('/', methods=['GET', 'POST'])
def hello_world():
    return "The random identifier stored with your session is: %s" % session.get('identifier',
                                                                                 'Not set')
