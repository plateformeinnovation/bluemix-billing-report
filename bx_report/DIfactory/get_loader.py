from VCAP import retrieve_VCAP
from bx_report.BXLoader import BXLoader


def get_loader(VCAP, bx_login, bx_pw):
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_VCAP(VCAP)
    return BXLoader(DBHost, DBPort, DBUser, DBPassword, DBName, bx_login, bx_pw)
