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

if sys.argv[1].lower() == 'dev':
    DEV = True
else:
    DEV = False

if DEV:
    PORT = 5000
    with open('bx_report/src/resource/ENV_VARIABLE', 'r') as f:
        bx_login = f.readline().strip()
        bx_pw = f.readline().strip()
        sleep_time = float(f.readline().strip())
else:
    PORT = 80
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
