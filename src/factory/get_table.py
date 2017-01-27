import logging

from VCAP import retrieve_VCAP
from src import flask
from src.BXTable import BXTable


def get_table(VCAP):
    logger = logging.getLogger(__name__)

    table = getattr(flask.g, 'table', None)

    if table is None:
        DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_VCAP(VCAP)

        # create BluemixTable object
        flask.g.table_detail = BXTable(
            DBHost, DBPort, DBName, DBUser, DBPassword)

        logger.debug('PostgreSQL login: ' + DBUser)
        logger.debug('PostgreSQL password: ' + DBPassword)
        logger.debug('PostgreSQL host: ' + DBHost)
        logger.debug('PostgreSQL port: ' + DBPort)
        logger.debug('PostgreSQL factory: ' + DBName)

    return flask.g.table_detail
