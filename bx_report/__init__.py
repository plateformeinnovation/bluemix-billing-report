# coding:utf-8

import logging
from datetime import date

import flask
import flask_login

from core.BluemixTable import BluemixTable
from database import get_table
from user import User, login_manager, user_loader


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
        auth_info = get_table().client.get_auth_info(email, password)

        if auth_info:  # successfully authenticated
            global current_date
            global organizations
            current_date = get_table().client.date_str(date.today())
            organizations = auth_info[0][1]
            if not auth_info[0][0]:  # normal user
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
    tables = ''
    for organization in organizations:
        tables += '\n<h3>' + organization + '</h3>\n'
        tables += get_table().table(organization, date_str)
    return flask.render_template('report.html', content=tables,
                                 su=su, flag=flag, current_date=date_str)


def last_month(date_str):
    year = int(date_str.split('-')[0])
    month = int(date_str.split('-')[1])
    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1
    return str(year) + ('-0' if month < 10 else '-') + str(month)


def next_month(date_str):
    if date_str == get_table().client.date_str(date.today()):
        return date_str
    year = int(date_str.split('-')[0])
    month = int(date_str.split('-')[1])
    if month == 12:
        year += 1
        month = 1
    else:
        month += 1
    return str(year) + ('-0' if month < 10 else '-') + str(month)


@app.route('/report_user_rt/<date_str>')
@flask_login.login_required
def report_user_rt(date_str):
    global current_date
    if date_str == 'previous':
        current_date = last_month(current_date)
    if date_str == 'next':
        current_date = next_month(current_date)

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
    tables_space = '\n<h2 class="round">Consumption by spaces</h2>\n'
    tables_category = '\n<h2 class="round">Consumption by categories</h2>\n'
    for organization in organizations:
        tables_space += '\n<h3>' + organization + '</h3>\n'
        tables_space += get_table().table_space_sum(organization, date_str)
        tables_category += '\n<h3>' + organization + '</h3>\n'
        tables_category += get_table().table_category_sum(organization, date_str)
    return flask.render_template('report.html', content=tables_space + tables_category, su=su,
                                 flag=flag, summary=summary, current_date=date_str)


@app.route('/report_admin_summary_rt/<date_str>')
@flask_login.login_required
def report_admin_summary_rt(date_str):
    global current_date
    if date_str == 'previous':
        current_date = last_month(current_date)
    if date_str == 'next':
        current_date = next_month(current_date)
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
            get_table().client.delete_user(user_to_delete)
            return flask.redirect(flask.url_for('admin'))
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
                get_table().client.insert_user(username, password, su, orgs)
        else:
            for item in dict_post:
                if '@' in item:
                    user = item
            orgs = dict_post.keys()
            orgs.remove(user)
            get_table().client.update_user_orgs(user, orgs)
            return flask.redirect(flask.url_for('admin'))

    items = get_table().client.list_all_users()
    items = sorted(items, key=lambda x: x[0])
    # if len(items) == 0:
    #     raise ValueError('no users in database.')
    table = get_table().admin_table(items)
    return flask.render_template('admin.html', content=table)


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('login'))
