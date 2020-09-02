#!/usr/bin/env python

import logging
import os
from datetime import datetime
import uuid

def load_log_config():

    # basic configuration
    log = logging.getLogger('process_batch')
    log.setLevel(logging.INFO)

    ## Add handler - replace with cloudwatch
    ## custom log formatter
    if not os.path.exists("logs"):
        os.makedirs("logs")

    ## exception formatter, replace with cloud
    filehandler = logging.FileHandler(os.path.join("logs", 'log_{:%Y-%m-%d}.log'.format(datetime.now())))
    streamhandler = logging.StreamHandler()
    

    ## add handlers
    log.addHandler(streamhandler)
    log.addHandler(filehandler)


def make_unique_id():
    id = uuid.uuid4()
    return str(id)
