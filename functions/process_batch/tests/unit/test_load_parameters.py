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


from load_parameters import handler, load_delta_file


### Test:
## 1. load delta file
## 2. break .csv into chunks
## 3. load chunk, create step function
## 4. test creating step function

EVENT_FILE = os.path.join(
    os.path.dirname(__file__),
    'events',
    'event_load_parameters.json'
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
    s3_client.create_bucket(Bucket = event['bucket'])
    yield

@contextmanager
def step_function(stepfunctions_client):
    yield stepfunctions_client

def test_lambda_handler(event):
    os.environ = {"STAGE": "DEV", "BUCKET_NAME": "Test"}
    ret = handler(event, "")
    
    assert ret is not None
    assert "parameters" in ret
    assert "fda" in event
    

def test_lambda_handler_invoke_stepfunction(event):
    os.environ = {"STAGE": "DEV", "BUCKET_NAME": "Test"}
    ret = handler(event, "")

    #response = step_function.start_execution(input=json.dumps(ret))

    assert ret!=None


    
    




