from . import retrieve_VCAP, bx_login, bx_pw
from ..BXLoader import BXLoader


def get_loader():
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_VCAP()
    loader = BXLoader(DBHost, DBPort, DBUser, DBPassword,
                      DBName, bx_login, bx_pw)
    return loader
