import re

import flask
import flask_login

from bx_report import app, VCAP, last_update_time, lock
from bx_report.DIfactory.get_table import get_table
from bx_report.utils.Utilsdate import Utilsdate
from bx_report.views import UserSession


def __report_summary(su, date_str):
    cost_sum = 0
    tables_space = '\n<h2 class="round">Consumption by organization/space</h2>\n'
    tables_category = '\n<h2 class="round">Consumption by organization/category</h2>\n'
    for organization in UserSession.get_organizations():
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
    with lock:
        update_time_content = 'Information updating...' if last_update_time.value == 'Updating' else 'Last updated: ' + last_update_time.value
        update_time = '\n<h4 align="right">' + update_time_content + '</h4>'
    head_cost_sum = '\n<h2 class="round color_cost_sum margin_total">Total consumption: {}</h2>\n'.format(cost_sum)
    return flask.render_template('report.html', content=update_time + head_cost_sum + tables_space + tables_category, su=su,
                                 summary=True, current_date=date_str)


@app.route('/summary/<date_str>')
@flask_login.login_required
def summary(date_str):
    if date_str == 'history':
        return __report_summary(flask_login.current_user.getSu(), 'history')
    current_date = UserSession.get_current_date()
    if date_str == 'previous':
        current_date = Utilsdate.previous_month_str(current_date)
        UserSession.set_current_date(current_date)
    if date_str == 'next':
        current_date = Utilsdate.next_month_str(current_date)
        UserSession.set_current_date(current_date)
    return __report_summary(flask_login.current_user.getSu(), current_date)
