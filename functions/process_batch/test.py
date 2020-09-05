#!/usr/bin/env python

import os
app_file = "data/metadata/Applications.txt"

def read_metadata_file(filepath):
    rows = []
    def split_line_into_words(line): return [w for w in line.split("\t")]
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for index, line in enumerate(f.readlines()):
                data = split_line_into_words(line)
                rows.append(data)
    return rows[1:]  # ignore header

data = read_metadata_file(app_file)



product_info = [{'drug_name': 'PREMARIN', 'active_substance': 'ESTROGENS, CONJUGATED', 'strength': '1.25MG', 'dosage_form': 'TABLET;ORAL', 'marketing_status': 'Prescription', 'therapeutic_equivalence_codes': 'None', 'reference_drug': 'Yes', 'reference_standard': 'Yes', 'product_number': 1}, {'drug_name': 'PREMARIN', 'active_substance': 'ESTROGENS, CONJUGATED', 'strength': '2.5MG', 'dosage_form': 'TABLET;ORAL', 'marketing_status': 'Discontinued', 'therapeutic_equivalence_codes': 'None', 'reference_drug': 'No', 'reference_standard': 'No', 'product_number': 2}, {'drug_name': 'PREMARIN', 'active_substance': 'ESTROGENS, CONJUGATED', 'strength': '0.3MG', 'dosage_form': 'TABLET;ORAL', 'marketing_status': 'Prescription', 'therapeutic_equivalence_codes': 'None', 'reference_drug': 'Yes', 'reference_standard': 'No', 'product_number': 3}, {
    'drug_name': 'PREMARIN', 'active_substance': 'ESTROGENS, CONJUGATED', 'strength': '0.625MG', 'dosage_form': 'TABLET;ORAL', 'marketing_status': 'Prescription', 'therapeutic_equivalence_codes': 'None', 'reference_drug': 'Yes', 'reference_standard': 'Yes', 'product_number': 4}, {'drug_name': 'PREMARIN', 'active_substance': 'ESTROGENS, CONJUGATED', 'strength': '0.9MG', 'dosage_form': 'TABLET;ORAL', 'marketing_status': 'Prescription', 'therapeutic_equivalence_codes': 'None', 'reference_drug': 'Yes', 'reference_standard': 'Yes', 'product_number': 5}, {'drug_name': 'PREMARIN', 'active_substance': 'ESTROGENS, CONJUGATED', 'strength': '0.45MG', 'dosage_form': 'TABLET;ORAL', 'marketing_status': 'Prescription', 'therapeutic_equivalence_codes': 'None', 'reference_drug': 'Yes', 'reference_standard': 'No', 'product_number': 6}]


if len(product_info) > 0:
    values = set()
    for each in product_info:
        values.add(extract_from_dict(each, 'drug_name'))

print(values)
