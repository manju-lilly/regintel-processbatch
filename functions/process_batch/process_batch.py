#!/usr/bin/env python
from __future__ import print_function

import boto3
import json
import time
import os
import logging
import warnings
import csv
import datetime

from botocore.exceptions import ClientError

from urllib.parse import unquote_plus
import traceback
import re

import utils
from fda_api import FDAAPI

# ignore warnings
warnings.filterwarnings("ignore")

## Initialize logging
logger = utils.load_log_config()

# Read configuration
configuration = utils.load_osenv()
logging.info(f"read configuration:{len(configuration)}")


# initialize AWS services
S3_CLIENT = boto3.client('s3')
S3_RESOURCE = boto3.resource('s3')

# Create CloudWatchEvents client
CLOUDWATCH_EVENTS = boto3.client('events')


def handler(event, context):
    """
    Method trigger file and construct events 
    
    :param event
    :param context
    
    """
    logging.info(" in process delta lambda function")
    

    stage = event['parameters']['stage']
    bucket_name = event['parameters']['bucket_name']

    ## check stats
    total_records_process = event['process_batch_stats']['number_of_records_to_process'] if 'process_batch_stats' in event else 0
    if total_records_process == 0:
        ## notify to user process complete nothing to process
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "no records to process"
            })
        }

    # else process the chunks.
    s3_metadata_file_path = event['parameters']['s3_metadata_file_path']
    logging.info(f"s3 path to the metadata file:{s3_metadata_file_path}")

    delta_file_records = event['chunks']
    is_test = True if "test" in event else False
    api = FDAAPI(S3_metadata_loc=s3_metadata_file_path, test=is_test)

    '''
     'appplication_docs_type_id': row[0],
            'application_no': application_no,
            'submission_type': row[2],
            'submission_no': row[3],
            'application_docs_url': row[4],
            'drug_name': row[5],
            's3_path': row[6]
    '''
    for row in delta_file_records:
        fda_metadata = api.format_response(
            application_no=int(row['application_no']), submission_no=int(row['submission_no']),
            application_doc_type_id=int(row['appplication_docs_type_id']),
            submission_type=row['submission_type'], s3_raw=row['s3_path'], url=row['application_docs_url'])

        ## Put an event
        
        response = CLOUDWATCH_EVENTS.put_events(
            Entries=[
                {
                    'Time': datetime.datetime.now(),
                    'Source': 'process_batch_fda',
                    'DetailType': 'process batch event submitted',
                    'Detail': json.dumps({"metadata": fda_metadata})
                },
            ]
        )
        print(json.dumps(fda_metadata, indent=4))

    return event
