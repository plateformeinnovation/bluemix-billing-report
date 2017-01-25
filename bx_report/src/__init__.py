# coding:utf-8

import logging
from datetime import date

import flask
import flask_login

from factory.get_table import get_table
from flask_user import login_manager, user_loader
from utils.Utilsdate import Utilsdate


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# create a flask app
app = flask.Flask(__name__)
app.config.from_object('config')
app.secret_key = app.config['SECRET_KEY']

login_manager.init_app(app)


# the route() decorator tells Flask what URL should trigger this function
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return flask.render_template('login.html')

    if flask.request.method == 'POST':

        email = flask.request.form['email']
        password = flask.request.form['pw']
        auth_info = get_table().client._authenticate(email, password)

        if auth_info:  # successfully authenticated
            global current_date
            global organizations
            current_date = Utilsdate.stringnize_date(date.today())
            organizations = auth_info[1]
            if not auth_info[0]:  # normal user
                user = user_loader(email)
                flask_login.login_user(user)  # login created user
                return flask.redirect(flask.url_for(
                    'report_user_rt', date_str='current'))
            else:  # super user
                user = user_loader(email)
                flask_login.login_user(user)
                return flask.redirect(flask.url_for(
                    'report_admin_summary_rt', date_str='current'))

        return 'Bad login'


def __report(su, date_str):
    if date_str == 'history':
        flag = 'history'
    else:
        flag = 'rt'
    global organizations
    tables = '\n<h2 class="round">Consumption by organization/space/category</h2>\n'
    for organization in organizations:
        table = get_table().table_detail(organization, date_str)
        if table:
            tables += '\n<h3>' + organization + '</h3>\n'
            tables += table
    return flask.render_template('report.html', content=tables,
                                 su=su, flag=flag, current_date=date_str)


@app.route('/report_user_rt/<date_str>')
@flask_login.login_required
def report_user_rt(date_str):
    global current_date
    if date_str == 'previous':
        current_date = Utilsdate.previous_month_str(current_date)
    if date_str == 'next':
        current_date = Utilsdate.next_month_str(current_date)

    return __report(flask_login.current_user.getSu(), current_date)


@app.route('/report_user_history')
@flask_login.login_required
def report_user_history():
    return __report(flask_login.current_user.getSu(), 'history')


def __report_admin(su, date_str, summary):
    if date_str == 'history':
        flag = 'history'
    else:
        flag = 'rt'
    global organizations
    tables_space = '\n<h2 class="round">Consumption by organization/space</h2>\n'
    tables_category = '\n<h2 class="round">Consumption by organization/category</h2>\n'
    for organization in organizations:
        table_space = get_table().table_space(organization, date_str)
        table_category = get_table().table_category(organization, date_str)
        if table_space:
            tables_space += '\n<h3>' + organization + '</h3>\n'
            tables_space += table_space
        if table_category:
            tables_category += '\n<h3>' + organization + '</h3>\n'
            tables_category += table_category
    return flask.render_template('report.html', content=tables_space + tables_category, su=su,
                                 flag=flag, summary=summary, current_date=date_str)


@app.route('/report_admin_summary_rt/<date_str>')
@flask_login.login_required
def report_admin_summary_rt(date_str):
    global current_date
    if date_str == 'previous':
        current_date = Utilsdate.previous_month_str(current_date)
    if date_str == 'next':
        current_date = Utilsdate.next_month_str(current_date)
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


@app.route('/admin', methods=['GET', 'POST'])
@flask_login.login_required
def admin():
    if flask.request.method == 'POST':
        dict_post = flask.request.form.to_dict()
        if dict_post.has_key('delete'):
            user_to_delete = dict_post['delete']
            get_table().client._delete_user(user_to_delete)
            # return flask.redirect(flask.url_for('admin'))
        elif dict_post.has_key('modify'):
            username = dict_post['login']
            pw = dict_post['modify']
            get_table().client._update_user_pw(username, pw)
            # return flask.redirect(flask.url_for('admin'))
        elif dict_post.has_key('username'):
            username = dict_post['username']
            password = dict_post['password']
            su = True if dict_post.has_key('su') else False
            orgs = dict_post.keys()
            orgs.remove('username')
            orgs.remove('password')
            if su:
                orgs.remove('su')
            if username and password:
                get_table().client._insert_user(username, password, su, orgs)
        else:
            for item in dict_post:
                if '@' in item:
                    user = item
            orgs = dict_post.keys()
            orgs.remove(user)
            get_table().client._update_user_orgs(user, orgs)
            # return flask.redirect(flask.url_for('admin'))

    items = get_table().client._list_all_users()
    items = filter(lambda x: x[0] != 'admin', items)
    items = sorted(items, key=lambda x: x[0])
    table = get_table().admin_table(items)
    return flask.render_template('admin.html', content=table)


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('login'))
