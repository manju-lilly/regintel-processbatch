#!/usr/bin/env python

import logging
import os
import boto3
from botocore.exceptions import ClientError
import json
import sys

from datetime import datetime
import uuid

from custom_log_formatter import CustomLogFormatter


def load_osenv():
    """
    Method to load environment variables
    
    return: os environment parameters
    """
    config = {}
    for key in os.environ.keys():
        config[key] = os.getenv(key, "")

    return config

# Ref: citeline


def load_log_config():
    """
    Configure custom logformatter
    """
    # basic configuration
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = CustomLogFormatter(
        '[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(levelno)s\t%(message)s\n', '%Y-%m-%dT%H:%M:%S')

    if logger.hasHandlers():
        logger.debug("using default lambda log handler")
        log_handler = logger.handlers[0]
        log_handler.setFormatter(formatter)
    else:
        logger.debug("creating a new handler")

        # initialize the handler
        log_handler = logging.StreamHandler(sys.stdout)
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)

    ## set log level
    logger.setLevel(logging.DEBUG)

    ## set loglevel
    boto3.set_stream_logger('botocore', logging.WARNING)
    boto3.set_stream_logger('boto3', logging.WARNING)

    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('s3transfer').setLevel(logging.WARNING)

    return logger


def make_unique_id():
    """Build unique id

    Returns:
        string: uuid
    """
    id = uuid.uuid4()
    return str(id)

## Ref: citeline


def split_s3_url(s3_object_url):
    """Method to slit s3 url into its component parts

    Args:
        s3_object_url: s3 url

    Returns:
        bucket_name: s3 bucket name
        prefix: s3 url prefix
        filename: s3 url filename

    """
    # remove s3://

    ## Load logger
    logger = load_log_config()

    s3_object_url = s3_object_url.replace("s3://", "")

    s3_parts = s3_object_url.split("/")
    bucket_name = s3_parts[0]

    prefix = "/".join(s3_parts[1:])
    filename = os.path.basename(prefix)

    logger.debug("%s bucket name: %s", s3_object_url, bucket_name)
    logger.debug("%s prefix: %s", s3_object_url, prefix)
    logger.debug("%s filename: %s", s3_object_url, filename)

    return (bucket_name, prefix, filename)


def read_obj_from_bucket(object_path):
    """Method to read from the s3 object path

    Args:
        object_path (str): s3 object path
    """

    ## path
    logger = load_log_config()

    logger.info(f"Reading from: {object_path}")

    client = boto3.resource("s3")

    bucket_name, prefix, filename = split_s3_url(object_path)

    s3_object = client.Object(bucket_name=bucket_name, key=prefix)

    try:
        content = s3_object.get()
        logger.info(
            f"{content['ContentLength']} bytes read from the s3 object: {object_path}")

    except ClientError as e:
        logger.exception(f"failed to read contents of the file: {object_path}")
        raise

    return content

