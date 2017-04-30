from bx_report.BXTable import BXTable
from bx_report.utils.read_vcap import retrieve_vcap


def get_table(VCAP):
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_vcap(VCAP)
    return BXTable(DBHost, DBPort, DBName, DBUser, DBPassword)
