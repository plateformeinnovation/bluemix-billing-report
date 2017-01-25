from abc import ABCMeta, abstractmethod

class InterfaceBillingRetrieve(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_all_organizations(self):
        pass

    @abstractmethod
    def cost_by_space(self, region, org, date_str):
        pass

    @abstractmethod
    def cost_by_category(self, region, org, date_str):
        pass

    @abstractmethod
    def cost_detail_by_space_category(self, region, org, date_str):
        pass