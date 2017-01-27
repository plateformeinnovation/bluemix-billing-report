import os
import re


def retrieve_VCAP(VCAP):
    VCAP_VALUE = os.environ[VCAP]
    INFO = re.split(r'://|:|@|/', VCAP_VALUE)
    DBUser = INFO[1]
    DBPassword = INFO[2]
    DBHost = INFO[3]
    DBPort = INFO[4]
    DBName = INFO[5]
    return (DBUser, DBPassword, DBHost, DBPort, DBName)
