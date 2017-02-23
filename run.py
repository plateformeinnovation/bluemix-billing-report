#!/usr/bin/env python
import logging
import multiprocessing
import os
import time

from bx_report import VCAP, bx_login, bx_pw, sleep_time, PORT, app, last_update_time, lock
from bx_report.DIfactory.get_loader import get_loader
from bx_report.utils.Utilsdate import Utilsdate


class LoadingProcess(multiprocessing.Process):
    '''
    The process to load billing info into PostgreSQL from bx tool
    '''

    def __init__(self, VCAP, bx_login, bx_pw, sleep_time, last_update_time, lock):
        # super object is a proxy object which delegates the methods of LoadingThread's super class
        super(LoadingProcess, self).__init__(target=self.load, args=(last_update_time, lock))

        self.logger = logging.getLogger(__name__)

        self.sleepTime = float(sleep_time)

        self.bluemix_loader = get_loader(VCAP, bx_login, bx_pw)

    def load(self, last_update_time, lock):
        last_updt_time = self.bluemix_loader.load_all_region(self.bluemix_loader.beginning_date)
        # last_updt_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with lock:
            last_update_time.value = last_updt_time
        while True:
            self.logger.info('loading process {} sleeping...'.format(os.getpid()))
            time.sleep(sleep_time)
            last_updt_time = self.bluemix_loader.load_all_region(Utilsdate.last_month_date())
            with lock:
                last_update_time.value = last_updt_time


logging.info('CPU cores number: {}'.format(multiprocessing.cpu_count()))

loadingProcess = LoadingProcess(VCAP, bx_login, bx_pw, sleep_time, last_update_time, lock)
loadingProcess.daemon = True
loadingProcess.start()

logging.info('main process pid: {}'.format(multiprocessing.current_process().ident))
logging.info('loading process pid: {}'.format(loadingProcess.ident))

app.run('0.0.0.0', PORT)
