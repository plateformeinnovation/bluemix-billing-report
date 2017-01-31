class GlobalV(object):
    current_date = None
    organizations = None

    @staticmethod
    def set_current_date(current_date):
        GlobalV.current_date = current_date

    @staticmethod
    def set_organizations(organizations):
        GlobalV.organizations = organizations

    @staticmethod
    def get_current_date():
        return GlobalV.current_date

    @staticmethod
    def get_organizations():
        return GlobalV.organizations
