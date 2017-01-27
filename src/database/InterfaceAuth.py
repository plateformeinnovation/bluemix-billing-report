from abc import ABCMeta, abstractmethod


class InterfaceAuth(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def _insert_user(self, user, password, su, orgs):
        pass

    @abstractmethod
    def _delete_user(self, user):
        pass

    @abstractmethod
    def _update_user_pw(self, user, pw):
        pass

    @abstractmethod
    def _update_user_orgs(self, user, orgs):
        pass

    @abstractmethod
    def _authenticate(self, login, password):
        pass

    @abstractmethod
    def _verify_su(self, login):
        pass

    @abstractmethod
    def _list_all_users(self):
        pass
