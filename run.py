#!/usr/bin/env python
import logging
import multiprocessing
import os
import time

from bx_report import VCAP, bx_login, bx_pw, sleep_time, PORT, app
from bx_report.DIfactory.get_loader import get_loader
from bx_report.utils.Utilsdate import Utilsdate


class LoadingProcess(multiprocessing.Process):
    '''
    The process to load billing info into PostgreSQL from bx tool
    '''

    def __init__(self, VCAP, bx_login, bx_pw, sleep_time):
        # super object is a proxy object which delegates the methods of LoadingThread's super class
        super(LoadingProcess, self).__init__()

        self.logger = logging.getLogger(__name__)

        self.sleepTime = float(sleep_time)

        self.bluemix_loader = get_loader(VCAP, bx_login, bx_pw)

    def run(self):
        self.bluemix_loader.load_all_region(self.bluemix_loader.beginning_date)
        while True:
            self.logger.info('loading process {} sleeping...'.format(os.getpid()))
            time.sleep(sleep_time)
            self.bluemix_loader.load_all_region(Utilsdate.last_month_date())


logging.info('CPU cores number: {}'.format(multiprocessing.cpu_count()))
lock = multiprocessing.Lock()
loadingProcess = LoadingProcess(VCAP, bx_login, bx_pw, sleep_time)
loadingProcess.daemon = True
loadingProcess.start()
logging.info('main process: {}'.format(multiprocessing.current_process().ident))
logging.info('child process (loading): {}'.format(loadingProcess.ident))

app.run('0.0.0.0', PORT)
