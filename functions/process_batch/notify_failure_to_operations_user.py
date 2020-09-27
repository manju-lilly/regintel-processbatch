import json
import boto3
import time
import urllib
import os

sns = boto3.client('sns')


class ProcessBatchFDAStateMachineFailedException(Exception):
    pass


def handler(event, context):
    # send an email to the operations user - exceptions message
    operations_notification_arn = os.environ['OPERATIONS_NOTIFICATION_ARN']
    stage = os.environ['STAGE']
    request_id = context.aws_request_id

    metadata_path = event["s3_metadata_file_path"]
    delta_file_path = event["s3_delta_file_path"]

    email_subject = 'Job Failed : Process Batch FDA : ' + delta_file_path
    email_body = json.dumps(event, indent=2)

    sns.publish(
        TopicArn=operations_notification_arn,
        Message=email_body,
        Subject=email_subject
    )

    raise ProcessBatchFDAStateMachineFailedException(
        'FDA process batch state machine failed to execute completely.')
