#!/usr/bin/env python

import os
import json
import sqlite3
import traceback
import csv
import time

from functools import reduce

import logging
from collections import namedtuple

from utils import load_log_config, make_unique_id, read_obj_from_bucket

META_DATA_ITEM = namedtuple("META_DATA_ITEM", 'tablename filename')


class FDAAPI(object):
    """
    FDA class to extract data from the document

    Args:
        object ([type]): [description]
    """
    # region metadata_info
    APPLICATION = META_DATA_ITEM('application', 'Applications.txt')
    ACTION_TYPE = META_DATA_ITEM('action_type', 'ActionTypes_Lookup.txt')
    APPLICATION_DOC = META_DATA_ITEM('application_doc', 'ApplicationDocs.txt')
    APPLICATION_DOC_TYPE = META_DATA_ITEM(
        'application_doc_type', 'ApplicationsDocsType_Lookup.txt')
    MARKETING_STATUS = META_DATA_ITEM(
        'marketing_status', 'MarketingStatus.txt')
    MARKETING_STATUS_LOOKUP = META_DATA_ITEM(
        'marketing_status_lookup', 'MarketingStatus_Lookup.txt')
    PRODUCT = META_DATA_ITEM('product', 'Products.txt')
    SUBMISSION_CLASS = META_DATA_ITEM(
        'submission_class', 'SubmissionClass_Lookup.txt')
    SUBMISSION_PROPERTY_TYPE = META_DATA_ITEM(
        'submission_property_type', 'SubmissionPropertyType.txt')
    SUBMISSION = META_DATA_ITEM('submission', 'Submissions.txt')
    TE = META_DATA_ITEM('te', 'TE.txt')

    # endregion

    APPLICATION_TYPE_MAPPING = {'IND': 'Investigational New Drug Application', 'NDA': 'New Drug Application',
                                'BLA': 'Biologic License Application', 'ANDA': 'Abbreviated New Drug,Application', 'OTC': 'Over-the-Counter'}

    ## TODO: check with Suresh
    APPROVED = "Approved"

    def __init__(self, **kwargs):
        metadata_folder_loc = kwargs.get('S3_metadata_loc', '')

        if metadata_folder_loc is None:
            raise Exception("Metadata location was not specified!")

        self.metadata_folder_loc = metadata_folder_loc
        self.engine_url = ":memory:"

        # setup logger
        self.logger = load_log_config()
        self.conn, self.cursor = self.create_connection()

        result = self.create_tables()

        # if result - insert metadata
        if result:
            self.insert_metadata()

    def create_connection(self):
        """
        create database connection to the SQLite database specified by database file location  
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(self.engine_url)
            conn.row_factory = sqlite3.Row  # getting the column names
            c = conn.cursor()
        except Exception as e:
            self.logger.error("error creating connection", e)

        return (conn, c)

    def create_tables(self):
        number_of_tables = 0
        conn = self.conn
        try:
            # open connection
            # Action Types
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, description TEXT, supplCategoryLevel1Code TEXT,supplCategoryLevel2Code TEXT, PRIMARY KEY(id))" % self.ACTION_TYPE.tablename)
            number_of_tables += 1

            # ApplicationDocs
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, docsTypeId	INTEGER, applNo	INTEGER, submissionType	TEXT, submissionNo	INTEGER, applicationDocsTitle	TEXT, applicationDocsURL	TEXT, applicationDocsDate	TEXT);" % self.APPLICATION_DOC.tablename)
            number_of_tables += 1

            # Application table
            conn.execute("CREATE TABLE if not exists %s ( applNo integer, applType text, applPublicNotes text, sponsorName text);" %
                         self.APPLICATION.tablename)
            number_of_tables += 1

            # ApplicationDocsType_Lookup table
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, description TEXT);" %
                         self.APPLICATION_DOC_TYPE.tablename)
            number_of_tables += 1

            # Marketing status
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, applNo	INTEGER, productNo	INTEGER);" %
                         self.MARKETING_STATUS.tablename)
            number_of_tables += 1

            # Marketing status lookup
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, description TEXT);" %
                         self.MARKETING_STATUS_LOOKUP.tablename)
            number_of_tables += 1

            # Products
            conn.execute("CREATE TABLE if not exists %s (applNo	INTEGER, productNo	INTEGER, form	TEXT, strength	TEXT,referenceDrug	TEXT, drugName	TEXT, activeIngredient	TEXT, referenceStandard	TEXT); " % self.PRODUCT.tablename)
            number_of_tables += 1

            # Submission Class Lookup
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, submissionClassCode	TEXT,submissionClassDescription	TEXT);" %
                         self.SUBMISSION_CLASS.tablename)
            number_of_tables += 1

            # Submission Property Type
            conn.execute("CREATE TABLE if not exists %s (applNo	INTEGER, submissionType	TEXT, submissionNo	INTEGER,submissionPropertyTypeCode	TEXT, SubmissionPropertyTypeID	TEXT);" %
                         self.SUBMISSION_PROPERTY_TYPE.tablename)
            number_of_tables += 1

            # Submissions
            conn.execute("CREATE TABLE if not exists %s (applNo INTEGER, subclasscodeId	INTEGER, subType	TEXT,subNo	INTEGER, subStatus	TEXT, subDate	TEXT, subPublicNotes	TEXT, reviewPriority	TEXT);" % self.SUBMISSION.tablename)
            number_of_tables += 1

            # TE
            conn.execute(
                "CREATE TABLE if not exists %s (applNo	INTEGER, productNo	INTEGER, marketingStatusId	INTEGER,teCode	TEXT);" % self.TE.tablename)
            number_of_tables += 1

            # commit
            conn.commit()

        except Exception as ex:
            tb = traceback.format_exc()
            self.logger.error(tb)
            self.logger.exception('exception occurred while creating tables')
            return False

        # names of the table that are created
        query = "SELECT tbl_name FROM sqlite_master WHERE type='table'"
        rows = self.conn.execute(query).fetchall()
        for row in rows:
            self.logger.info("table created: %s" % row[0])

        return True

    def get_rows(self, sql):
        """Function for getting multiple rows

        Args:
            sql (string): select query
        """
        cur = self.conn.cursor()
        self.conn.row_factory = self.sqlite_dict
        cur.execute(sql)
        return cur.fetchall()

    def get_row(self, sql):
        """Function for getting multiple rows

        Args:
            sql (string): select query
        """
        cur = self.conn.cursor()
        self.conn.row_factory = self.sqlite_dict
        cur.execute(sql)
        return cur.fetchone()

    def insert_metadata(self):
        """
        insert metadata
        """
        ## ActionTypes
        num_rows = self.insert_action_type(self.read_metadata_file(os.path.join(
            self.metadata_folder_loc, self.ACTION_TYPE.filename)))

        self.logger.info(
            f"inserted into action type, no of rows: {num_rows} inserted")

        ## ApplicationDocs
        self.insert_into_appl_docs(self.read_metadata_file(os.path.join(
            self.metadata_folder_loc, self.APPLICATION_DOC.filename)))
        print("inserted into application docs")

        ## Applications
        self.insert_into_appl(self.read_metadata_file(os.path.join(
            self.metadata_folder_loc, self.APPLICATION.filename)))
        print("inserted into applications")

        ## application doc type
        self.insert_into_appl_docs_type(self.read_metadata_file(os.path.join(
            self.metadata_folder_loc, self.APPLICATION_DOC_TYPE.filename)))
        print("inserted into application doc type")

        ## marketing
        self.insert_into_marketing_status(self.read_metadata_file(
            os.path.join(self.metadata_folder_loc, self.MARKETING_STATUS.filename)))

        ## marketing status
        self.insert_into_marketing_status_lookup(self.read_metadata_file(
            os.path.join(self.metadata_folder_loc, self.MARKETING_STATUS_LOOKUP.filename)))

        ## products
        self.insert_into_products(self.read_metadata_file(
            os.path.join(self.metadata_folder_loc, self.PRODUCT.filename)))

        ## submission class lookup
        self.insert_into_submission_class_lookup(self.read_metadata_file(
            os.path.join(self.metadata_folder_loc, self.SUBMISSION_CLASS.filename)))

        ## submission property type
        self.insert_into_submission_property_type(self.read_metadata_file(
            os.path.join(self.metadata_folder_loc, self.SUBMISSION_PROPERTY_TYPE.filename)))

        # submissions
        self.insert_into_submissions(self.read_metadata_file(
            os.path.join(self.metadata_folder_loc, self.SUBMISSION.filename)))

        # te
        self.insert_into_te(self.read_metadata_file(
            os.path.join(self.metadata_folder_loc, self.TE.filename)))

    def format_response(self, **kwargs):
        """[summary] JSON response for the event

        Args:
            drug_name ([string]): [drug name]
            application_no ([int]): [application no]
            supplement_type ([string]): [type of the supplement whether original or supplement]
            supplement_number ([int]): [supplement number]
            application_doc_typeId ([int]): [description]

        Returns:
            [type]: [json event response]
        """
        strTime = time.localtime(time.time())
        last_updated = time.strftime("%Y-%m-%d", strTime)
        application_no = kwargs.get("application_no", "")
        submission_type = kwargs.get("submission_type", "")
        submission_no = kwargs.get("submission_no", "")
        application_doc_type_id = kwargs.get("application_doc_type_id", "")
        s3_raw = kwargs.get("s3_raw", "")
        url = kwargs.get("url", "")

        product_info = self.get_products(application_no)
        application_info = self.get_application(application_no)
        submission_info = self.get_submission(
            application_no, application_doc_type_id, submission_no)

        # lambda helpers
        def extract_from_product_info(key, dict_items): return list(
            set([self.extract_from_dict(key, item) for item in dict_items]))

        def get_item(l): return l.pop() if len(l) == 1 else l

        ## Construct response object
        ## build response object
        response = {}
        response['s3_raw'] = s3_raw
        response['last_updated'] = last_updated
        response['source_url'] = url
        response['file_name'] = os.path.basename(s3_raw)
        response['data_source'] = 'FDA'
        response['drug_name'] = get_item(
            extract_from_product_info("drug_name", product_info))
        response['active_substance'] = extract_from_product_info(
            "active_substance", product_info)
        response['strength'] = extract_from_product_info(
            "strength", product_info)
        response['dosage_form'] = extract_from_product_info(
            "dosage_form", product_info)
        response['therapeutic_area'] = ''
        response['therapeutic_indication'] = ''
        response['year_of_authorization'] = self.extract_from_dict(
            "yearOfAuthorization", submission_info)
        response['license_holder'] = self.extract_from_dict(
            'sponsorName', application_info)
        response['route_of_administration'] = extract_from_product_info(
            "dosage_form", product_info)

        ## TODO: check with Suresh again
        response['submission_date_for_initial_approval'] = ''

        ## NCE, Labeling etc.
        response['approval_type'] = self.extract_from_dict(
            'approvalType', submission_info)
        response['document_type'] = self.extract_from_dict(
            'documentTypeDesc', application_info)

        ## TODO: check with Suresh again (EMA has Authorized/Withdrawn)
        response['approval_status'] = self.APPROVED
        response['orphan_designation'] = self.extract_from_dict(
            'orphanDesignation', submission_info)

        fda = {}
        fda['application_no'] = application_no
        fda['submission_no'] = submission_no

        fda['submission_type_id'] = application_doc_type_id
        fda['submission_type_desc'] = self.extract_from_dict(
            'submissionType', submission_info)

        fda['approval_type_code'] = self.extract_from_dict(
            'approvalTypeCode', submission_info)
        fda['submission_status'] = self.extract_from_dict(
            'submissionStatus', submission_info)
        fda['submission_notes'] = self.extract_from_dict(
            'submissionNotes', submission_info)
        fda['review_priority'] = self.extract_from_dict(
            'reviewPriority', submission_info)
        fda['products'] = product_info

        response['fda'] = fda

        return response

    # region private methods to insert data
    def insert_action_type(self, data):
        types = []

        for row in data:
            id = int(row['ActionTypes_LookupID'])
            desc = self.clean_string(
                row['ActionTypes_LookupDescription']) if row['ActionTypes_LookupDescription'] else ""
            code1 = self.clean_string(
                row['SupplCategoryLevel1Code']) if row['SupplCategoryLevel1Code'] else ""
            code2 = self.clean_string(
                row['SupplCategoryLevel2Code']) if row['SupplCategoryLevel2Code'] else ""

            types.append((id, desc, code1, code2))

        self.insert_into_sqlite_table(
            types, "INSERT or IGNORE INTO %s VALUES (?,?,?,?)" % self.ACTION_TYPE.tablename)

    def insert_into_appl_docs(self, data):
        docs = []
        for row in data:
            docsId = int(row['ApplicationDocsID'])
            docTypeId = int(row['ApplicationDocsTypeID']
                            ) if row['ApplicationDocsTypeID'] else ''
            applNo = int(row['ApplNo']) if row['ApplNo'] else ''
            subtype = self.clean_string(
                row['SubmissionType']) if row['SubmissionType'] else ""
            subno = int(row['SubmissionNo']) if row['SubmissionNo'] else ""
            appDocTitle = self.clean_string(
                row['ApplicationDocsTitle']) if row['ApplicationDocsTitle'] else ""
            applDocUrl = self.clean_string(
                row['ApplicationDocsURL']) if row['ApplicationDocsURL'] else ""
            applDate = self.clean_string(
                row['ApplicationDocsDate']) if row['ApplicationDocsDate'] else ""

            docs.append((docsId, docTypeId, applNo, subtype, subno,
                         appDocTitle, applDocUrl, applDate))

        self.insert_into_sqlite_table(
            docs, "INSERT or IGNORE INTO %s VALUES (?,?,?,?,?,?,?,?)" % self.APPLICATION_DOC.tablename)

    def insert_into_appl(self, data):
        applications = []

        for row in data:
            applNo = int(row['ApplNo']) if row['ApplNo'] else ''
            appltype = self.clean_string(
                row['ApplType']) if row['ApplType'] else ""
            applPublicNotes = self.clean_string(
                row['ApplPublicNotes']) if row['ApplPublicNotes'] else ""
            sponsorName = self.clean_string(
                row['SponsorName']) if row['SponsorName'] else ""

            applications.append((applNo, appltype, applPublicNotes,
                                 sponsorName))

        self.insert_into_sqlite_table(
            applications, "INSERT or IGNORE INTO %s VALUES (?,?,?,?)" % self.APPLICATION.tablename)

    def insert_into_appl_docs_type(self, data):
        appl_doc_types = []

        for row in data:
            id = int(row['ApplicationDocsType_Lookup_ID']
                     ) if row['ApplicationDocsType_Lookup_ID'] else ''
            desc = self.clean_string(row['ApplicationDocsType_Lookup_Description']
                                     ) if row['ApplicationDocsType_Lookup_Description'] else ""
            appl_doc_types.append((id, desc))

        self.insert_into_sqlite_table(
            appl_doc_types, "INSERT or IGNORE INTO %s VALUES (?,?)" % self.APPLICATION_DOC_TYPE.tablename)

    def insert_into_marketing_status(self, data):
        statuses = []
        for row in data:
            id = int(row['MarketingStatusID']
                     ) if row['MarketingStatusID'] else ''
            applNo = int(row['ApplNo']) if row['ApplNo'] else ''
            productNo = int(row['ProductNo']) if row['ProductNo'] else ''

            statuses.append((id, applNo, productNo))

        self.insert_into_sqlite_table(
            statuses, "INSERT or IGNORE INTO %s VALUES (?,?,?)" % self.MARKETING_STATUS.tablename)

    def insert_into_marketing_status_lookup(self, data):
        statuses_lookup = []

        for row in data:
            id = int(row['MarketingStatusID']
                     ) if row['MarketingStatusID'] else ''
            desc = self.clean_string(
                row['MarketingStatusDescription']) if row['MarketingStatusDescription'] else ''

            statuses_lookup.append((id, desc))

        self.insert_into_sqlite_table(
            statuses_lookup, "INSERT or IGNORE INTO %s VALUES (?,?)" % self.MARKETING_STATUS_LOOKUP.tablename)

    def insert_into_products(self, data):
        products = []
        for row in data:
            applNo = int(row['ApplNo']) if row['ApplNo'] else ''
            productNo = int(row['ProductNo']) if row['ProductNo'] else ''
            form = self.clean_string(row['Form']) if row['Form'] else ''
            strength = self.clean_string(
                row['Strength']) if row['Strength'] else ''
            refdrug = self.clean_string(
                row['ReferenceDrug']) if row['ReferenceDrug'] else ''
            drugName = self.clean_string(
                row['DrugName']) if row['DrugName'] else ''
            activeIngredient = self.clean_string(
                row['ActiveIngredient']) if row['ActiveIngredient'] else ''
            refstandard = self.clean_string(
                row['ReferenceStandard']) if row['ReferenceStandard'] else ''

            products.append((applNo, productNo, form, strength, refdrug,
                             drugName, activeIngredient, refstandard))

        self.insert_into_sqlite_table(
            products, "INSERT or IGNORE INTO %s VALUES (?,?,?,?,?,?,?,?)" % self.PRODUCT.tablename)

    def insert_into_submission_class_lookup(self, data):
        submission_class = []
        for row in data:
            id = int(row['SubmissionClassCodeID']
                     ) if row['SubmissionClassCodeID'] else ''
            code = self.clean_string(
                row['SubmissionClassCode']) if row['SubmissionClassCode'] else ''
            desc = self.clean_string(
                row['SubmissionClassCodeDescription']) if row['SubmissionClassCodeDescription'] else ''

            submission_class.append((id, code, desc))
        self.insert_into_sqlite_table(
            submission_class, "INSERT or IGNORE INTO %s VALUES (?,?,?)" % self.SUBMISSION_CLASS.tablename)

    def insert_into_submissions(self, data):
        submissions = []
        for row in data:
            applNo = int(row['ApplNo']) if row['ApplNo'] else ''
            subclasscodeId = int(
                row['SubmissionClassCodeID']) if row['SubmissionClassCodeID'] else ''
            subType = self.clean_string(
                row['SubmissionType']) if row['SubmissionType'] else ''
            subNo = int(row['SubmissionNo']) if row['SubmissionNo'] else ''
            subStatus = self.clean_string(
                row['SubmissionStatus']) if row['SubmissionStatus'] else ''
            subDate = self.clean_string(
                row['SubmissionStatusDate']) if row['SubmissionStatusDate'] else ''
            subPublicNotes = self.clean_string(
                row['SubmissionsPublicNotes']) if row['SubmissionsPublicNotes'] else ''
            reviewPriority = self.clean_string(
                row['ReviewPriority']) if row['ReviewPriority'] else ''

            submissions.append((applNo, subclasscodeId, subType, subNo,
                                subStatus, subDate, subPublicNotes, reviewPriority))

        self.insert_into_sqlite_table(
            submissions, "INSERT or IGNORE INTO %s VALUES (?,?,?,?,?,?,?,?)" % self.SUBMISSION.tablename)

    def insert_into_submission_property_type(self, data):
        submission_property_types = []
        for row in data:
            applNo = int(row['ApplNo']) if row['ApplNo'] else None
            submissionType = self.clean_string(
                row['SubmissionType']) if row['SubmissionType'] else None
            submissionNo = int(row['SubmissionNo']
                               ) if row['SubmissionNo'] else None
            submissionTypeCode = self.clean_string(
                row['SubmissionPropertyTypeCode']) if row['SubmissionPropertyTypeCode'] else None
            submissionPropertyTypeID = int(
                row['SubmissionPropertyTypeID']) if row['SubmissionPropertyTypeID'] else None

            submission_property_types.append((applNo, submissionType, submissionNo, submissionTypeCode,
                                              submissionPropertyTypeID))

        self.insert_into_sqlite_table(
            submission_property_types, "INSERT or IGNORE INTO %s VALUES (?,?,?,?,?)" % self.SUBMISSION_PROPERTY_TYPE.tablename)

    def insert_into_te(self, data):
        te_data = []
        for row in data:
            #ApplNo	ProductNo	MarketingStatusID	TECode
            applNo = int(row['ApplNo']) if row['ApplNo'] else None
            productNo = int(row['ProductNo']) if row['ProductNo'] else None
            marketing_status_id = int(
                row['MarketingStatusID']) if row['MarketingStatusID'] else None
            te = self.clean_string(row['TECode']) if row['TECode'] else None

            te_data.append((applNo, productNo, marketing_status_id, te))

        self.insert_into_sqlite_table(
            te_data, "INSERT or IGNORE INTO %s VALUES (?,?,?,?)" % self.TE.tablename)

    #endregion

    # region get
    def get_products(self, application_no):
        ## fill following data
        # get product information
        product_sql = """select distinct  p.drugName 'drug_name', p.activeIngredient 'active_substance', p.strength strength, p.form 'dosage_form', x.description as 'marketing_status', (case when te.teCode is NULL then 'None' else te.teCode end)  'therapeutic_equivalence_codes',
                (case when p.referenceDrug is '1' then 'Yes' else 'No' end) 'reference_drug',
                (case when p.referenceStandard is '1' then 'Yes' else 'No' end) 'reference_standard',
                p.productNo as 'product_number'
                from {product_tbl} p 
                        left join(select ms.id, ms.applNo, ms_lkp.description, ms.productNo from {marketing_status_tbl} ms
                        left join {marketing_status_lkp_tbl} ms_lkp on ms.id=ms_lkp.id) x
                on p.applNo = x.applNo and p.productNo = x.productNo
                left join {te_tbl} on p.applNo = te.applNo and p.productNo = te.productNo 
                where p.applNo = {applNo}

                """

        product_sql = (product_sql.format(product_tbl=self.PRODUCT.tablename,
                                          marketing_status_tbl=self.MARKETING_STATUS.tablename,
                                          marketing_status_lkp_tbl=self.MARKETING_STATUS_LOOKUP.tablename,
                                          te_tbl=self.TE.tablename, applNo=application_no))

        product_rows = self.get_rows(product_sql)

        products = []
        for row in product_rows:
            item = dict(row)
            product_info = {}
            for k, v in item.items():
                if k not in product_info:
                    product_info[k] = set()
                if v is not None:
                    product_info[k].add(v)
            product_info = (dict([(k, v.pop()) if len(v) == 1 else(
                k, list(v)) for k, v in product_info.items()]))
            products.append(product_info)

        return products

    def get_submission(self, application_no, application_doc_type_id, submission_no):
        ## supplement information query
        submission_sql = """
        select distinct 
		sub_class_lkp.submissionClassCode approvalTypeCode,
		sub_class_lkp.submissionClassDescription approvalType,
		sub.subStatus submissionStatus,
		docs.docsTypeId documentTypeId,
		docs.docTypeDesc documentTypeDesc,
		date(sub.subDate) yearOfAuthorization,
		sub.subPublicNotes submissionNotes,
		sub.reviewPriority reviewPriority ,
        (case when sub_prop_type.submissionPropertyTypeCode is NULL then '' when sub_prop_type.submissionPropertyTypeCode is 'Null' then '' else sub_prop_type.submissionPropertyTypeCode end) orphanDesignation,
        sub.subType as submissionType

        from {submission_tbl} sub  left join {submission_class_lkp_tbl} sub_class_lkp on sub.subclasscodeId = sub_class_lkp.id
        left join {submission_property_type_tbl} sub_prop_type on sub.applNo = sub_prop_type.applNo and sub.subNo = sub_prop_type.submissionNo
        inner join (select docs.id,docs.submissionNo, docsTypeId, docs_lkp.description docTypeDesc, applNo, submissionType, applicationDocsTitle, applicationDocsURL, applicationDocsDate, description from {application_docs_tbl} docs
        left join {application_docs_type_lookup_tbl} docs_lkp on docs.docsTypeId = docs_lkp.id) docs on docs.applNo = sub.applNo and docs.submissionNo = sub.subNo 
        where sub.applNo = {applNo} and sub.subNo = {subNo} and docsTypeId={docsTypeId}
        """
        submission_sql = submission_sql.format(submission_tbl=self.SUBMISSION.tablename, submission_class_lkp_tbl=self.SUBMISSION_CLASS.tablename, submission_property_type_tbl=self.SUBMISSION_PROPERTY_TYPE.tablename,
                                               application_docs_tbl=self.APPLICATION_DOC.tablename, application_docs_type_lookup_tbl=self.APPLICATION_DOC_TYPE.tablename, applNo=application_no,
                                               subNo=submission_no,
                                               docsTypeId=application_doc_type_id)

        submission_row = self.get_row(submission_sql)
        if submission_row is not None and len(submission_row) > 0:
            submission_info = dict(submission_row)
        else:
            submission_info = {}

        return submission_info

    def get_application(self, application_no):
        """ Function to retrieve application information from application table
        Args:
            application_no (int): application no

        Returns:
            [type]: [description]
        """
        application_sql = "select * from {table_name} where applNo = {application_no} ".format(table_name=self.APPLICATION.tablename,
                                                                                               application_no=application_no)

        application_row = self.get_row(application_sql)

        if application_row is not None and len(application_row) > 0:
            application_info = dict(application_row)

            ## map application doc type
            application_info['documentType'] = self.APPLICATION_TYPE_MAPPING.get(
                application_info['applType'], '')

        else:
            application_info = {}

        return application_info

    # endregion

    #region helpers

    def insert_into_sqlite_table(self, data, sql):
        self.cursor.executemany(sql, data)
        self.conn.commit()

    def read_metadata_file(self, filepath, aws_env=True):
        """Read data

        Args:
            filepath ([type]): [description]

        Returns:
            reader: return dictionary reader
        """
        if not aws_env:
            if os.path.exists(filepath):
                rows = []
                with open(filepath, 'r', encoding='windows-1252') as f:
                    reader = csv.DictReader(
                        f, delimiter='\t', quoting=csv.QUOTE_NONE)
                    for row in reader:
                        rows.append(row)
                    return rows

        response = read_obj_from_bucket(filepath)

        # split the contents of the file
        content = response['Body'].read().decode('windows-1252')
        lines = content.split("\n")
        self.logger.info(
            f"read from s3: {filepath}, number of lines:{len(lines)}")
        rows = []
        reader = csv.DictReader(lines, delimiter='\t', quoting=csv.QUOTE_NONE)
        for row in reader:
            rows.append(row)

        return rows

    def check_table_exists(self, table_name):
        """Method to check if the table exists

        Args:
            table_name : name of the table

        Returns:
            1 if table else exists otherwise returns 0 if the table does not exists
        """
        return self.conn.execute("select count(*) from sqlite_master where type='table' and name=?", [table_name]).fetchone()[0]

    def drop_table(self, table_name):
        self.conn.execute("DROP TABLE [{}]".format(table_name))

    def get_total_rows(self, table_name):
        """Return total number of rows in the table

        Args:
            table_name (string): name of the table
        """
        count = self.conn.execute(
            'select count(*) from "{}"'.format(table_name)).fetchone()[0]
        self.logger.info("<{}: {} rows>".format(table_name, count))
        return count

    ## Get sqlite row to the dictionary
    def sqlite_dict(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    @classmethod
    def clean_string(self, s):
        bad_chars = [":", ";"]
        s = s.rstrip(os.linesep)
        return s.strip()

    ## extract from nested dictionary
    def extract_from_dict(self, my_key, dictionary_items):
        found_value = ''
        for key, value in dictionary_items.items():
            if type(value) is dict:
                self.extract_from_dict(my_key, value)
            else:
                if key == my_key:
                    found_value = value

        return found_value

    #endregion
