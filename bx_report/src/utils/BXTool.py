import json
import logging
import os
import subprocess

from singleton import singleton


@singleton
class BXTool(object):
    def __init__(self, bx_login, bx_pw,
                 api_uk="https://api.eu-gb.bluemix.net",
                 api_us="https://api.ng.bluemix.net",
                 api_au="https://api.au-syd.bluemix.net"):

        self.logger = logging.getLogger(__name__)

        self.bx_login = bx_login
        self.bx_password = bx_pw

        self.api_uk = api_uk
        self.api_us = api_us
        self.api_au = api_au

        self.connected_region = None

        self.all_orgs = None

    def CFLogin(self, region, organization="moodpeek", space="dev"):
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

    def get_orgs_list_all(self):
        if self.all_orgs is None:
            organizations = []
            self.CFLogin('uk')
            organizations.extend(self.__get_orgs_list_current_region())
            self.CFLogin('us')
            organizations.extend(self.__get_orgs_list_current_region())
            self.CFLogin('au')
            organizations.extend(self.__get_orgs_list_current_region())
            self.all_orgs = list(set(organizations))
            self.logger.debug('all organizations: ' + str(self.all_orgs))
        return self.all_orgs

    def __get_orgs_list_current_region(self):

        command_summary = "cf orgs"
        childProcess = subprocess.Popen(command_summary, shell=True, stdout=subprocess.PIPE)
        out, err = childProcess.communicate()
        returnCode = childProcess.poll()
        while returnCode != 0:
            childProcess = subprocess.Popen(command_summary, shell=True, stdout=subprocess.PIPE)
            out, err = childProcess.communicate()
            returnCode = childProcess.poll()
        org_list = out.split('\n')[3:-1]

        return org_list

    def get_orgs_list_by_date(self, report_date):

        command_summary = "bx bss orgs-usage-summary -d %s --json" % (report_date)
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

        self.logger.debug('organization list {}: {}'.format(report_date, org_list))
        return org_list

    def retrieve_records(self, org, report_date):
        command_org = "bluemix bss org-usage %s --json -d %s" % (org, report_date)
        childProcess = subprocess.Popen(command_org, shell=True, stdout=subprocess.PIPE)
        out, err = childProcess.communicate()
        returnCode = childProcess.poll()
        count = 0
        if returnCode == 0:
            json_str = out
        while returnCode != 0:
            if count > 4:
                self.logger.debug('{} {}: Failed - connection error'.format(org, report_date))
                return None
            childProcess = subprocess.Popen(command_org, shell=True, stdout=subprocess.PIPE)
            out, err = childProcess.communicate()
            returnCode = childProcess.poll()
            if returnCode == 0:
                json_str = out
            count += 1
        json_data = json.loads(json_str)
        spaces_list_raw = json_data[0]["billable_usage"]["spaces"]
        if not spaces_list_raw:
            self.logger.debug('{} {}: None.'.format(org, report_date))
            return None
        self.logger.debug('{} {}: Loaded.'.format(org, report_date))
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
