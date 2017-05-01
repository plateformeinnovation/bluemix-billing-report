import logging

from flask_table import Col, create_table

from bx_report.DBLoader import DBLoader
from bx_report.utils.singleton import singleton


@singleton
class TableFactory(object):
    def __init__(self, host, port, dbname, user, password):

        self.logger = logging.getLogger(__name__)

        self.logger.debug('initializing BluemixTable.')

        self.regions = ['uk', 'us', 'au', 'de']

        self.client = DBLoader(
            host, port, user, password, dbname, 'public',
            'billing', 'authentication')

    def table_detail(self, organization, date):
        row_list = list()
        sum_cost = 0
        for region in self.regions:
            rows_for_region = self.__detail_rows(region, organization, date)
            for row in rows_for_region:
                sum_cost += row['cost']
            row_list.extend(rows_for_region)
        row_list.append(dict(region='', space='', category='', unit='', usage='', cost=sum_cost))

        if sum_cost == 0:
            return None

        BillingTable = create_table('BillingTable') \
            .add_column('region', Col('region')) \
            .add_column('space', Col('space')) \
            .add_column('category', Col('category')) \
            .add_column('unit', Col('unit')) \
            .add_column('usage', Col('usage')) \
            .add_column('cost', Col('cost (EUR)'))

        table = BillingTable(row_list)
        table.classes = ['responstable']

        return table.__html__()

    def __detail_rows(self, region, organization, date_str):
        '''
        generate rows (list of dict) to insert into table
        :param region:
        :param organization:
        :param date_str: in format like '2017-01' or 'history' for all
        :return: a list of dict like
        [{'category': 'cloudantNoSQLDB', 'cost': 0.34, 'space': 'dev', 'usage': 255.0, 'organization': 'CDO', 'region': 'uk', 'unit': u'HOUR'}, {'category': 'applications', 'cost': 25.14, 'space': 'dev', 'usage': 477.87, 'organization': 'CDO', 'region': 'uk', 'unit': u'GB-HOURS'}]
        '''
        return self.client.cost_detail_by_space_category(region, organization, date_str)

    def table_space(self, organization, date_str):
        row_list = list()
        sum_cost = 0
        for region in self.regions:
            rows_for_region = self.__space_rows(region, organization, date_str)
            for row in rows_for_region:
                sum_cost += row['cost']
            row_list.extend(rows_for_region)
        row_list.append(dict(region='', space='', cost=sum_cost))

        if sum_cost == 0:
            return None

        BillingTable = create_table('SummaryTable') \
            .add_column('region', Col('region')) \
            .add_column('space', Col('space')) \
            .add_column('cost', Col('cost (EUR)'))

        table = BillingTable(row_list)
        table.classes = ['responstable']

        return table.__html__()

    def __space_rows(self, region, organization, date_str):
        return self.client.cost_by_space(region, organization, date_str)

    def table_category(self, organization, date_str):
        row_list = list()
        sum_cost = 0
        for region in self.regions:
            rows_for_region = self.__category_rows(region, organization, date_str)
            for row in rows_for_region:
                sum_cost += row['cost']
            row_list.extend(rows_for_region)
        row_list.append(dict(region='', category='', cost=sum_cost))

        if sum_cost == 0:
            return None

        BillingTable = create_table('SummaryTable') \
            .add_column('region', Col('region')) \
            .add_column('category', Col('category')) \
            .add_column('cost', Col('cost (EUR)'))

        table = BillingTable(row_list)
        table.classes = ['responstable']

        return table.__html__()

    def __category_rows(self, region, organization, date_str):
        return self.client.cost_by_category(region, organization, date_str)

    def admin_table(self, items):
        row_list = list()
        organizations = self.client.get_all_organizations()
        organizations = map(lambda x: x[0], organizations)
        for item in items:
            login = '<form method="post">\n' + item[0] + \
                    '<input type="hidden" name="delete" value="%s">' % item[0] + \
                    '<br>\n<button type="submit">Delete</button>\n' + \
                    '</form>\n' + \
                    '<form method="post">\n' + \
                    '<input type="hidden" name="login" value="%s">' % item[0] + \
                    '<br>\n<input type="password" name="modify">' + \
                    '<br>\n<button type="submit">Reset password</button>\n' + \
                    '</form>\n'
            row = dict(login=login,
                       spaces=self.__gen_checkbox_form(item[0], item[1], organizations))
            row_list.append(row)

        row_dict = dict()
        row_dict['login'] = '''
            <form method="post">
            Username:
            <input type="text" name="username" value=""><br>
            Password:
            <input type="password" name="password" value=""><br>
            <input type="checkbox" name="su" value="">Super user<br>
            '''
        row_dict['spaces'] = self.__gen_checkbox_form(None, [], organizations)

        row_list.append(row_dict)


        class EscapedCol(Col):
            def td_format(self, content):
                return content


        AdminTable = create_table() \
            .add_column('login', EscapedCol('login')) \
            .add_column('spaces', EscapedCol('spaces'))

        table = AdminTable(row_list)
        table.classes = ['responstable']

        return table.__html__()

    def __gen_checkbox(self, name, value, checked=False):
        if checked:
            checkbox = '''
                <input type="checkbox" name="%s" value="%s" checked="checked"> %s<br>
                ''' % (name, value, name)
        else:
            checkbox = '''
                <input type="checkbox" name="%s" value="%s"> %s<br>
                ''' % (name, value, name)
        return checkbox

    def __gen_checkbox_form(self, user, user_org, all_org):
        if user:
            checkbox_form = str('<form method="post">\n')
            checkbox_form += '<input type="hidden" name="%s">\n' % user
        else:
            checkbox_form = str()

        for org in all_org:
            checkbox_form += self.__gen_checkbox(org, user, checked=True) \
                if (org in user_org) and user else self.__gen_checkbox(org, user)
        checkbox_form += '<input type="submit" value="%s">\n' % ('Submit' if user else 'Add')
        checkbox_form += '</form>\n'
        return checkbox_form
