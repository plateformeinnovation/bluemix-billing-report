from VCAP import retrieve_VCAP
from src.BXTable import BXTable


def get_table(VCAP):
    DBUser, DBPassword, DBHost, DBPort, DBName = retrieve_VCAP(VCAP)
    return BXTable(DBHost, DBPort, DBName, DBUser, DBPassword)
