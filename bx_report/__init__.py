# coding:utf-8

import logging
import multiprocessing
import os
import sys

import flask

logging.basicConfig(level=logging.INFO, filename='bx_report.log', format='%(asctime)s %(message)s')
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

ENV_BX_LOGIN = 'BX_LOGIN'
ENV_BX_PW = 'BX_PASSWORD'
ENV_BX_SLEEP = 'BX_SLEEP'
ENV_MAIL_SENDER = 'MAIL_SENDER'
ENV_MAIL_SENDER_PW = 'MAIL_SENDER_PW'
VCAP = 'VCAP_SERVICES_COMPOSE_FOR_POSTGRESQL_0_CREDENTIALS_URI'
FILE_LOGIN = 'bx_report/resource/ENV_VARIABLE'
FILE_TEST_LOGIN = 'resource/ENV_VARIABLE'

if len(sys.argv) != 3:
    print sys.stderr, 'run.py port flag'
    sys.exit(1)

PORT = int(sys.argv[1])
FLAG = sys.argv[2]

if FLAG != 'prod':
    logging.basicConfig(level=logging.DEBUG)

if FLAG == 'prod':
    bx_login = os.environ[ENV_BX_LOGIN]
    bx_pw = os.environ[ENV_BX_PW]
    sleep_time = float(os.environ[ENV_BX_SLEEP])
    mail_sender = os.environ[ENV_MAIL_SENDER]
    mail_sender_pw = os.environ[ENV_MAIL_SENDER_PW]
else:
    file_login = FILE_LOGIN if os.path.exists(FILE_LOGIN) else FILE_TEST_LOGIN
    with open(file_login) as f:
        bx_login = f.readline().strip()
        bx_pw = f.readline().strip()
        sleep_time = float(f.readline().strip())
        mail_sender = f.readline().strip()
        mail_sender_pw = f.readline().strip()


# create a flask app
app = flask.Flask(__name__)
app.config.from_object('config')
app.secret_key = app.config['SECRET_KEY']

# create a manager (another server process) to store our shared info
server = multiprocessing.Manager()

# shared memory on the server
last_update_time = server.Value(unicode, 'Updating')
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
from bx_report.views import details
from bx_report.views import summary
from bx_report.views import admin
