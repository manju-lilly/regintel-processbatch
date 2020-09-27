#! /usr/bin/env python3

import json
import os
import sys
from datetime import datetime
import logging
import csv
import warnings
import itertools
from datetime import datetime
# AWS specific packages
import boto3

import utils

warnings.filterwarnings("ignore")

# Initialize globals
logger = utils.load_log_config()
configuration = utils.load_osenv()

# Import AWS resources
s3_resource = boto3.resource("s3")
sfn = boto3.client("stepfunctions")


def handler(event, context):
    logger.info("Loading parameters from environment")

    # load environment variables
    stage = configuration.get("STAGE", "dev")
    bucket_name = configuration.get(
        "BUCKET_NAME", "lly-reg-intel-raw-zone-dev")
    s3_delta_file_path = configuration.get("DELTA_FILE_PATH", "")
    s3_metadata_file_path = configuration.get("METADATA_FILE_PATH", "")

    ## log environment variables
    logger.info(msg="Environment variables: ", extra={"stage": stage, "bucket_name": bucket_name, "delta_path": s3_delta_file_path,
                                                      "metadata_path": s3_metadata_file_path})

    ## Build event parameters
    event['parameters'] = {}
    event['parameters']['stage'] = stage
    event['parameters']['bucket_name'] = bucket_name

    ## compute delta file path, metadata file path
    (response, paths) = validate_get_paths(
        s3_delta_file_path, s3_metadata_file_path)
    if not response:
        raise Exception("Nothing to process, delta files not found!")

    # TODO: this will change based on the trigger - or use polling to check if trigger file has updates.
    s3_delta_file_path = paths["delta_file_path"]
    s3_metadata_file_path = paths["metadata_file_path"]

    event['parameters']['s3_metadata_file_path'] = s3_metadata_file_path
    event['parameters']['s3_delta_file_path'] = s3_delta_file_path

    # Logging information
    logging.info(f"s3 path to the delta file:{s3_delta_file_path}")
    logging.info(f"s3 path to the metadata file:{s3_metadata_file_path}")

    istest = True if 'test' in event else False
    delta_file_details = load_delta_file(s3_delta_file_path, istest)

    # Add - stats information
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

    # Invoke stepfunctions
    sfn_arn = "arn:aws:states:us-east-2:896265685124:stateMachine:process-batch"
    logger.info("Starting Step Function (%s) with json %s...",
                sfn_arn, json.dumps(event))

    # if we re testing lambda function - return test
    if "test" in event:
        return event

    response = sfn.start_execution(
        stateMachineArn=sfn_arn,
        input=json.dumps(event)
    )

    return event


def validate_get_paths(s3_delta_file_path, s3_metadata_file_path):
    """[summary]

    Args:
        s3_delta_file_path ([type]): [description]
        s3_metadata_file_path ([type]): [description]
    """
    bucket_name = configuration.get("BUCKET_NAME", "")
    number_of_metadata_files = configuration.get("NUM_METADATA_FILES", 10)

    month = str('%02d' % datetime.now().month)
    year = str(datetime.now().year)
    day = str('%02d' % datetime.now().day)
    hour = str('%02d' % datetime.now().hour)
    minute = str('%02d' % datetime.now().minute)
    second = str('%02d' % datetime.now().second)

    ## year, month, date
    def compute_path(path): return "{}/{}/{}/{}".format(path, year, month, day)

    s3_delta_file_path = compute_path(s3_delta_file_path)
    s3_metadata_file_path = compute_path(s3_metadata_file_path)

    ## check if there is .csv in delta
    csv_file_path = utils.get_s3_objects(
        bucket=bucket_name, prefix=s3_delta_file_path, suffix=".csv")
    csv_file_path = list(csv_file_path)

    if len(csv_file_path) == 0:
        return (False, "delta file not found! nothing to process")

    ## check for metadata
    metadata_files = utils.get_s3_objects(
        bucket=bucket_name, prefix=s3_metadata_file_path, suffix=".txt")
    metadata_files = list(metadata_files)

    if len(metadata_files) != int(number_of_metadata_files):
        return (False, "metadata files not found! nothing to process")

    print(list(map(lambda x: utils.make_s3_uri(bucket_name, x), metadata_files)))

    return (True, {"delta_file_path": utils.make_s3_uri(bucket_name, csv_file_path.pop()), "metadata_file_path": utils.make_s3_uri(bucket_name, s3_metadata_file_path),
                   "metadata_files": list(map(lambda x: utils.make_s3_uri(bucket_name, x), metadata_files))})


def load_delta_file(s3_url, istest=False):
    """
    Method to load the delta file with its content
    """
    if istest:
        f = open(s3_url, 'r')
        lines = f.read().splitlines()

    else:
        response = utils.read_obj_from_bucket(s3_url)
        # split the contents of the file
        content = response['Body'].read().decode('utf-8')
        lines = content.split("\n")

    csv_reader = csv.DictReader((line for line in lines if not line.isspace() and not line.replace(",", "").isspace()),
                                delimiter=',')

    def map_row(row): return {
        'appplication_docs_type_id': row['applicationdocstypeid'],
        'application_no': row['applno'],
        'submission_type': row['submissiontype'],
        'submission_no': row['submissionno'],
        'application_docs_url': row['url'],
        'drug_name': row['drugname'],
        's3_path': row['s3_path'],
        'url': row['url']
    }

    all_records = []
    for row in list(csv_reader):

        s3_path = row['s3_path']

        ## cfm folder her inner pdfs
        if row['s3_path'].endswith("cfm"):
            continue
            bucket_name, key, filename = split_s3_url(s3_path)
            inner_pdf_paths = utils.get_s3_objects(
                BUCKET_NAME=bucket_name, prefix=key, suffix=".pdf")
            for path in list(inner_pdf_paths):
                new_row = row.copy()
                new_row['s3_path'] = path
                all_records.append(map_row(new_row))
        else:
            all_records.append(map_row(row))

    total_no_of_records = len(all_records)
    print(total_no_of_records)

    ##
    n = int(configuration.get('DEFAULT_CHUNK_SIZE', 10))
    chunked_data = [all_records[i * n:(i + 1) * n]
                    for i in range((len(all_records) + n - 1) // n)]

    return (chunked_data, total_no_of_records)
