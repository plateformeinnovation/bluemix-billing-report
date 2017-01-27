from src.database import DBConnection, InterfaceAuth, InterfaceBilling


class BluemixClient(DBConnection, InterfaceAuth, InterfaceBilling):
    '''
    Python inherits constructor(__init__) and destructor(__del__) directly !!!
    Here we overwrite __init__
    '''

    def __get_records(self, region, org, *args):
        '''
        Get records in factory for region, organization, [space], [date]
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
                SELECT_STATEMENT = self._select(
                    '*', self.schema, self.billing_table, region=region,
                    organization=org)
            else:
                space = args[0]
                SELECT_STATEMENT = self._select(
                    '*', self.schema, self.billing_table, region=region,
                    space=space, organization=org)
        else:
            if len(args) == 1:
                date = args[0]
                SELECT_STATEMENT = self._select(
                    '*', self.schema, self.billing_table, region=region,
                    organization=org, date=date)
            else:
                space = args[0]
                date = args[1]
                SELECT_STATEMENT = self._select(
                    '*', self.schema, self.billing_table, region=region,
                    space=space, organization=org, date=date)

        self.cursor.execute(SELECT_STATEMENT)
        return self.cursor.fetchall()

    def __get_spaces(self, region, org, date_str):
        '''
        get all spaces of the region, organization
        :param region:
        :param org:
        :param date_str: in format like '2017-01' or 'history' for all
        :return: a list of spaces like [('preprod',), ('prod',),
        ('_openup',), ('devops',), ('dev',)]
        '''

        if region == "uk":
            region = "eu-gb"
        if region == "us":
            region = "us-south"
        if region == "au":
            region = "au-syd"

        LIST_SPACES = self._select(
            'space', self.schema, self.billing_table, distinct=True,
            region=region, organization=org, date=date_str)

        self.cursor.execute(LIST_SPACES)

        return self.cursor.fetchall()

    def __sum_cost_for_space(self, region, org, space, date_str):
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
                raise Exception("factory storage exception.")
            for element in records[0]:
                if isinstance(element, dict):
                    if "cost" in element:
                        sum += element["cost"]
                    else:
                        for sub_element in element.values():
                            sum += sub_element["cost"]
            return sum

    def __sum_cost_for_category(self, region, org, category, date_str):
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

    def __cost_detail_by_category(self, region, org, space, date_str):
        '''
        for a region, organization, space, the detailed cost of
        applications, containers, or each services if the cost of them is not 0
        :param region:
        :param org:
        :param space:
        :param date_str:
        :return: a dict like
        {'cloudantNoSQLDB': {u'cost': 0.79, u'unit': u'GIGABYTE_OUTBOUND', u'quantity': 835},
        'applications': {u'cost': 4.37, u'unit': None, u'quantity': 83.13}}
        '''
        res_dict = dict()
        records = self.__get_records(region, org, space, date_str)

        if date_str == "history":
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
                raise Exception("storage exception.")
            if records[0][4]['cost'] != 0:
                res_dict['applications'] = records[0][4]
            if records[0][5]['cost'] != 0:
                res_dict['containers'] = records[0][5]
            if records[0][6]:
                for service in records[0][6]:
                    if records[0][6][service]['cost'] != 0:
                        res_dict[service] = records[0][6][service]
            return res_dict

    def get_all_organizations(self):
        SELECT_STATEMENT = self._select(
            'organization', self.schema, self.billing_table, distinct=True)
        self.cursor.execute(SELECT_STATEMENT)
        return self.cursor.fetchall()

    def cost_by_space(self, region, org, date_str):
        space_list = self.__get_spaces(region, org, date_str)

        row_list = list()
        for space in space_list:
            space = space[0]
            row_dict = dict(region=region, space=space)
            row_dict['cost'] = round(self.__sum_cost_for_space(region, org, space, date_str), 2)
            if row_dict['cost'] > 0.01:
                row_list.append(row_dict)

        return row_list

    def cost_by_category(self, region, org, date_str):
        category_dict = dict()
        for category in ['applications', 'containers', 'services']:
            category_dict.update(self.__sum_cost_for_category(region, org, category, date_str))

        row_list = list()
        for category in category_dict:
            if category_dict[category] == 0:
                continue
            row_dict = dict(region=region, category=category)
            row_dict['cost'] = round(category_dict[category], 2)
            if row_dict['cost'] > 0.01:
                row_list.append(row_dict)

        return row_list

    def cost_detail_by_space_category(self, region, org, date_str):
        '''
        detailed consumption info of different spaces and categories
        for a region, organization, date
        :param region:
        :param org:
        :param date_str:
        :return: a list of dict like
        [{'category': 'cloudantNoSQLDB', 'cost': 0.34, 'space': 'dev', 'usage': 255.0, 'organization': 'CDO', 'region': 'uk', 'unit': u'HOUR'}, {'category': 'applications', 'cost': 25.14, 'space': 'dev', 'usage': 477.87, 'organization': 'CDO', 'region': 'uk', 'unit': u'GB-HOURS'}]
        '''
        space_list = self.__get_spaces(region, org, date_str)

        row_list = list()
        for space in space_list:
            space = space[0]
            space_cost_detail = self.__cost_detail_by_category(region, org, space, date_str)
            for category in space_cost_detail:
                if space_cost_detail[category]['cost'] < 0.1:
                    continue
                row_dict = dict(region=region, space=space, category=category,
                                unit=space_cost_detail[category]['unit'],
                                usage=round(space_cost_detail[category]['quantity'], 2),
                                cost=round(space_cost_detail[category]['cost'], 2))
                row_list.append(row_dict)

        return row_list

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
                AND NOT EXISTS (
                    SELECT * FROM {schema}.{table}
                    WHERE login='{login}'
                ); '''.format(schema=self.schema, table=self.auth_table, login=user,
                              password=password, su=su, orgs=orgs_str)
        else:
            INSERT_STATEMENT = '''
                INSERT INTO {schema}.{table} (login, password, su, orgs)
                SELECT '{login}', '{password}', '{su}', '{orgs}'
                WHERE NOT EXISTS (
                    SELECT * FROM {schema}.{table} WHERE login='{login}' ); '''.format(schema=self.schema,
                                                                                       table=self.auth_table,
                                                                                       login=user,
                                                                                       password=password, su=su,
                                                                                       orgs=orgs_str)
        self.cursor.execute(INSERT_STATEMENT)
        self.conn.commit()

    def _delete_user(self, user):
        DELETE_STATEMENT = '''
            DELETE FROM %s.%s WHERE login='%s'
            ''' % (self.schema, self.auth_table, user)
        self.cursor.execute(DELETE_STATEMENT)
        self.conn.commit()

    def _update_user_pw(self, user, pw):
        UPDATE_STATEMENT = '''
            UPDATE {}.{} SET password='{}' WHERE login='{}'
            '''.format(self.schema, self.auth_table, pw, user)
        self.cursor.execute(UPDATE_STATEMENT)
        self.conn.commit()

    def _update_user_orgs(self, user, orgs):
        orgs_str = str()
        for org in orgs:
            orgs_str += '"' + org + '",'
        orgs_str = orgs_str[:-1]
        UPDATE_STATEMENT = '''
            UPDATE %s.%s SET orgs='{%s}' WHERE login='%s'
            ''' % (self.schema, self.auth_table, orgs_str, user)
        self.cursor.execute(UPDATE_STATEMENT)
        self.conn.commit()

    def _authenticate(self, login, password):
        SELECT_STATEMENT = self._select(
            'su, orgs', self.schema, self.auth_table,
            login=login, password=password)
        self.cursor.execute(SELECT_STATEMENT)
        return self.cursor.fetchone()

    def _verify_su(self, login):
        SELECT_STATEMENT = self._select(
            'su', self.schema, self.auth_table, login=login)
        self.cursor.execute(SELECT_STATEMENT)
        return self.cursor.fetchall()

    def _list_all_users(self):
        SELECT_STATEMENT = self._select(
            'login, orgs', self.schema, self.auth_table)
        self.cursor.execute(SELECT_STATEMENT)
        return self.cursor.fetchall()
