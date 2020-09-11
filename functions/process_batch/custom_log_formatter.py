#!/usr/bin/env python

import logging
import json

## Format logger


class CustomLogFormatter(logging.Formatter):

    def format(self, record):

        ## get message from record
        record.message = record.getMessage()

        ## include time
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        j = {
            'levelname': record.levelname,
            'time': '%(asctime)s.%(msecs)dZ' % dict(asctime=record.asctime, msecs=record.msecs),
            'aws_request_id': getattr(record, 'aws_request_id', '00000000-0000-0000-0000-000000000000'),
            'message': record.message,
            'module': record.module,
            'extra_data': record.__dict__.get('data', {}),
        }

        return json.dumps(j)
