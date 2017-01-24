from abc import ABCMeta, abstractmethod

class InterfaceAuthMod(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def _check_existence(self, region, org, space, date):
        pass

    @abstractmethod
    def _update_record(self, region, org, space, date, applications, containers, services):
        pass

    @abstractmethod
    def _insert_record(self, region, org, space, date, applications, containers, services):
        pass
