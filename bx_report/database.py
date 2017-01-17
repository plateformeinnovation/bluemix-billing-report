import logging
import os
import re

import flask

from core.BluemixLoader import BluemixLoader
from core.BluemixTable import BluemixTable


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ENV_BX_LOGIN = 'BX_LOGIN'
ENV_BX_PW = 'BX_PASSWORD'
ENV_BX_SLEEP = 'BX_SLEEP'
VCAP = 'VCAP_SERVICES_COMPOSE_FOR_POSTGRESQL_0_CREDENTIALS_URI'

DEV = True

if DEV:
    with open('resource/ENV_VARIABLE', 'r') as f:
        bx_login = f.readline().strip()
        bx_pw = f.readline().strip()
        sleep_time = f.readline().strip()
else:
    bx_login = os.environ[ENV_BX_LOGIN]
    bx_pw = os.environ[ENV_BX_PW]
    sleep_time = os.environ[ENV_BX_SLEEP]


def retrieve_VCAP():
    VCAP_VALUE = os.environ[VCAP]
    INFO = re.split(r'://|:|@|/', VCAP_VALUE)
    DBUser = INFO[1]
    DBPassword = INFO[2]
    DBHost = INFO[3]
    DBPort = INFO[4]
    DBName = INFO[5]
    return (DBUser, DBPassword, DBHost, DBPort, DBName)


def get_table():
    table = getattr(flask.g, 'table', None)
    if table is None:
        DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_VCAP()

        # create BluemixTable object
        flask.g.table = BluemixTable(DBHost, DBPort, DBName, DBUser, DBPassword)

        logger.debug('PostgreSQL login: ' + DBUser)
        logger.debug('PostgreSQL password: ' + DBPassword)
        logger.debug('PostgreSQL host: ' + DBHost)
        logger.debug('PostgreSQL port: ' + DBPort)
        logger.debug('PostgreSQL database: ' + DBName)
    return flask.g.table


def get_loader():
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_VCAP()
    loader = BluemixLoader(DBHost, DBPort, DBUser, DBPassword,
                           DBName, bx_login, bx_pw)
    return loader
