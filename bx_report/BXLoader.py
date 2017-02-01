import json
import sys
from datetime import date

from bx_report import bx_login, bx_pw
from bx_report.database import DBConnection, InterfaceBillingMod
from bx_report.utils.BXTool import BXTool
from bx_report.utils.Utilsdate import Utilsdate


class BXLoader(DBConnection, InterfaceBillingMod):
    # bound with class, like static variable in Java
    BEGINNING_DATE = date(2016, 1, 1)

    def __init__(self, host, port, user, password, dbname,
                 bx_login, bx_pw, schema='public', billing_table='billing',
                 auth_table='authentication', beginning_date=None):

        # call correspond __init__ method by mro (Method Resolution Order)
        super(BXLoader, self).__init__(host, port, user, password, dbname,
                                       schema, billing_table, auth_table)

        self.beginning_date = beginning_date if beginning_date \
            else BXLoader.BEGINNING_DATE

        self.loaded_region = list()

        self.CREATE_BILLING_TABLE_STATEMENT = """
            CREATE TABLE IF NOT EXISTS %s.%s(
                region character varying NOT NULL,
                organization character varying NOT NULL,
                space character varying NOT NULL,
                date character varying NOT NULL,
                applications json,
                containers json,
                services json,
                CONSTRAINT billing_pkey PRIMARY KEY (region, organization, space, date)
            );""" % (self.schema, self.billing_table)

        self.CREATE_AUTH_TABLE_STATEMENT = '''
            CREATE TABLE IF NOT EXISTS %s.%s(
                login character varying NOT NULL,
                password character varying,
                su boolean,
                orgs text[],
                CONSTRAINT authentication_pkey PRIMARY KEY (login)
            );''' % (self.schema, self.auth_table)

        self.bx_tool = BXTool(bx_login, bx_pw)

        try:
            self._create_billing_table()
            self._create_auth_table()
            self.__insert_admin()
        except:
            print >> sys.stderr, "BXLoader init error."

    # inherits __del__ of superclass

    def load_all_region(self, starting_date):

        self.logger.info('start loading billing information from bx...')
        self.bx_tool.CFLogin('uk')
        self.__load_current_region(starting_date)
        self.bx_tool.CFLogin('us')
        self.__load_current_region(starting_date)
        self.bx_tool.CFLogin('au')
        self.__load_current_region(starting_date)

        self.conn.commit()
        self.logger.info('loading finished.')

    def __load_current_region(self, beginning_date):
        '''
        load billing info to DIfactory for an organization of a region
        :param region:
        :param org:
        :param space:
        :param beginning_date:
        :return:
        '''
        if (self.bx_tool.connected_region and
                (self.bx_tool.connected_region not in self.loaded_region)):
            self.logger.info('loading {}...'.format(self.bx_tool.connected_region))

            report_date = date.today()

            while (report_date >= beginning_date):
                report_date_str = Utilsdate.stringnize_date(report_date)
                org_list = self.bx_tool.get_orgs_list_by_date(report_date_str)
                for org in org_list:
                    bill_records = self.bx_tool.retrieve_records(org, report_date_str)
                    if bill_records:
                        for record in bill_records:
                            if self._check_existence(record["region"], org, record["space"], record["date"]):
                                if report_date.year == date.today().year and report_date.month == date.today().month:
                                    self._update_record(record["region"], org, record["space"], record["date"],
                                                        json.dumps(record["applications"]),
                                                        json.dumps(record["containers"]),
                                                        json.dumps(record["services"]))
                                else:
                                    break
                            else:
                                self._insert_record(record["region"], org, record["space"], record["date"],
                                                    json.dumps(record["applications"]),
                                                    json.dumps(record["containers"]),
                                                    json.dumps(record["services"]))
                report_date = Utilsdate.previous_month_date(report_date)
            self.loaded_region.append(self.bx_tool.connected_region)
            self.logger.info('Region {} loaded.'.format(self.bx_tool.connected_region))
        else:
            self.logger.info('Region {} already loaded, loading skipped.'.format(self.bx_tool.connected_region))

    def _create_billing_table(self):
        self.cursor.execute(self.CREATE_BILLING_TABLE_STATEMENT)
        self.conn.commit()
        self.logger.debug('Table {}.{} created.'.format(self.schema, self.billing_table))

    def _create_auth_table(self):
        self.cursor.execute(self.CREATE_AUTH_TABLE_STATEMENT)
        self.conn.commit()
        self.logger.debug('Table {}.{} created.'.format(self.schema, self.auth_table))

    def __insert_admin(self):
        self._insert_user(bx_login, bx_pw, True, self.bx_tool.get_orgs_list_all())
        self.logger.debug('User admin added.')

    def _insert_user(self, user, password, su, orgs):
        su = 'true' if su else 'false'
        orgs_str = str()
        for org in orgs:
            orgs_str += '"' + org + '",'
        orgs_str = '{' + orgs_str[:-1] + '}'
        if su == 'true':
            INSERT_STATEMENT = '''
                INSERT INTO {schema}.{table} (login, password, su, orgs)
                SELECT '{login}', '{password}', '{su}', orgs
                FROM {schema}.{table}
                WHERE login='admin'
                ON CONFLICT (login) DO UPDATE SET
                login=EXCLUDED.login, password=EXCLUDED.password,
                su=EXCLUDED.su, orgs=EXCLUDED.orgs;
                '''.format(schema=self.schema, table=self.auth_table, login=user,
                              password=password, su=su, orgs=orgs_str)
        else:
            INSERT_STATEMENT = '''
                INSERT INTO {schema}.{table} (login, password, su, orgs)
                SELECT '{login}', '{password}', '{su}', '{orgs}'
                WHERE NOT EXISTS (
                    SELECT * FROM {schema}.{table} WHERE login='{login}' );
                    '''.format(schema=self.schema, table=self.auth_table,
                               login=user, password=password, su=su, orgs=orgs_str)
        self.cursor.execute(INSERT_STATEMENT)
        self.conn.commit()

    def _check_existence(self, region, org, space, date):
        SELECT_STATEMENT = self._select(
            '*', self.schema, self.billing_table, region=region,
            organization=org, space=space, date=date)
        self.cursor.execute(SELECT_STATEMENT)
        if self.cursor.fetchone():
            return True
        else:
            return False

    def _update_record(self, region, org, space, date, applications, containers, services):
        UPDATE_STATEMENT = """
            UPDATE %s.%s
            SET applications='%s', containers='%s', services='%s'
            WHERE region = '%s' AND organization = '%s' AND space = '%s' AND date = '%s';
            """ % (self.schema, self.billing_table, applications,
                   containers, services, region, org, space, date)
        try:
            self.cursor.execute(UPDATE_STATEMENT)
        except:
            self.logger.debug('EXCEPTION in update.')
        self.conn.commit()

    def _insert_record(self, region, org, space, date, applications, containers, services):
        INSERT_STATEMENT = """
            INSERT INTO %s.%s
            (region, organization, space, date, applications, containers, services)
            VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s');
            """ % (self.schema, self.billing_table,
                   region, org, space, date, applications, containers, services)
        self.cursor.execute(INSERT_STATEMENT)
        self.conn.commit()
