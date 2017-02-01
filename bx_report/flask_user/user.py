import sys

import flask_login


# This module is imported in run.py
assert sys.modules.has_key('bx_report')

# These modules are imported in bx_report/__init__.py
assert sys.modules.has_key('bx_report.flask_user')
assert sys.modules.has_key('bx_report.flask_user.user')

# since bx_report was already registered in sys.modules
# and VCAP has been executed. we can import it directly
# with not re-executing the whole module
from bx_report import VCAP
from bx_report.DIfactory.get_table import get_table


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
    su = get_table(VCAP).client._verify_su(email)
    try:
        su = su[0][0]
    except IndexError:
        print >> sys.stderr, 'user {} information error'.format(email)
        return None
    user = User(su)
    user.id = email
    return user
