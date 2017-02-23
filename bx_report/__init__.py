# coding:utf-8

import logging
import multiprocessing
import ctypes
import os
import sys

import flask


logging.basicConfig(level=logging.INFO, filename='bx_report.log', format='%(asctime)s %(message)s')
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

ENV_BX_LOGIN = 'BX_LOGIN'
ENV_BX_PW = 'BX_PASSWORD'
ENV_BX_SLEEP = 'BX_SLEEP'
VCAP = 'VCAP_SERVICES_COMPOSE_FOR_POSTGRESQL_0_CREDENTIALS_URI'

DEV = False

if len(sys.argv) > 1:
    PORT = int(sys.argv[1])

if len(sys.argv) > 2 and sys.argv[2] == 'dev':
    DEV = True
    logging.basicConfig(level=logging.DEBUG)

if len(sys.argv) > 3 or len(sys.argv) == 1:
    print sys.stderr, 'run.py port [dev]'
    sys.exit(1)

if DEV:
    with open('bx_report/resource/ENV_VARIABLE', 'r') as f:
        bx_login = f.readline().strip()
        bx_pw = f.readline().strip()
        sleep_time = float(f.readline().strip())
else:
    bx_login = os.environ[ENV_BX_LOGIN]
    bx_pw = os.environ[ENV_BX_PW]
    sleep_time = float(os.environ[ENV_BX_SLEEP])

# create a flask app
app = flask.Flask(__name__)
app.config.from_object('config')
app.secret_key = app.config['SECRET_KEY']

last_update_time = multiprocessing.Value(ctypes.c_char_p, 'Updating')
lock = multiprocessing.Lock()

# Let the variable initialization finished, then we can use these variables
# in others modules by proper imports

# Register bx_report.flask_user, bx_report.flask_user.user
# in sys.modules, so we have these modules in sys.modules from now on.
#
# bx_report has already been registered in previous run.py file
from bx_report.flask_user.user import login_manager


login_manager.init_app(app)

from bx_report.views import login
from bx_report.views import report_user
from bx_report.views import report_admin
from bx_report.views import admin
