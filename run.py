#!/usr/bin/env python
import threading

from bx_report import app
from bx_report.database import get_loader, sleep_time


class LoadingThread(threading.Thread):
    '''
    The thread to load consumption info into PostgreSQL
    '''

    def __init__(self, sleep_time):
        # super object is a proxy object which delegates the methods of LoadingThread's super class
        super(LoadingThread, self).__init__()

        self.sleepTime = float(sleep_time)

        self.bluemix = get_loader()

    def run(self):
        self.bluemix.load_all_region(self.bluemix.beginning_date)
        while True:
            self.bluemix.load_all_region(self.bluemix.last_month_date())


loadingThread = LoadingThread(sleep_time)
loadingThread.setDaemon(True)
loadingThread.start()

app.run('0.0.0.0', 5000)
