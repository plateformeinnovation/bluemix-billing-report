from bx_report.BXLoader import BXLoader
from bx_report.utils.read_vcap import retrieve_vcap


def get_loader(VCAP, bx_login, bx_pw):
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_vcap(VCAP)
    return BXLoader(DBHost, DBPort, DBUser, DBPassword, DBName, bx_login, bx_pw)
