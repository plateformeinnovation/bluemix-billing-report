class UserSession(object):
    current_date = None
    organizations = None

    @staticmethod
    def set_current_date(current_date):
        UserSession.current_date = current_date

    @staticmethod
    def set_organizations(organizations):
        UserSession.organizations = organizations

    @staticmethod
    def get_current_date():
        return UserSession.current_date

    @staticmethod
    def get_organizations():
        return UserSession.organizations
