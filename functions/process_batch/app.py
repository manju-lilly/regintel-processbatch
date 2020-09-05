#!/usr/bin/env python
from __future__ import print_function

import boto3
import json
import time
import os
import logging

from botocore.exceptions import ClientError

from urllib.parse import unquote_plus
from bs4 import BeautifulSoup
import traceback
import re

import utils

## Initialize logging
logger = logging.getLogger()
utils.load_log_config()

# Read configuration
configuration = utils.load_osenv()
logging.info(f"read configuration:{len(configuration)}")


# initialize AWS services
S3_CLIENT = boto3.client('s3')
S3_RESOURCE = boto3.resource('s3')

def lambda_handler(event, context):
    """
    Method trigger file and construct events 
    
    :param event
    :param context
    
    """
    

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": capitalize("hello world")
        }) 
    }
