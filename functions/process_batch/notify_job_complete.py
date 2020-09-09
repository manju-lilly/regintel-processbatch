import json
import boto3
import time
import urllib
import os

import logging

## Initialize logging
logger = utils.load_log_config()

# Read configuration
configuration = utils.load_osenv()
logging.info(f"read configuration:{len(configuration)}")


s3 = boto3.resource('s3')
sns = boto3.client('sns')


def handler(event, context):
    logger.info(' sending notification of job completion to operations user')

    # send an email to the operations user - request folder + data received
    operations_notification_arn = os.environ['OPERATIONS_NOTIFICATION_ARN']
    email_subject = 'Job Complete - Folder - ' + directory_name
    email_body = json.dumps(event, indent=2)

    sns.publish(
        TopicArn=operations_notification_arn,
        Message=email_body,
        Subject=email_subject
    )
