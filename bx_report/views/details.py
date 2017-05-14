import re

import flask
import flask_login

from bx_report import app, VCAP, last_update_time, lock
from bx_report.factory.get_table_render import get_table_render
from bx_report.utils.Utilsdate import Utilsdate
from bx_report.views import UserSession


def __report_details(su, date_str):
    '''
    render report.html and return it
    :param su: super user or not (boolean)
    :param date_str: which month or history
    :return:
    '''
    cost_sum = 0
    tables = '\n<h2 class="round">Consumption by organization/space/category</h2>\n'
    for organization in UserSession.get_organizations():
        table = get_table_render(VCAP).table_detail(organization, date_str)
        if table:
            cost_list = re.findall(r'[0-9]+.[0-9]+', str(table))
            cost_sum += float(cost_list[len(cost_list) - 1])
            tables += '\n<h3>' + organization + '</h3>\n'
            tables += table
    with lock:
        update_time_content = 'Information updating...'\
            if last_update_time.value == 'Updating'\
            else 'Last updated: ' + last_update_time.value
        update_time = '\n<h4 align="right">' + update_time_content + '</h4>'
    head_cost_sum = '\n<h2 class="round color_cost_sum margin_total">Total consumption: {}</h2>\n'\
        .format(cost_sum)
    return flask.render_template('report.html', content=update_time + head_cost_sum + tables,
                                 su=su, current_date=date_str)


@app.route('/details/<date_str>')
@flask_login.login_required
def details(date_str):
    if date_str == 'history':
        return __report_details(flask_login.current_user.getSu(), 'history')

    current_date = UserSession.get_current_date()
    if date_str == 'previous':
        current_date = Utilsdate.previous_month_str(current_date)
        UserSession.set_current_date(current_date)
    if date_str == 'next':
        current_date = Utilsdate.next_month_str(current_date)
        UserSession.set_current_date(current_date)

    return __report_details(flask_login.current_user.getSu(), current_date)

