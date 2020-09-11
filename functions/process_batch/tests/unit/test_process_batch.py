#!/usr/bin/env python3
# pylint: disable=redefined-outer-name,missing-docstring

import json
import os
import pytest
import boto3
import imp

from botocore.exceptions import ClientError
from contextlib import contextmanager

from moto import mock_s3, mock_stepfunctions
from process_batch import handler

EVENT_FILE = os.path.join(
    os.path.dirname(__file__),
    'events',
    'event_process_batch.json'
)

@pytest.fixture()
def event(event_file=EVENT_FILE):
    """
    Trigger event
    
    """
    with open(event_file) as f:
        return json.load(f)


@contextmanager
def s3_setup(s3_client, event):
    """
    Create s3 bucket

    Args:
        s3_client ([type]): [description]
        event ([type]): [description]
    """
    s3_client.create_bucket(Bucket=event['bucket'])
    yield


@contextmanager
def step_function(stepfunctions_client):
    yield stepfunctions_client


def test_lambda_handler(event):
    os.environ = {"STAGE": "DEV", "BUCKET_NAME": "Test"}
    ret = handler(event, "")

    assert ret is not None
    
    