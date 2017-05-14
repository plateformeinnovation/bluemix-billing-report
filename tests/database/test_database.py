import unittest

import bx_report.db.DBConnection as db
import bx_report.utils.read_vcap as vcap

class TestDatabase(unittest.TestCase):
    def setUpClass(cls):
        VCAP = 'VCAP_SERVICES_COMPOSE_FOR_POSTGRESQL_0_CREDENTIALS_URI'
        DBUser, DBPassword, DBHost, DBPort, DBName = vcap.retrieve_vcap(VCAP)
        cls.conn = db.DBConnection(DBHost, DBPort, DBUser, DBPassword, DBName)

    def tearDownClass(cls):
        cls.conn.__del__()
