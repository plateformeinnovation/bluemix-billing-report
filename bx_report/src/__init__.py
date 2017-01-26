# coding:utf-8

import logging
import os
import sys

import flask


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ENV_BX_LOGIN = 'BX_LOGIN'
ENV_BX_PW = 'BX_PASSWORD'
ENV_BX_SLEEP = 'BX_SLEEP'
VCAP = 'VCAP_SERVICES_COMPOSE_FOR_POSTGRESQL_0_CREDENTIALS_URI'

DEV = False

if len(sys.argv) > 1:
    PORT = int(sys.argv[1])

if len(sys.argv) > 2 and sys.argv[2] == 'dev':
    DEV = True

if len(sys.argv) > 3 or len(sys.argv) == 1:
    print sys.stderr, 'run.py port [dev]'
    sys.exit(1)

if DEV:
    with open('bx_report/src/resource/ENV_VARIABLE', 'r') as f:
        bx_login = f.readline().strip()
        bx_pw = f.readline().strip()
        sleep_time = float(f.readline().strip())
else:
    bx_login = os.environ[ENV_BX_LOGIN]
    bx_pw = os.environ[ENV_BX_PW]
    sleep_time = float(os.environ[ENV_BX_SLEEP])

from bx_report.src.flask_user import login_manager, user_loader


# create a flask app
app = flask.Flask(__name__)
app.config.from_object('config')
app.secret_key = app.config['SECRET_KEY']

login_manager.init_app(app)

from bx_report.src.views import login
from bx_report.src.views import report_user
from bx_report.src.views import report_admin
from bx_report.src.views import admin
