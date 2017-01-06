#!/usr/bin/env python
from __future__ import print_function
from session_example.app import app
import os
import sys

host = os.getenv('SESSION_EXAMPLE_HOST', '127.0.0.1')
try:
    port = int(os.getenv('SESSION_EXAMPLE_PORT', 5000))
except ValueError:
    print ("Port argument must be an integer")

try:
    app.run(debug=True, host=host, port=port)
except Exception as e:
    sys.stderr.write("%s\n" % repr(e))
