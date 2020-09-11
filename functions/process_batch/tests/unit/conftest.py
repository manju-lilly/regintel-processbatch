#!/usr/bin/env python3

import os
import boto
import boto3
from moto import mock_stepfunctions, mock_s3, mock_sns
import pytest


@pytest.fixture(scope='module')
def aws_credentials():
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    


@pytest.fixture(scope='module')
def s3_client(aws_credentials):
    """[summary]
    s3 mock client
    Args:
        aws_credentials ([type]): [description]
    """
    with mock_s3():
        conn = boto3.client('s3', region_name='us-east-2')
        yield conn

@pytest.fixture(scope='module')
def stepfunctions_client(aws_credentials):
    """
    
    step functions

    Args:
        aws_credentials ([type]): [description]
    """
    with mock_stepfunctions():
        conn = boto3.client("stepfunctions", region_name='us-east-2')


