import requests
from helpers.api_annotater import get_annotations_filtered
import pandas as pd

annotations = pd.DataFrame(get_annotations_filtered('created_date_gt=2023-11-25&source=gpt-4')).drop_duplicates(subset='resolvable_object_id')
ocrs =  pd.DataFrame(get_annotations_filtered('created_date_gt=2023-11-25&source=gcv_ocr_text')).drop_duplicates(subset='resolvable_object_id')

with open('input/catalog_numbers.txt') as file:
    file_ids = ['urn:catalog:O:V:' + line.strip() for line in file]

missing_ids = [id for id in file_ids if id not in annotations['resolvable_object_id'].values]

annotations_expanded = annotations[['resolvable_object_id']].join(pd.json_normalize(annotations['annotation']))
ocrs_annotation = ocrs[['resolvable_object_id', 'annotation']].rename(columns={'annotation': 'ocr'})
result_df = pd.merge(ocrs_annotation, annotations_expanded, on='resolvable_object_id')

result_df['verbatimRecordedBy'] = result_df['verbatimRecordedBy'].fillna(result_df['verbatimCollectors'])
result_df['verbatimLocality'] = result_df['verbatimLocality'].fillna(result_df['verbatimLocationCollected'])
result_df['verbatimEventDate'] = result_df['verbatimEventDate'].fillna(result_df['verbatimDateCollected'])
result_df['occurrenceRemarks'] = result_df['occurrenceRemarks'].fillna(result_df['verbatimHerbarium'])
result_df.drop(columns=['verbatimCollectors', 'verbatimLocationCollected', 'verbatimDateCollected', 'verbatimHerbarium'], inplace=True)

columns = result_df.columns.tolist()
verbatim_columns = [col for col in columns if col.startswith('verbatim')]
other_columns = [col for col in columns if col not in verbatim_columns and col not in ['resolvable_object_id', 'ocr', 'isExsiccata', 'isExHerb', 'occurrenceRemarks']]
new_order = ['resolvable_object_id', 'ocr'] + verbatim_columns + ['isExsiccata', 'isExHerb', 'occurrenceRemarks'] + other_columns
reordered = result_df[new_order]

import pdb; pdb.set_trace()
reordered.to_csv('output-from-api.csv')
