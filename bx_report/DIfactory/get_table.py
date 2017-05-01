from bx_report.TableFactory import TableFactory
from bx_report.utils.read_vcap import retrieve_vcap


def get_table(VCAP):
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_vcap(VCAP)
    return TableFactory(DBHost, DBPort, DBName, DBUser, DBPassword)
