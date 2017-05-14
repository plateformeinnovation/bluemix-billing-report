from bx_report.TableRender import TableRender
from bx_report.utils.read_vcap import retrieve_vcap


def get_table_render(VCAP):
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_vcap(VCAP)
    return TableRender(DBHost, DBPort, DBName, DBUser, DBPassword)
