import logging
import os
import re
import sys

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


def retrieve_VCAP():
    VCAP_VALUE = os.environ[VCAP]
    INFO = re.split(r'://|:|@|/', VCAP_VALUE)
    DBUser = INFO[1]
    DBPassword = INFO[2]
    DBHost = INFO[3]
    DBPort = INFO[4]
    DBName = INFO[5]
    return (DBUser, DBPassword, DBHost, DBPort, DBName)
