import sys
import logging

import psycopg2


class BluemixClient(object):
    # This is a static variable (bound with class)
    instanceCount = 0

    def __init__(self, dbhost, dbport, dbname, dbuser, dbpassword,
                 dbschema='public', billingTable='billing',
                 authTable='authentication'):

        self.logger = logging.getLogger(__name__)

        self.dbschema = dbschema
        self.billingTable = billingTable
        self.authTable = authTable

        try:
            self.conn = psycopg2.connect(
                host=dbhost, port=dbport, database=dbname,
                user=dbuser, password=dbpassword)
            self.logger.debug('Database {} connected.'.format(dbname))
            self.cursor = self.conn.cursor()
        except psycopg2.OperationalError:
            print >> sys.stderr, "database connection error."

    def __del__(self):
        BluemixClient.instanceCount -= 1
        self.conn.close()

    def __select(self, column, schema, table, distinct=False, **kwargs):
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

    def date_str(self, current_date):
        return str(current_date.year) + "-" + (
            ("0" + str(current_date.month))
            if current_date.month < 10 else str(current_date.month))

    def __get_records(self, region, org, *args):
        '''
        Get records in database for region, organization, [space], [date]
        :param region:
        :param org:
        :param args:
        :return:
        '''
        if len(args) > 2 or len(args) == 0:
            raise ValueError("arguments number error.")

        if region == "uk":
            region = "eu-gb"
        if region == "us":
            region = "us-south"
        if region == "au":
            region = "au-syd"

        if "history" in args:
            if len(args) == 1:
                SELECT_STATEMENT = self.__select(
                    '*', self.dbschema, self.billingTable, region=region,
                    organization=org)
            else:
                space = args[0]
                SELECT_STATEMENT = self.__select(
                    '*', self.dbschema, self.billingTable, region=region,
                    space=space, organization=org)
        else:
            if len(args) == 1:
                date = args[0]
                SELECT_STATEMENT = self.__select(
                    '*', self.dbschema, self.billingTable, region=region,
                    organization=org, date=date)
            else:
                space = args[0]
                date = args[1]
                SELECT_STATEMENT = self.__select(
                    '*', self.dbschema, self.billingTable, region=region,
                    space=space, organization=org, date=date)

        self.cursor.execute(SELECT_STATEMENT)
        return self.cursor.fetchall()

    def get_all_organizations(self):
        SELECT_STATEMENT = self.__select(
            'organization', self.dbschema, self.billingTable, distinct=True)
        self.cursor.execute(SELECT_STATEMENT)
        return self.cursor.fetchall()

    def get_spaces(self, region, org, date):
        '''
        get all spaces of the region, organization
        :param region:
        :param org:
        :param date: in format like '2017-01' or 'history' for all
        :return: a list of spaces like [('preprod',), ('prod',),
        ('_openup',), ('devops',), ('dev',)]
        '''

        if region == "uk":
            region = "eu-gb"
        if region == "us":
            region = "us-south"
        if region == "au":
            region = "au-syd"

        LIST_SPACES = self.__select(
            'space', self.dbschema, self.billingTable, distinct=True,
            region=region, organization=org, date=date)

        self.cursor.execute(LIST_SPACES)

        return self.cursor.fetchall()

    def space_cost(self, region, org, space, date_str):
        '''
        get total cost(all categories) of a region, organization, space
        :param region:
        :param org:
        :param space:
        :param date_str:
        :return:
        '''
        sum = 0
        records = self.__get_records(region, org, space, date_str)
        if date_str == "history":
            for record in records:
                for element in record:
                    if isinstance(element, dict):
                        if "cost" in element:
                            sum += element["cost"]
                        else:
                            for sub_element in element.values():
                                sum += sub_element["cost"]
            return sum
        else:
            if len(records) > 1:
                raise Exception("database storage exception.")
            for element in records[0]:
                if isinstance(element, dict):
                    if "cost" in element:
                        sum += element["cost"]
                    else:
                        for sub_element in element.values():
                            sum += sub_element["cost"]
            return sum

    def category_cost(self, region, org, category, date_str):
        '''
        get total cost(all spaces) of a region, organization, category
        :param region:
        :param org:
        :param category: 'applications' or 'containers' or 'services'
        :param date_str:
        :return: a dict like {'applications': 2548.6307544397228} or
        {'containers': 2260.3634617700973} or
        {'cloudantNoSQLDB': 0.7902999999999999, 'Object-Storage': 0}
        '''
        res_dict = dict()
        records = self.__get_records(region, org, date_str)
        if category == "applications":
            res_dict["applications"] = 0
            for element in records:
                if element[4]:
                    res_dict["applications"] += element[4]["cost"]
        if category == "containers":
            res_dict["containers"] = 0
            for element in records:
                if element[5]:
                    res_dict["containers"] += element[5]["cost"]
        if category == "services":
            for element in records:
                if element[6]:
                    for item in element[6]:
                        if item in res_dict:
                            res_dict[str(item)] += element[6][item]["cost"]
                        else:
                            res_dict[str(item)] = element[6][item]["cost"]
        return res_dict

    def category_cost_detail(self, region, org, space, date):
        '''
        for a region, organization, space, the detailed cost of
        applications, containers, or each services if the cost of them is not 0
        :param region:
        :param org:
        :param space:
        :param date:
        :return: a dict like
        {'cloudantNoSQLDB': {u'cost': 0.7902999999999999, u'unit': u'GIGABYTE_OUTBOUND', u'quantity': 835},
        'applications': {u'cost': 4.3730325, u'unit': None, u'quantity': 83.1375}}
        '''
        res_dict = dict()
        records = self.__get_records(region, org, space, date)

        if date == "history":
            for record in records:
                if "applications" not in res_dict:
                    res_dict['applications'] = record[4]
                else:
                    res_dict['applications']['cost'] += record[4]['cost']
                    res_dict['applications']['quantity'] += record[4]['quantity']
                    if record[4]['unit']:
                        res_dict['applications']['unit'] = record[4]['unit']
                if 'containers' not in res_dict:
                    res_dict['containers'] = record[5]
                else:
                    res_dict['containers']['cost'] += record[5]['cost']
                    res_dict['containers']['quantity'] += record[5]['quantity']
                    if record[5]['unit']:
                        res_dict['containers']['unit'] = record[5]['unit']
                if record[6]:
                    for service in record[6]:
                        if service not in res_dict:
                            res_dict[str(service)] = record[6][service]
                        else:
                            res_dict[str(service)]['cost'] += record[6][service]['cost']
                            res_dict[str(service)]['quantity'] += record[6][service]['quantity']
                            if record[6][service]['unit']:
                                res_dict[str(service)]['unit'] = record[6][service]['unit']
            res_dict_non_zero = dict()
            for key in res_dict:
                if res_dict[key]['cost'] != 0:
                    res_dict_non_zero[key] = res_dict[key]
            return res_dict_non_zero
        else:
            if len(records) > 1:
                raise Exception("database storage exception.")
            if records[0][4]['cost'] != 0:
                res_dict['applications'] = records[0][4]
            if records[0][5]['cost'] != 0:
                res_dict['containers'] = records[0][5]
            if records[0][6]:
                for service in records[0][6]:
                    if records[0][6][service]['cost'] != 0:
                        res_dict[service] = records[0][6][service]
            return res_dict

    def get_auth_info(self, login, password):
        SELECT_STATEMENT = self.__select(
            'su, orgs', self.dbschema, self.authTable,
            login=login, password=password)
        self.cursor.execute(SELECT_STATEMENT)
        return self.cursor.fetchall()

    def get_su(self, login):
        SELECT_STATEMENT = self.__select(
            'su', self.dbschema, self.authTable, login=login)
        self.cursor.execute(SELECT_STATEMENT)
        return self.cursor.fetchall()

    def list_all_users(self):
        SELECT_STATEMENT = self.__select(
            'login, orgs', self.dbschema, self.authTable, su='false')
        self.cursor.execute(SELECT_STATEMENT)
        return self.cursor.fetchall()

    def update_user_orgs(self, user, orgs):
        orgs_str = str()
        for org in orgs:
            orgs_str += '"' + org + '",'
        orgs_str = orgs_str[:-1]
        UPDATE_STATEMENT = '''
            UPDATE %s.%s SET orgs='{%s}' WHERE login='%s'
            ''' % (self.dbschema, self.authTable, orgs_str, user)
        self.cursor.execute(UPDATE_STATEMENT)
        self.conn.commit()

    def delete_user(self, user):
        DELETE_STATEMENT = '''
            DELETE FROM %s.%s WHERE login='%s'
            ''' % (self.dbschema, self.authTable, user)
        self.cursor.execute(DELETE_STATEMENT)
        self.conn.commit()

    def insert_user(self, user, password, su, orgs):
        su = 'true' if su else 'false'
        orgs_str = str()
        for org in orgs:
            orgs_str += '"' + org + '",'
        orgs_str = '{' + orgs_str[:-1] + '}'
        INSERT_STATEMENT = '''
            INSERT INTO {schema}.{table} (login, password, su, orgs)
            SELECT '{login}', '{password}', '{su}', '{orgs}'
            WHERE NOT EXISTS (
                SELECT * FROM {schema}.{table}
                WHERE login='{login}'
            ); '''.format(schema=self.dbschema, table=self.authTable, login=user,
                          password=password, su=su, orgs=orgs_str)
        self.cursor.execute(INSERT_STATEMENT)
        self.conn.commit()
