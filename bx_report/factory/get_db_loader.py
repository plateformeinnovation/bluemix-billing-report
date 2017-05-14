from bx_report.db.DBLoader import DBLoader
from bx_report.utils.read_vcap import retrieve_vcap


def get_db_loader(VCAP, bx_login, bx_pw):
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_vcap(VCAP)
    return DBLoader(DBHost, DBPort, DBUser, DBPassword, DBName, bx_login, bx_pw)
