#!/usr/bin/env python

import os
import csv 


def get_chunks(reader, chunk_size=1):
    """Returns chunks array from csv file

    Args:
        lines ([type]): [description]
        chunk_size (int, optional): [description]. Defaults to 10.
    """
    ## filter empty lines
    chunk = []
    for index, line in enumerate(reader):
        if (index % chunk_size == 0 and index > 0):
            yield chunk
            del chunk[:]
        chunk.append(line)
    yield chunk
    

delta_csv = os.path.join("data", "deltafile.csv")
with open(delta_csv, 'r', encoding='windows-1252') as fin:
    reader = csv.DictReader((line for line in fin if not line.isspace() and not line.replace(",","").isspace()),
                             delimiter=',')
    chunks = []
    for chunk in get_chunks(reader):
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

        print(delta_data)
        chunks.append(delta_data)

    print(len(chunks))
        

 
