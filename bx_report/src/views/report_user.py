from bx_report.src import flask, app, VCAP
from bx_report.src.factory.get_table import get_table
from bx_report.src.utils.Utilsdate import Utilsdate
from bx_report.src.views import flask_login, GlobalV


def __report(su, date_str):
    if date_str == 'history':
        flag = 'history'
    else:
        flag = 'rt'
    tables = '\n<h2 class="round">Consumption by organization/space/category</h2>\n'
    for organization in GlobalV.get_organizations():
        table = get_table(VCAP).table_detail(organization, date_str)
        if table:
            tables += '\n<h3>' + organization + '</h3>\n'
            tables += table
    return flask.render_template('report.html', content=tables,
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
