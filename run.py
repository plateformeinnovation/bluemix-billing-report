#!/usr/bin/env python
import logging
import multiprocessing
import time

from bx_report import VCAP, bx_login, bx_pw, sleep_time, PORT, app
from bx_report.DIfactory.get_loader import get_loader


class LoadingProcess(multiprocessing.Process):
    '''
    The thread to load consumption info from bx tool into PostgreSQL
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
            self.logger.info('loading process sleeping...')
            time.sleep(sleep_time)
            self.bluemix_loader.load_all_region(self.bluemix_loader.last_month_date())


logging.info('CPU cores number: {}'.format(multiprocessing.cpu_count()))
loadingProcess = LoadingProcess(VCAP, bx_login, bx_pw, sleep_time)
loadingProcess.daemon = True
loadingProcess.start()
logging.info('main process on core: {}'.format(multiprocessing.current_process().ident))
logging.info('loading child process on core: {}'.format(loadingProcess.ident))

app.run('0.0.0.0', PORT)
