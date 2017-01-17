import sys

import flask_login

from database import get_table


# User class inherits from flask_login.UserMixin
class User(flask_login.UserMixin):
    def __init__(self, su):
        self.su = su

    # super user or not
    def getSu(self):
        return self.su


login_manager = flask_login.LoginManager()
login_manager.login_view = 'login'


# reload user when necessary
@login_manager.user_loader
def user_loader(email):
    su = get_table().client.get_su(email)
    try:
        su = su[0][0]
    except IndexError:
        print >> sys.stderr, 'user {} information error'.format(email)
        return None
    user = User(su)
    user.id = email
    return user
