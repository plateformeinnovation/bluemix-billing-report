import json
import sys
from datetime import date, datetime

from bx_report import bx_login, bx_pw
from bx_report.db import DBConnection, InterfaceBillingMod
from bx_report.utils.BluemixCli import BluemixCli, API_LIST
from bx_report.utils.Utilsdate import Utilsdate


class DBLoader(DBConnection, InterfaceBillingMod):
    # bound with class, like static variable in Java
    BEGINNING_DATE = date(2016, 1, 1)

    def __init__(self, host, port, user, password, dbname,
                 bx_login, bx_pw, schema='public', billing_table='billing',
                 auth_table='authentication', beginning_date=None):

        # call correspond __init__ method by mro (Method Resolution Order)
        super(DBLoader, self).__init__(host, port, user, password, dbname,
                                       schema, billing_table, auth_table)

        self.beginning_date = beginning_date if beginning_date \
            else DBLoader.BEGINNING_DATE

        self.region_loaded = list()

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

        self.bx_cli = BluemixCli(bx_login, bx_pw)

        try:
            self._create_billing_table()
            self._create_auth_table()
            self.__insert_update_admin()
            self._disconnect()
        except:
            print >> sys.stderr, "BXLoader init error."

    # inherits __del__ of superclass

    def load_all_region(self, beginning_date):
        self._connect()
        self.__insert_update_admin()
        self.logger.info('start loading billing information with bx from {}.'
                         .format(Utilsdate.stringnize_date(beginning_date)))

        for region_api in API_LIST:
            self.bx_cli.cf_login(region_api)
            self.__load_current_region(beginning_date)

        self._cleaning()

        self.conn.commit()
        self.logger.info('loading finished.')
        self.region_loaded = []
        self._disconnect()

        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def __load_current_region(self, beginning_date):
        '''
        load billing information from bx cli to PostgreSQL
        for current connected region
        :param beginning_date: starting date
        :return:
        '''
        if (self.bx_cli.connected_region and
                (self.bx_cli.connected_region not in self.region_loaded)):
            self.logger.info('loading {} from {}.'
                             .format(self.bx_cli.connected_region,
                                     Utilsdate.stringnize_date(beginning_date)))

            report_date = date.today()

            while (report_date >= beginning_date):
                report_date_str = Utilsdate.stringnize_date(report_date)
                org_list = self.bx_cli.get_orgs_list_by_date(report_date_str)
                for org in org_list:
                    bill_records = self.bx_cli.retrieve_records(org, report_date_str)
                    if bill_records:
                        for record in bill_records:
                            if self._check_existence(record["region"], org, record["space"], record["date"]):
                                self._update_record(record["region"], org, record["space"], record["date"],
                                                    json.dumps(record["applications"]),
                                                    json.dumps(record["containers"]),
                                                    json.dumps(record["services"]))
                            else:
                                self._insert_record(record["region"], org, record["space"], record["date"],
                                                    json.dumps(record["applications"]),
                                                    json.dumps(record["containers"]),
                                                    json.dumps(record["services"]))
                report_date = Utilsdate.previous_month_date(report_date)
            self.region_loaded.append(self.bx_cli.connected_region)
            self.logger.info('Region {} loaded.'.format(self.bx_cli.connected_region))
        else:
            self.logger.info('Region {} already loaded, loading skipped.'.format(self.bx_cli.connected_region))

    def _create_billing_table(self):
        self.cursor.execute(self.CREATE_BILLING_TABLE_STATEMENT)
        self.conn.commit()
        self.logger.debug('Table {}.{} created.'.format(self.schema, self.billing_table))

    def _create_auth_table(self):
        self.cursor.execute(self.CREATE_AUTH_TABLE_STATEMENT)
        self.conn.commit()
        self.logger.debug('Table {}.{} created.'.format(self.schema, self.auth_table))

    def __insert_update_admin(self):
        '''
        insert or update admin user with newest organization list
        :return:
        '''
        self._insert_user(bx_login, bx_pw, True, self.bx_cli.get_orgs_list_all())
        self.logger.debug('Admin user added.')

    def _insert_user(self, user, password, su, orgs):
        orgs_str = str()
        for org in orgs:
            orgs_str += '"' + org + '",'
        orgs_str = '{' + orgs_str[:-1] + '}'
        if su:
            INSERT_STATEMENT = '''
                INSERT INTO {schema}.{table} (login, password, su, orgs)
                SELECT '{login}', '{password}', '{su}', '{orgs}'
                FROM {schema}.{table}
                WHERE login='{login}'
                ON CONFLICT (login) DO UPDATE SET
                login=EXCLUDED.login, password=EXCLUDED.password,
                su=EXCLUDED.su, orgs=EXCLUDED.orgs;
                '''.format(schema=self.schema, table=self.auth_table, login=user,
                           password=password, su='true', orgs=orgs_str)
        else:
            INSERT_STATEMENT = '''
                INSERT INTO {schema}.{table} (login, password, su, orgs)
                SELECT '{login}', '{password}', '{su}', '{orgs}'
                WHERE NOT EXISTS (
                    SELECT * FROM {schema}.{table} WHERE login='{login}' );
                    '''.format(schema=self.schema, table=self.auth_table,
                               login=user, password=password, su='false', orgs=orgs_str)
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

    def _cleaning(self):
        CLEAN_STATEMENT = """
        delete from billing where space like '%-%-%-%-%'
        """
        self.cursor.execute(CLEAN_STATEMENT)
        self.conn.commit()
