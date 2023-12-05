import requests
from helpers.api_annotater import get_annotations_filtered
import pandas as pd

annotations = pd.DataFrame(get_annotations_filtered('created_date_gt=2023-11-25&source=gpt-4')).drop_duplicates(subset='resolvable_object_id')
ocrs =  pd.DataFrame(get_annotations_filtered('created_date_gt=2023-11-25&source=gcv_ocr_text')).drop_duplicates(subset='resolvable_object_id')
df = annotations.merge(ocrs, on='resolvable_object_id', how='left')

with open('input/catalog_numbers.txt') as file:
    file_ids = [line.strip() for line in file]

missing_ids = [id for id in file_ids if id not in df['resolvable_object_id'].values]

import pdb; pdb.set_trace()
df.to_csv('output.csv')
