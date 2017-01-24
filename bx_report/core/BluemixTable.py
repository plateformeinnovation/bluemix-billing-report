from .BluemixClient import BluemixClient
from flask_table import Col, create_table

import logging

class BluemixTable(object):
    def __init__(self, host, port, dbname, user, password):

        self.logger = logging.getLogger(__name__)

        self.logger.debug('initializing BluemixTable.')

        self.client = BluemixClient(host, port, dbname, user, password)

    def table(self, organization, date):
        row_list = list()
        sum_cost = 0
        for region in ['uk', 'us', 'au']:
            rows_for_region = self.__generate_rows(region, organization, date)
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

    def __generate_rows(self, region, organization, date):
        '''
        generate rows (list of dict) to insert into the table
        :param region:
        :param organization:
        :param date: in format like '2017-01' or 'history' for all
        :return: a list of dict like
        [{'category': 'cloudantNoSQLDB', 'cost': 0.34, 'space': 'dev', 'usage': 255.0, 'organization': 'CDO', 'region': 'uk', 'unit': u'HOUR'}, {'category': 'applications', 'cost': 25.14, 'space': 'dev', 'usage': 477.87, 'organization': 'CDO', 'region': 'uk', 'unit': u'GB-HOURS'}]
        '''
        space_list = self.client.get_spaces(region, organization, date)

        row_list = list()
        for space in space_list:
            space = space[0]
            category_cost_detail = self.client.category_cost_detail(region, organization, space, date)
            for category in category_cost_detail:
                if category_cost_detail[category]['cost'] < 0.1:
                    continue
                row_dict = dict(region=region, space=space, category=category,
                                unit=category_cost_detail[category]['unit'],
                                usage=round(category_cost_detail[category]['quantity'], 2),
                                cost=round(category_cost_detail[category]['cost'], 2))
                row_list.append(row_dict)

        return row_list

    def table_space_sum(self, organization, date_str):
        row_list = list()
        sum_cost = 0
        for region in ['uk', 'us', 'au']:
            rows_for_region = self.__generate_summary_space_rows(region, organization, date_str)
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

    def __generate_summary_space_rows(self, region, organization, date_str):
        space_list = self.client.get_spaces(region, organization, date_str)

        row_list = list()
        for space in space_list:
            space = space[0]
            row_dict = dict(region=region, space=space)
            row_dict['cost'] = round(self.client.space_cost(region, organization, space, date_str), 2)
            if row_dict['cost'] > 0.01:
                row_list.append(row_dict)

        return row_list

    def table_category_sum(self, organization, date_str):
        row_list = list()
        sum_cost = 0
        for region in ['uk', 'us', 'au']:
            rows_for_region = self.__generate_summary_category_rows(region, organization, date_str)
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

    def __generate_summary_category_rows(self, region, organization, date_str):
        category_dict = dict()
        for category in ['applications', 'containers', 'services']:
            category_dict.update(self.client.category_cost(region, organization, category, date_str))

        row_list = list()
        for category in category_dict:
            if category_dict[category] == 0:
                continue
            row_dict = dict(region=region, category=category)
            row_dict['cost'] = round(category_dict[category], 2)
            if row_dict['cost'] > 0.01:
                row_list.append(row_dict)

        return row_list

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
                    '<br>\n<input type="text" name="modify">' + \
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
            <input type="text" name="password" value=""><br>
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
