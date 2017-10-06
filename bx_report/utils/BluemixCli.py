import json
import logging
import subprocess

from singleton import singleton

API_UK = "https://api.eu-gb.bluemix.net"
API_US = "https://api.ng.bluemix.net"
API_AU = "https://api.au-syd.bluemix.net"
API_DE = "https://api.eu-de.bluemix.net"

API_LIST = [API_DE, API_US, API_UK, API_AU]


@singleton
class BluemixCli(object):
    def __init__(self, bx_login, bx_pw):

        self.logger = logging.getLogger(__name__)

        self.bx_login = bx_login
        self.bx_password = bx_pw

        self.connected_region = None

    def cf_login(self, region_api, organization="moodpeek", space="dev"):
        self.connected_region = region_api
        if region_api == API_DE:
            organization = 'CDO'
        command_cf = 'bx login -a {} -u {} -p {} -c 724c026606b28bc419bfe40e8ad2d05c -o {} -s {}'.format(
            region_api, self.bx_login, self.bx_password, organization, space)
        if self.__subprocess(command_cf)[0] != 0:
            raise IOError('cf connection error.')
        self.logger.info('cf connected to region {}'.format(region_api))

    def get_orgs_list_all(self):
        all_orgs = []
        self.logger.info('start loading all organizations from cf...')
        for region_api in API_LIST:
            self.cf_login(region_api)
            all_orgs.extend(self.__get_orgs_list_current_region())
        all_orgs = list(set(all_orgs))
        self.logger.info('all organizations got: ' + str(all_orgs))
        return all_orgs

    def __get_orgs_list_current_region(self):

        command_summary = "bx cf orgs"
        return_code, out = self.__subprocess(command_summary)
        while return_code != 0:
            return_code, out = self.__subprocess(command_summary)
        org_list = out.split('\n')[3:-1]
        return org_list

    def get_orgs_list_by_date(self, report_date):

        command_summary = "bx billing orgs-usage-summary -d %s --json" % (report_date)
        return_code, out = self.__subprocess(command_summary)
        while return_code != 0:
            self.logger.debug('Getting organization list again for {}'.format(report_date))
            return_code, out = self.__subprocess(command_summary)
        json_str = out

        json_data = json.loads(json_str)
        org_list = list()
        if json_data["organizations"]:
            for org in json_data["organizations"]:
                org_list.append(org["name"])

        self.logger.debug('organization list {}: {}'.format(report_date, org_list))
        return org_list

    def retrieve_records(self, org, report_date):
        command_org = "bx billing org-usage %s --json -d %s" % (org, report_date)

        return_code, out = self.__subprocess(command_org)
        cnt = 0
        while return_code != 0 and cnt < 5:
            cnt += 1
            return_code, out = self.__subprocess(command_org)
        if return_code != 0:
            self.logger.debug('{} {}: Failed - connection error'.format(org, report_date))
            return None
        else:
            json_str = out

        json_data = json.loads(json_str)
        spaces_list_raw = json_data[0]["billable_usage"]["spaces"]
        if not spaces_list_raw:
            self.logger.debug('{} {}: None.'.format(org, report_date))
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
        self.logger.debug('{} {}: Loaded.'.format(org, report_date))
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

    def __subprocess(self, command):
        child_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        out, err = child_process.communicate()
        return_code = child_process.poll()
        return (return_code, out)
