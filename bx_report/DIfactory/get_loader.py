from bx_report.BluemixRetriever import BluemixRetriever
from bx_report.utils.read_vcap import retrieve_vcap


def get_loader(VCAP, bx_login, bx_pw):
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_vcap(VCAP)
    return BluemixRetriever(DBHost, DBPort, DBUser, DBPassword, DBName, bx_login, bx_pw)
