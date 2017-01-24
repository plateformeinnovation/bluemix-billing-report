import logging
import sys

import psycopg2


class DBConnection(object):
    def __init__(self, host, port, user, password, dbname,
                 schema, billing_table, auth_table):
        self.logger = logging.getLogger(__name__)

        self.schema = schema
        self.billing_table = billing_table
        self.auth_table = auth_table

        try:
            self.conn = psycopg2.connect(
                host=host, port=port, database=dbname, user=user, password=password)
            self.cursor = self.conn.cursor()
            self.logger.debug('Database {} connected.'.format(dbname))
        except:
            print >> sys.stderr, 'factory connection error.'

    def __del__(self):
        self.conn.close()

    # protected method which can be inherited
    def _select(self, column, schema, table, distinct=False, **kwargs):
        '''
        Generate a select cluase
        :param column:
        :param schema:
        :param table:
        :param distinct:
        :param kwargs:
        :return:
        '''
        if distinct:
            SELECT_STATEMENT = """
                SELECT DISTINCT %s FROM %s.%s
                """ % (column, schema, table)
        else:
            SELECT_STATEMENT = """
                SELECT %s FROM %s.%s
                """ % (column, schema, table)
        if len(kwargs) > 0:
            SELECT_STATEMENT += " WHERE "
            for key, value in kwargs.items():
                if key == 'date' and value == 'history':
                    continue
                SELECT_STATEMENT += "%s = '%s' AND " % (key, value)
            SELECT_STATEMENT = SELECT_STATEMENT[:-5]
        return SELECT_STATEMENT
