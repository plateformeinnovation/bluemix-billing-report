#!/usr/bin/env python
import logging
import multiprocessing

from bx_report import VCAP, bx_login, bx_pw, sleep_time, PORT, app, last_update_time, lock
from bx_report.db_loading_process import LoadingProcess

logging.info('CPU cores number: {}'.format(multiprocessing.cpu_count()))

loadingProcess = LoadingProcess(VCAP, bx_login, bx_pw, sleep_time, last_update_time, lock)
loadingProcess.daemon = True
loadingProcess.start()

logging.info('main process pid: {}'.format(multiprocessing.current_process().ident))
logging.info('loading process pid: {}'.format(loadingProcess.ident))

app.run('0.0.0.0', PORT)
