#!/usr/bin/env python

import os
import json
import sqlite3
import traceback
from functools import reduce
## replace with cloudwatch
import logging
from utils import load_log_config


from collections import namedtuple

META_DATA_ITEM = namedtuple("META_DATA_ITEM", 'tablename filename')

# initialize logging - globally
load_log_config()

class FDAAPI(object):
    """
    FDA class to extract data from the document

    Args:
        object ([type]): [description]
    """
    #region metadata_info

    APPLICATION = META_DATA_ITEM('application', 'Applications.txt')
    ACTION_TYPE = META_DATA_ITEM('actionType', 'ActionTypes_Lookup.txt')
    APPLICATION_DOC = META_DATA_ITEM(
        'applicationDoc', 'ApplicationDocs.txt')

    APPLICATION_DOC_TYPE = META_DATA_ITEM(
        'applicationDocType', 'ApplicationsDocsType_Lookup.txt')
    MARKETING_STATUS = META_DATA_ITEM(
        'marketingStatus', 'MarketingStatus.txt')
    MARKETING_STATUS_LOOKUP = META_DATA_ITEM('marketingStatusLookup', 'MarketingStatus_Lookup.txt')
    PRODUCT = META_DATA_ITEM('product', 'Products.txt')
    SUBMISSION_CLASS = META_DATA_ITEM(
        'submissionClass', 'SubmissionClass_Lookup.txt')
    SUBMISSION_PROPERTY_TYPE = META_DATA_ITEM(
        'submissionPropertyType', 'SubmissionPropertyType.txt')
    SUBMISSION = META_DATA_ITEM('submission', 'Submissions.txt')
    TE = META_DATA_ITEM('te','TE.txt')

    #endregion

    def __init__(self, **kwargs):
        metadata_folder_loc = kwargs.get('S3_metadata_loc', '')

        if metadata_folder_loc is None:
            raise Exception("Metadata location was not specified!")

        self.metadata_folder_loc = metadata_folder_loc
        self.engine_url = ":memory:"
        
        # setup logger
        self.logger = logging.getLogger('process_batch')
        self.conn = self.create_connection()
        result = self.create_tables()

        # if result - insert metadata
        if result:
            self.insert_metadata()

    def create_connection(self):
        """create database connection to the SQLite database specified by db_file location
        
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(self.engine_url)
            conn.row_factory = sqlite3.Row  # getting the column names
        except Exception as e:
            self.logger.error("error creating connection", e)

        return conn

    def create_tables(self):
        number_of_tables = 0
        conn = self.conn
        try:
            # open connection
            # Action Types
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, description	TEXT, supplCategoryLevel1Code TEXT,supplCategoryLevel2Code TEXT, PRIMARY KEY(id))" % self.ACTION_TYPE.tablename)
            number_of_tables += 1
            
            # ApplicationDocs
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, docsTypeId	INTEGER, applNo	INTEGER, submissionType	TEXT, submissionNo	INTEGER, applicationDocsTitle	TEXT, applicationDocsURL	TEXT, applicationDocsDate	TEXT);" % self.APPLICATION_DOC.tablename)
            number_of_tables += 1

            # Application table
            conn.execute("CREATE TABLE if not exists %s ( applNo integer, applType text, applPublicNotes text, sponsorName text);" % self.APPLICATION.tablename)
            number_of_tables += 1

            # ApplicationDocsType_Lookup table
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, description TEXT);" % self.APPLICATION_DOC_TYPE.tablename)
            number_of_tables += 1

            # Marketing status
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, applNo	INTEGER, productNo	INTEGER);" % self.MARKETING_STATUS.tablename)
            number_of_tables += 1

            # Marketing status lookup
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, description	TEXT);" %
                        self.MARKETING_STATUS_LOOKUP.tablename)
            number_of_tables += 1

            # Products
            conn.execute("CREATE TABLE if not exists %s (applNo	INTEGER, productNo	INTEGER, form	TEXT, strength	TEXT,referenceDrug	TEXT, drugName	TEXT, activeIngredient	TEXT, referenceStandard	TEXT); " % self.PRODUCT.tablename)
            number_of_tables += 1

            # Submission Class Lookup
            conn.execute("CREATE TABLE if not exists %s (id	INTEGER, submissionClassCode	TEXT,submissionClassDescription	TEXT);" % self.SUBMISSION_CLASS.tablename)
            number_of_tables += 1

            # Submission Property Type
            conn.execute("CREATE TABLE if not exists %s (applNo	INTEGER, submissionType	TEXT, submissionNo	INTEGER,submissionPropertyTypeCode	TEXT, SubmissionPropertyTypeID	TEXT);" % self.SUBMISSION_PROPERTY_TYPE.tablename)
            number_of_tables += 1

            # Submissions
            conn.execute("CREATE TABLE if not exists %s (applNo INTEGER, subclasscodeId	INTEGER, subType	TEXT,subNo	INTEGER, subStatus	TEXT, subDate	TEXT, subPublicNotes	TEXT, reviewPriority	TEXT);" %
                        self.SUBMISSION.tablename)
            number_of_tables += 1

            # TE
            conn.execute("CREATE TABLE if not exists %s (applNo	INTEGER, productNo	INTEGER, marketingStatusId	INTEGER,teCode	TEXT);" %self.TE.tablename)
            number_of_tables += 1

            # commit
            conn.commit()
                
        except Exception as ex:
            tb = traceback.format_exc()
            self.logger.error(tb)
            self.logger.exception('Exception occurred')
            
        ## names of the table that are created
        query = "SELECT tbl_name FROM sqlite_master WHERE type='table'"
        rows = self.conn.execute(query).fetchall()
        for row in rows:
            self.logger.info("table created: %s" % row)

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

    def insert_metadata(self):
        """
        insert metadata
        """
        ## ActionTypes
        self.insert_action_type(self.read_metadata_file(os.path.join(
            self.metadata_folder_loc, self.ACTION_TYPE.filename)))
        
        print("inserted into action type")
        ## ApplicationDocs
        self.insert_into_appl_docs(self.read_metadata_file(os.path.join(self.metadata_folder_loc, self.APPLICATION_DOC.filename)))
        print("inserted into application docs")

        ## Applications
        self.insert_into_appl(self.read_metadata_file(os.path.join(self.metadata_folder_loc, self.APPLICATION.filename)))
        print("inserted into applications")


        ## application doc type
        self.insert_into_appl_docs_type(self.read_metadata_file(os.path.join(self.metadata_folder_loc, self.APPLICATION_DOC_TYPE.filename)))
        print("inserted into application doc type")
        
        ## marketing 
        self.insert_into_marketing_status(self.read_metadata_file(
            os.path.join(self.metadata_folder_loc, self.MARKETING_STATUS.filename)))
        
        ## marketing status
        self.insert_into_marketing_status_lookup(self.read_metadata_file(os.path.join(self.metadata_folder_loc, self.MARKETING_STATUS_LOOKUP.filename)))

        ## products
        self.insert_into_products(self.read_metadata_file(os.path.join(self.metadata_folder_loc, self.PRODUCT.filename)))

        ## submission class lookup
        self.insert_into_submission_class_lookup(self.read_metadata_file(os.path.join(self.metadata_folder_loc, self.SUBMISSION_CLASS.filename)))

        ## submission property type
        self.insert_into_submission_property_type(self.read_metadata_file(os.path.join(self.metadata_folder_loc, self.SUBMISSION_PROPERTY_TYPE.filename)))

        # submissions
        self.insert_into_submissions(self.read_metadata_file(os.path.join(self.metadata_folder_loc, self.SUBMISSION.filename)))

        # te
        self.insert_into_te(self.read_metadata_file(os.path.join(self.metadata_folder_loc,self.TE.filename)))

    
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
        
        response = {}
        response["applicationNo"] = kwargs.get("applicationNo","")
        response["supplementType"] = kwargs.get("supplementType","")
        response["supplementNo"] = kwargs.get("supplementNo","")
        response["applicationDocTypeId"] = kwargs.get("applicationDocTypeId","")
    

        ## fill following data
        # get product information
        product_sql = """select distinct p.applNo ApplicationNo, p.drugName DrugName, p.activeIngredient ActiveIngredient, p.strength Strength, p.form Form, x.description as 'MarketingStatus',
                            (case when te.teCode is NULL then 'None' else te.teCode end)  TECode,
                (case when p.referenceDrug is '1' then 'Yes' else 'No' end) ReferenceListedDrug,
                (case when p.referenceStandard is '1' then 'Yes' else 'No' end) ReferenceStandard from product p 
                left join(select ms.id, ms.applNo, ms_lkp.description, ms.productNo from marketingStatus ms
                        left join marketingStatusLookup ms_lkp on ms.id=ms_lkp.id) x
                on p.applNo = x.applNo and p.productNo = x.productNo
                left join te on p.applNo = te.applNo and p.productNo = te.productNo where p.applNo = {applNo}
                """
        product_sql = (product_sql.format(
            applNo=kwargs.get("applicationNo", "")))
        
        product_rows = self.get_rows(product_sql)
        product_info = {}
        for row in product_rows:
            item = dict(row)        
            for k, v in item.items():
                if k not in product_info:
                    product_info[k] = set()
                
                if v is not None:
                    product_info[k].add(v)

        ##TODO change code
        for k, v in product_info.items():
            if len(v) == 1:
                product_info[k] = v.pop()
            else:
                product_info[k] = list(v)
        # {'ApplicationNo': 4782, 'DrugName': 'PREMARIN', 'ActiveIngredient': 'ESTROGENS, CONJUGATED', 'Strength': ['0.3MG', '2.5MG', '0.625MG', '1.25MG', '0.45MG', '0.9MG'], 'Form': 'TABLET;ORAL', 'MarketingStatus': ['Discontinued\n', 'Prescription\n'], 'TECode': 'None', 'ReferenceListedDrug': ['No', 'Yes'], 'ReferenceStandard': 'No'}
        print(product_info)
        
        ## supplement information query
        supplement_sql =
        """
        select  sub.subNo SubmissionNo,
		sub.applNo ApplicationNo,
		sub_class_lkp.submissionClassCode ApprovalTypeCode,
		sub_class_lkp.submissionClassDescription ApprovalType,
		sub.subStatus SubmissionStatus,
		docs.docsTypeId DocumentTypeId,
		docs.docTypeDesc DocumentTypeDesc,
		sub.subDate ActionDate,
		sub.subPublicNotes SubmissionNotes,
		sub.reviewPriority ReviewPriority ,
        (case when sub_prop_type.submissionPropertyTypeCode is NULL then '' when sub_prop_type.submissionPropertyTypeCode is 'Null' then '' else sub_prop_type.submissionPropertyTypeCode end) OrphanDesignation
        from submissions sub  left join submission_class_lookup sub_class_lkp on sub.subclasscodeId = sub_class_lkp.id
        left join submission_property_type sub_prop_type on sub.applNo = sub_prop_type.applNo and sub.subNo = sub_prop_type.submissionNo
        inner join (select docs.id,docs.submissionNo, docsTypeId, docs_lkp.description docTypeDesc, applNo, submissionType, applicationDocsTitle, applicationDocsURL, applicationDocsDate, description from application_docs docs
        left join application_docs_type_lookup docs_lkp on docs.docsTypeId = docs_lkp.id) docs on docs.applNo = sub.applNo and docs.submissionNo = sub.subNo 
        where sub.applNo = {applNo},
        
        """



    #region private methods to insert data
    def insert_action_type(self, data):
        types=[]
        ids = []

        for row in data:
            id=int(row[0])
            desc=row[1] if row[1] else ""
            code1=row[2] if row[2] else ""
            code2=row[3] if row[3] else ""
            if id not in ids:
                ids.append(id)
            else:
                print("id exists", id)
            types.append((id, desc, code1, code2))
        
        self.insert_into_sqlite_table(types, "INSERT or IGNORE INTO %s VALUES (?,?,?,?)"% self.ACTION_TYPE.tablename)
        print("inserted into action type table")

    def insert_into_appl_docs(self, data):
        docs  = []
        for row in data:
            id = int(row[0])
            docTypeId = int(row[1]) if row[1] else None
            applNo = int(row[2]) if row[2] else None
            subtype = row[3] if row[3] else ""
            subno = int(row[4]) if row[4] else ""
            appDocTitle = row[5] if row[5] else ""
            applDocUrl = row[6] if row[6] else ""
            applDate = row[7] if row[7] else ""

            docs.append((id, docTypeId, applNo, subtype, subno,
                          appDocTitle, applDocUrl, applDate))

        self.insert_into_sqlite_table(
            docs, "INSERT or IGNORE INTO %s VALUES (?,?,?,?,?,?,?,?)" % self.APPLICATION_DOC.tablename)

    def insert_into_appl(self, data):
        applications = []

        for row in data:
            #ApplNo	ApplType ApplPublicNotes SponsorName
            applNo = int(row[0]) if row[0] else None
            appltype = row[1] if row[1] else ""
            applPublicNotes = row[2] if row[2] else ""
            sponsorName = row[3] if row[3] else ""

            applications.append((applNo, appltype, applPublicNotes,
                              sponsorName))

        self.insert_into_sqlite_table(
            applications, "INSERT or IGNORE INTO %s VALUES (?,?,?,?)" % self.APPLICATION.tablename)

    def insert_into_appl_docs_type(self, data):
        appl_doc_types = []
        
        for row in data:
            id = int(row[0]) if row[0] else None
            desc = row[1] if row[1] else ""
            appl_doc_types.append((id,desc))

        self.insert_into_sqlite_table(
            appl_doc_types, "INSERT or IGNORE INTO %s VALUES (?,?)" % self.APPLICATION_DOC_TYPE.tablename)
    
    def insert_into_marketing_status(self, data):
        statuses = []
        for row in data:
            id = int(row[0]) if row[0] else None
            applNo = int(row[1]) if row[1] else None
            productNo = int(row[2]) if row[2] else None
            
            statuses.append((id, applNo, productNo))

        self.insert_into_sqlite_table(statuses, "INSERT or IGNORE INTO %s VALUES (?,?,?)" % self.MARKETING_STATUS.tablename)

    def insert_into_marketing_status_lookup(self, data):
        statuses_lookup = []

        for row in data:
            id = int(row[0]) if row[0] else None
            desc = row[1] if row[1] else None

            statuses_lookup.append((id, desc))

        self.insert_into_sqlite_table(
            statuses_lookup, "INSERT or IGNORE INTO %s VALUES (?,?)" % self.MARKETING_STATUS_LOOKUP.tablename)

    def insert_into_products(self, data):
        products = []
        for row in data:
            applNo = int(row[0]) if row[0] else None
            productNo = int(row[1]) if row[1] else None
            form = row[2] if row[2] else None
            strength = row[3] if row[3] else None
            refdrug = row[4] if row[4] else None
            drugName = row[5] if row[5] else None
            activeIngredient = row[6] if row[6] else None
            refstandard = row[7] if row[7] else None

            products.append((applNo, productNo, form, strength, refdrug,
                          drugName, activeIngredient, refstandard))

        self.insert_into_sqlite_table(
            products, "INSERT or IGNORE INTO %s VALUES (?,?,?,?,?,?,?,?)" % self.PRODUCT.tablename)

    def insert_into_submission_class_lookup(self, data):
        submission_class = []
        for row in data:
            id = int(row[0]) if row[0] else None
            code = (row[1]) if row[1] else None
            desc = row[2] if row[2] else None

            submission_class.append((id, code, desc))
        self.insert_into_sqlite_table(
            submission_class, "INSERT or IGNORE INTO %s VALUES (?,?,?)" % self.SUBMISSION_CLASS.tablename)

    def insert_into_submissions(self, data):
        submissions = []
        for row in data:
            applNo = int(row[0]) if row[0] else None
            subclasscodeId = int(row[1]) if row[1] else None
            subType = row[2] if row[2] else None
            subNo = int(row[3]) if row[3] else None
            subStatus = row[4] if row[4] else None
            subDate = row[5] if row[5] else None
            subPublicNotes = row[6] if row[6] else None
            reviewPriority = row[7] if row[7] else None

            submissions.append((applNo, subclasscodeId, subType, subNo, subStatus, subDate, subPublicNotes, reviewPriority))

        self.insert_into_sqlite_table(submissions, "INSERT or IGNORE INTO %s VALUES (?,?,?,?,?,?,?,?)" % self.SUBMISSION.tablename)

    def insert_into_submission_property_type(self, data):
        submission_property_types = []
        for row in data:
            applNo = int(row[0]) if row[0] else None
            submissionType = (row[1]) if row[1] else None
            submissionNo = int(row[2]) if row[2] else None
            submissionTypeCode = row[3] if row[3] else None
            submissionPropertyTypeID = int(row[4]) if row[4] else None
            
            submission_property_types.append((applNo, submissionType, submissionNo, submissionTypeCode,
                            submissionPropertyTypeID))

        self.insert_into_sqlite_table(
            submission_property_types, "INSERT or IGNORE INTO %s VALUES (?,?,?,?,?)" % self.SUBMISSION_PROPERTY_TYPE.tablename)

    def insert_into_te(self, data):
        te_data = []
        for row in data:
            #ApplNo	ProductNo	MarketingStatusID	TECode
            applNo = int(row[0]) if row[0] else None
            productNo = int(row[1]) if row[1] else None
            marketing_status_id = int(row[2]) if row[2] else None
            te = row[3] if row[3] else None
            
            te_data.append((applNo, productNo, marketing_status_id, te))

        self.insert_into_sqlite_table(
            te_data, "INSERT or IGNORE INTO %s VALUES (?,?,?,?)" % self.TE.tablename)

    #endregion

    #region helpers
    def insert_into_sqlite_table(self, data, sql):
        conn = self.conn
        conn.cursor().executemany(sql, data)
        conn.commit()

    def read_metadata_file(self, filepath):
        rows = []
        split_line_into_words = lambda line: [w for w in line.split("\t")]

        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                for index, line in enumerate(f.readlines()):
                    data = split_line_into_words(line)
                    rows.append(data)
        return rows[1:] # ignore header

    def check_table_exists(self, tablename):
        return self.conn.execute("select count(*) from sqlite_master where type='table' and name=?", [tablename]).fetchone()[0]
    
    def drop_table(tablename):
        self.conn.execute("DROP TABLE [{}]".format(tablename))

    def get_total_rows(self, table_name):
        """Return total number of rows in the table

        Args:
            table_name (string): name of the table
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT Count(*) from {}".format(table_name))
        count = cursor.fetchall()
        print("\n Total rows:{}".format(count[0][0]))
        return count[0][0]
    
    
    ## Get sqlite row to the dictionary
    def sqlite_dict(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    #endregion


api = FDAAPI(S3_metadata_loc=os.path.join("data", "metadata"))
api.format_response(applicationNo=4782)
