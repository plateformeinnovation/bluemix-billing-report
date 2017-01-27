import re

from src import flask, app, VCAP
from src.factory.get_table import get_table
from src.views import flask_login, GlobalV

from src.utils.Utilsdate import Utilsdate


def __report(su, date_str):
    cost_sum = 0
    if date_str == 'history':
        flag = 'history'
    else:
        flag = 'rt'
    tables = '\n<h2 class="round">Consumption by organization/space/category</h2>\n'
    for organization in GlobalV.get_organizations():
        table = get_table(VCAP).table_detail(organization, date_str)
        if table:
            cost_list = re.findall(r'[0-9]+.[0-9]+', str(table))
            cost_sum += float(cost_list[len(cost_list) - 1])
            tables += '\n<h3>' + organization + '</h3>\n'
            tables += table
    head_cost_sum = '\n<h2 class="round color_cost_sum">Total consumption: {}</h2>\n'.format(cost_sum)
    return flask.render_template('report.html', content=head_cost_sum + tables,
                                 su=su, flag=flag, current_date=date_str)


@app.route('/report_user_rt/<date_str>')
@flask_login.login_required
def report_user_rt(date_str):
    current_date = GlobalV.get_current_date()
    if date_str == 'previous':
        current_date = Utilsdate.previous_month_str(current_date)
        GlobalV.set_current_date(current_date)
    if date_str == 'next':
        current_date = Utilsdate.next_month_str(current_date)
        GlobalV.set_current_date(current_date)

    return __report(flask_login.current_user.getSu(), current_date)


@app.route('/report_user_history')
@flask_login.login_required
def report_user_history():
    return __report(flask_login.current_user.getSu(), 'history')
