import flask

from . import retrieve_VCAP, logger
from ..BXTable import BluemixTable


def get_table():
    table = getattr(flask.g, 'table', None)
    if table is None:
        DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_VCAP()

        # create BluemixTable object
        flask.g.table_detail = BluemixTable(DBHost, DBPort, DBName, DBUser, DBPassword)

        logger.debug('PostgreSQL login: ' + DBUser)
        logger.debug('PostgreSQL password: ' + DBPassword)
        logger.debug('PostgreSQL host: ' + DBHost)
        logger.debug('PostgreSQL port: ' + DBPort)
        logger.debug('PostgreSQL factory: ' + DBName)
    return flask.g.table_detail
