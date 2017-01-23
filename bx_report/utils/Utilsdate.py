# coding:utf-8

from datetime import date

from singleton import singleton


@singleton
class Utilsdate:
    def last_month_date(self):
        today = date.today()
        year, month = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
        return date(year, month, 1)

    def stringnize_date(self, current_date):
        return str(current_date.year) + "-" + (
            ("0" + str(current_date.month))
            if current_date.month < 10 else str(current_date.month))

    def previous_month_date(self, current_date):
        day = current_date.day
        month = current_date.month - 1 if current_date.month != 1 else 12
        year = current_date.year if current_date.month != 1 else current_date.year - 1
        return date(year, month, day)

    def previous_month_str(self, date_str):
        year = int(date_str.split('-')[0])
        month = int(date_str.split('-')[1])
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        return str(year) + ('-0' if month < 10 else '-') + str(month)

    def next_month_str(self, date_str):
        if date_str == Utilsdate().stringnize_date(date.today()):
            return date_str
        year = int(date_str.split('-')[0])
        month = int(date_str.split('-')[1])
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        return str(year) + ('-0' if month < 10 else '-') + str(month)
