#!/usr/bin/env python
import threading
import time

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

        self.bluemix_loader = get_loader()

    def run(self):
        self.bluemix_loader.load_all_region(self.bluemix_loader.beginning_date)
        while True:
            time.sleep(sleep_time)
            self.bluemix_loader.load_all_region(self.bluemix_loader.last_month_date())


loadingThread = LoadingThread(sleep_time)
loadingThread.setDaemon(True)
loadingThread.start()

app.run('0.0.0.0', 5000)
