#!/usr/bin/env python

import logging
import os
from datetime import datetime

## ref: stackoverflow
class ProcessBatchExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)
    
    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace('\n', "")
        return result    

def load_log_config():

    # basic configuration
    log = logging.getLogger('process_batch')
    log.setLevel(logging.INFO)

    ## Add handler - replace with cloudwatch
    ## custom log formatter
    if not os.path.exists("logs"):
        os.makedirs("logs")

    ## exception formatter
    filehandler = logging.FileHandler(
        os.path.join("logs", 'log_{:%Y-%m-%d}.log'.format(datetime.now())))
    streamhandler = logging.StreamHandler()
    filehandler.setFormatter(ProcessBatchExceptionFormatter(logging.BASIC_FORMAT))
    streamhandler.setFormatter(
        ProcessBatchExceptionFormatter(logging.BASIC_FORMAT))


    ## add handlers
    log.addHandler(streamhandler)
    log.addHandler(filehandler)
