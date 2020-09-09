#! /usr/bin/env python3

import json
import os
import sys
from datetime import datetime
import logging
import csv
import warnings
import itertools

# AWS specific packages
import boto3

import utils

warnings.filterwarnings("ignore")
## Initialize globals
logger = utils.load_log_config()
configuration = utils.load_osenv()

## Import AWS resources
s3_resource = boto3.resource("s3")
sfn = boto3.client("stepfunctions")
    
CHUNK_SIZE = 2
def handler(event, context):
    logger.info("Loading parameters from environment")
    
    ## load environment variables
    stage = os.environ['STAGE']
    bucket_name = os.environ['BUCKET_NAME']

    logger.info(' stage: ' + stage)
    logger.info(' bucket_name: ' + bucket_name)

    
    event['parameters'] = {}
    
    event['parameters']['stage'] = stage
    event['parameters']['bucket_name'] = bucket_name
    

    ## TODO: this will change based on the trigger - or use polling to check if trigger file has updates.
    s3_delta_file_path = event['s3_delta_file_path']
    s3_metadata_file_path = event['s3_metadata_file_path']
    
    event['parameters']['s3_metadata_file_path'] = s3_metadata_file_path
    event['parameters']['s3_delta_file_path'] = s3_delta_file_path
    
    
    ## Logging information
    logging.info(f"s3 path to the delta file:{s3_delta_file_path}")
    logging.info(f"s3 path to the metadata file:{s3_metadata_file_path}")

    delta_file_details = load_delta_file(s3_delta_file_path)

    ## Add - stats information
    if not "fda" in event:
        event['fda'] = {}
        event['fda']['process_batch_stats'] = {}
        
        # start timestamp
        start_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S:%f")
        event['fda']['process_batch_stats']['process_batch_start_timestamp'] = start_ts
        event['fda']['process_batch_stats']['process_batch_end_timestamp'] = None
        event['fda']['process_batch_stats']['stepfunction-execution-counter'] = 1
        event['fda']['process_batch_stats']['number_of_records_to_process'] = delta_file_details[1]
        
        event['fda']['chunks'] = delta_file_details[0]
    
        
    else:
        event['process_batch_stats']['fda']['stepfunction-execution-counter'] += 1

    
    ## Invoke stepfunctions
    sfn_arn = "arn:aws:states:us-east-2:896265685124:stateMachine:process-batch"
    logger.info("Starting Step Function (%s) with json %s...", sfn_arn, json.dumps(event))
    
    response = sfn.start_execution(
        stateMachineArn=sfn_arn,
        input= json.dumps(event)
    )
    
    
    return event

def load_delta_file(s3_url):
    """
    Method to load the delta file with its content
    
    """
    response = utils.read_obj_from_bucket(s3_url)

    # split the contents of the file
    content = response['Body'].read().decode('utf-8')
    lines = content.split("\n")

    csv_reader = csv.DictReader((line for line in lines if not line.isspace() and not line.replace(",", "").isspace()),
                            delimiter=',')
    
    chunked_data = []
    total_no_of_records = 0
    total_no_of_records = len(list(csv_reader))
    
    for chunk in utils.get_chunks(csv_reader, CHUNK_SIZE):
        delta_data = []
        for row in chunk:
            if row['ApplNo']!='':
                delta_data.append({
                    'appplication_docs_type_id': row['ApplicationDocsTypeID'],
                    'application_no': row['ApplNo'] ,
                    'submission_type': row['SubmissionType'],
                    'submission_no': row['SubmissionNo'],
                    'application_docs_url': row['ApplicationDocsURL'],
                    'drug_name': row['DrugName'],
                    's3_path': row['S3Path']
                })
        chunked_data.append(delta_data)
        
    return (chunked_data,total_no_of_records)