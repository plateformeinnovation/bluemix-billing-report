from VCAP import retrieve_VCAP
from bx_report.src.BXLoader import BXLoader


def get_loader(VCAP, bx_login, bx_pw):
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_VCAP(VCAP)
    loader = BXLoader(DBHost, DBPort, DBUser, DBPassword,
                      DBName, bx_login, bx_pw)
    return loader
