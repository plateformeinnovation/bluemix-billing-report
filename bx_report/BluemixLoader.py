import json
import logging
import os
import subprocess
import sys
from datetime import date

import psycopg2


class BluemixLoader(object):
    def __init__(self, db_host, db_port, db_user, db_password, db_name,
                 bx_login, bx_pw, schema, billing_table,
                 api_uk="https://api.eu-gb.bluemix.net",
                 api_us="https://api.ng.bluemix.net",
                 api_au="https://api.au-syd.bluemix.net",
                 beginning_date=None):

        self.logger = logging.getLogger(__name__)

        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.schema = schema
        self.billing_table = billing_table

        self.bx_login = bx_login
        self.bx_password = bx_pw

        self.api_uk = api_uk
        self.api_us = api_us
        self.api_au = api_au

        self.beginning_date = beginning_date if beginning_date else date(2016, 1, 1)

        self.connected_region = None
        self.loaded_region = list()

        self.CREATE_TABLE_STATEMENT = """
            CREATE TABLE IF NOT EXISTS %s.%s(
                region character varying NOT NULL,
                organization character varying NOT NULL,
                space character varying NOT NULL,
                date character varying NOT NULL,
                applications json,
                containers json,
                services json,
                CONSTRAINT billing_pkey PRIMARY KEY (region, organization, space, date)
            );""" % (self.schema, self.billing_table)

        try:
            self.conn = psycopg2.connect(
                host=self.db_host, port=self.db_port, database=db_name,
                user=self.db_user, password=self.db_password)
            self.logger.debug('Database {} connected.'.format(db_name))
            self.cursor = self.conn.cursor()
            self.cursor.execute(self.CREATE_TABLE_STATEMENT)
            self.conn.commit()
            self.logger.debug('Table {}.{} created.'.format(self.schema, self.billing_table))
        except psycopg2.OperationalError:
            print >> sys.stderr, "database connection error."

    def last_month_date(self):
        today = date.today()
        year, month = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
        return date(year, month, 1)

    def load_all_region(self, starting_date):

        self.__CFLogin('uk')
        self.logger.debug('Connected to uk')
        self.__load_current_region(starting_date)
        self.__CFLogin('us')
        self.logger.debug('Connected to us')
        self.__load_current_region(starting_date)
        self.__CFLogin('au')
        self.logger.debug('Connected to au')
        self.__load_current_region(starting_date)

        self.conn.commit()
        self.conn.close()

    def __CFLogin(self, region, organization="moodpeek", space="dev"):
        if region == "uk":
            region = self.api_uk
            self.connected_region = "uk"
        elif region == "us":
            region = self.api_us
            self.connected_region = "us"
        elif region == "au":
            region = self.api_au
            self.connected_region = "au"
        else:
            raise ValueError("api should be: uk, us, or au.")
            sys.exit(1)
        command_cf = 'cf login -a {} -u {} -p {} -o {} -s {}'.format(
            region, self.bx_login, self.bx_password, organization, space)
        os.system(command_cf)

    def __load_current_region(self, beginning_date):
        '''
        load billing info to database for an organization of a region
        :param region:
        :param org:
        :param space:
        :param beginning_date:
        :return:
        '''
        if (self.connected_region not in self.loaded_region):

            report_date = date.today()

            while (report_date >= beginning_date):
                report_date_str = self.__format_date(report_date)
                org_list = self.__get_organization_list(report_date_str)
                for org in org_list:
                    bill_records = self.__retrieve_records(org, report_date_str)
                    if bill_records:
                        for record in bill_records:
                            if self.__check_exist(record["region"], org, record["space"], record["date"]):
                                if report_date.year == date.today().year and report_date.month == date.today().month:
                                    self.__update_record(record["region"], org, record["space"], record["date"],
                                                         json.dumps(record["applications"]),
                                                         json.dumps(record["containers"]),
                                                         json.dumps(record["services"]))
                                else:
                                    break
                            else:
                                self.__insert_record(record["region"], org, record["space"], record["date"],
                                                     json.dumps(record["applications"]),
                                                     json.dumps(record["containers"]),
                                                     json.dumps(record["services"]))
                report_date = self.__month_prev(report_date)
            self.loaded_region.append(self.connected_region)
            self.logger.info('Region {} loaded.'.format(self.connected_region))
        else:
            self.logger.info('Region {} already loaded, loading skipped.'.format(self.connected_region))

    def __get_organization_list(self, report_date):
        command_summary = "bx bss orgs-usage-summary -d %s --json" % (report_date)
        self.logger.debug('Getting organization list for {}'.format(report_date))
        childProcess = subprocess.Popen(command_summary, shell=True, stdout=subprocess.PIPE)
        out, err = childProcess.communicate()
        returnCode = childProcess.poll()
        if returnCode == 0:
            json_str = out
        while returnCode != 0:
            self.logger.debug('Getting organization list again for {}'.format(report_date))
            childProcess = subprocess.Popen(command_summary, shell=True, stdout=subprocess.PIPE)
            out, err = childProcess.communicate()
            returnCode = childProcess.poll()
            if returnCode == 0:
                json_str = out
        json_data = json.loads(json_str)
        org_list = list()
        if json_data["organizations"]:
            for org in json_data["organizations"]:
                org_list.append(org["name"])
        return org_list

    def __retrieve_records(self, org, report_date):
        command_org = "bluemix bss org-usage %s --json -d %s" % (org, report_date)
        self.logger.debug('Loading organization {} for {}'.format(org, report_date))
        childProcess = subprocess.Popen(command_org, shell=True, stdout=subprocess.PIPE)
        out, err = childProcess.communicate()
        returnCode = childProcess.poll()
        count = 0
        if returnCode == 0:
            json_str = out
        while returnCode != 0:
            count += 1
            if count == 5:
                return None
            self.logger.debug('Loading organization again {} for {}'.format(org, report_date))
            childProcess = subprocess.Popen(command_org, shell=True, stdout=subprocess.PIPE)
            out, err = childProcess.communicate()
            returnCode = childProcess.poll()
            if returnCode == 0:
                json_str = out
        json_data = json.loads(json_str)
        spaces_list_raw = json_data[0]["billable_usage"]["spaces"]
        if not spaces_list_raw:
            return None
        region = json_data[0]["region"]
        space_bill_list = list()
        for space in spaces_list_raw:
            space_bill = dict()
            space_bill["date"] = report_date
            space_bill["region"] = region
            space_bill["space"] = space["name"]
            space_bill["applications"] = self.__sum_application(space["applications"])
            space_bill["containers"] = self.__sum_container(space["containers"])
            space_bill["services"] = self.__sum_service(space["services"])
            space_bill_list.append(space_bill)
        return space_bill_list

    def __check_exist(self, region, org, space, date):
        SELECT_STATEMENT = """
            SELECT * FROM %s.%s
            WHERE region = '%s' AND organization = '%s' AND space = '%s' AND date = '%s';
            """ % (self.schema, self.billing_table, region, org, space, date)
        self.cursor.execute(SELECT_STATEMENT)
        if len(self.cursor.fetchall()) > 0:
            return True
        else:
            return False

    def __update_record(self, region, org, space, date, applications, containers, services):
        UPDATE_STATEMENT = """
            UPDATE %s.%s
            SET applications='%s', containers='%s', services='%s'
            WHERE region = '%s' AND organization = '%s' AND space = '%s' AND date = '%s';
            """ % (self.schema, self.billing_table, applications,
                   containers, services, region, org, space, date)
        self.cursor.execute(UPDATE_STATEMENT)

    def __insert_record(self, region, org, space, date, applications, containers, services):
        INSERT_STATEMENT = """
            INSERT INTO %s.%s
            (region, organization, space, date, applications, containers, services)
            VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s');
            """ % (self.schema, self.billing_table,
                   region, org, space, date, applications, containers, services)
        self.cursor.execute(INSERT_STATEMENT)

    def __format_date(self, current_date):
        return str(current_date.year) + "-" + (
            ("0" + str(current_date.month)) if current_date.month < 10 else str(current_date.month))

    def __month_prev(self, current_date):
        day = current_date.day
        month = current_date.month - 1 if current_date.month != 1 else 12
        year = current_date.year if current_date.month != 1 else current_date.year - 1
        return date(year, month, day)

    def __sum_application(self, list_application):
        if len(list_application) != 0:
            sum_cost = self.__sum_usage(list_application, "cost")
            sum_quantity = self.__sum_usage(list_application, "quantity")
            unit = list_application[0]["usage"][0]["unit"]
            return {"cost": sum_cost, "quantity": sum_quantity, "unit": unit}
        else:
            return {"cost": 0, "quantity": 0, "unit": None}

    def __sum_container(self, list_container):
        if len(list_container) != 0:
            sum_cost = 0
            sum_quantity = 0
            for element in list_container:
                sum_cost += self.__sum_usage(element["instances"], "cost")
                sum_quantity += self.__sum_usage(element["instances"], "quantity")
            try:
                unit = list_container[0]["instances"][0]["usage"][0]["unit"]
            except IndexError:
                return {"cost": 0, "quantity": 0, "unit": None}
            return {"cost": sum_cost, "quantity": sum_quantity, "unit": unit}
        else:
            return {"cost": 0, "quantity": 0, "unit": None}

    def __sum_service(self, list_service):
        if len(list_service) != 0:
            billing_dict = {}
            for service in list_service:
                name = service["name"]
                sum_cost = self.__sum_usage(service["instances"], "cost")
                sum_quantity = self.__sum_usage(service["instances"], "quantity")
                unit = list_service[0]["instances"][0]["usage"][0]["unit"]
                billing_dict[name] = {"cost": sum_cost, "quantity": sum_quantity, "unit": unit}
            return billing_dict
        else:
            return None

    def __sum_usage(self, list_usage, aspect):
        '''
        sum up "cost" or "quantity" of applications or instances
        :param list_usage: applications list or instances list
        :param aspect: "cost" or "quantity"
        :return:
        '''
        sum = 0
        for element in list_usage:
            for usage in element["usage"]:
                sum += usage[aspect]
        return sum
