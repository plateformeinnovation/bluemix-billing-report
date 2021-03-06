import smtplib
from datetime import date
from email.mime.text import MIMEText

import flask
import flask_login

from bx_report import app, VCAP, mail_sender, mail_sender_pw, bx_login
from bx_report.factory.get_table_render import get_table_render
from bx_report.flask_user.user import user_loader
from bx_report.utils.Utilsdate import Utilsdate
from bx_report.views import UserSession


# the route() decorator tells Flask what URL should trigger this function
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return flask.render_template('login.html')

    if flask.request.method == 'POST':

        email = flask.request.form['email']
        password = flask.request.form['pw']
        auth_info = get_table_render(VCAP).client._authenticate(email, password)

        if auth_info:  # successfully authenticated
            UserSession.set_current_date(Utilsdate.stringnize_date(date.today()))
            UserSession.set_organizations(auth_info[1])
            if not auth_info[0]:  # normal user
                user = user_loader(email)
                flask_login.login_user(user)  # login created user
                return flask.redirect(flask.url_for(
                    'details', date_str='current'))
            else:  # super user
                user = user_loader(email)
                flask_login.login_user(user)
                return flask.redirect(flask.url_for(
                    'summary', date_str='current'))

        return 'Bad login'


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('login'))


@app.route('/forgotten', methods=['GET', 'POST'])
def forgotten():
    if flask.request.method == 'GET':
        return flask.render_template('forgotten.html')

    if flask.request.method == 'POST':
        receiver = [bx_login]
        user = flask.request.form['email'].strip()
        msg = MIMEText('Please reset password for {}.'.format(user))
        msg['Subject'] = 'OPEN Bluemix reporting platform - Password reset demand.'
        msg['From'] = mail_sender
        msg['To'] = receiver[0]
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(mail_sender, mail_sender_pw)
        server.sendmail(mail_sender, receiver, msg.as_string())
        server.quit()
        return flask.redirect(flask.url_for('login'))
