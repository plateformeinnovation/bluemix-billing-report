import re

import flask
import flask_login

from bx_report import app, VCAP
from bx_report.DIfactory.get_table import get_table
from bx_report.utils.Utilsdate import Utilsdate
from bx_report.views import GlobalV


def __report_admin(su, date_str, summary):
    cost_sum = 0
    if date_str == 'history':
        flag = 'history'
    else:
        flag = 'rt'
    tables_space = '\n<h2 class="round">Consumption by organization/space</h2>\n'
    tables_category = '\n<h2 class="round">Consumption by organization/category</h2>\n'
    for organization in GlobalV.get_organizations():
        table_space = get_table(VCAP).table_space(organization, date_str)
        table_category = get_table(VCAP).table_category(organization, date_str)
        if table_space:
            cost_list = re.findall(r'[0-9]+.[0-9]+', str(table_space))
            cost_sum += float(cost_list[len(cost_list) - 1])
            tables_space += '\n<h3>' + organization + '</h3>\n'
            tables_space += table_space
        if table_category:
            tables_category += '\n<h3>' + organization + '</h3>\n'
            tables_category += table_category
    head_cost_sum = '\n<h2 class="round color_cost_sum">Total consumption: {}</h2>\n'.format(cost_sum)
    return flask.render_template('report.html', content=head_cost_sum + tables_space + tables_category, su=su,
                                 flag=flag, summary=summary, current_date=date_str)


@app.route('/report_admin_summary_rt/<date_str>')
@flask_login.login_required
def report_admin_summary_rt(date_str):
    current_date = GlobalV.get_current_date()
    if date_str == 'previous':
        current_date = Utilsdate.previous_month_str(current_date)
        GlobalV.set_current_date(current_date)
    if date_str == 'next':
        current_date = Utilsdate.next_month_str(current_date)
        GlobalV.set_current_date(current_date)
    return __report_admin(flask_login.current_user.getSu(), current_date, True)


@app.route('/report_admin_summary_history')
@flask_login.login_required
def report_admin_summary_history():
    return __report_admin(flask_login.current_user.getSu(), 'history', True)


@app.route('/report_admin_rt')
@flask_login.login_required
def report_admin_rt():
    return __report_admin(flask_login.current_user.getSu(), 'rt', False)


@app.route('/report_admin_history')
@flask_login.login_required
def report_admin_history():
    return __report_admin(flask_login.current_user.getSu(), 'history', False)
