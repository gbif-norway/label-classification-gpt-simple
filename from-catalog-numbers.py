from helpers.api_gcv_ocr import detect_text_from_url, process_image_from_url
from helpers.api_annotater import annotate, delete_annotation, get_first_annotation
from helpers.api_openai import gpt_standardise_text
from helpers.dwc_parser import norway_date_parse
from helpers.dwc_parser import norway_text_exclusion
from helpers.api_gbif import get_smallest_img_from_gbif
import pandas as pd
import yaml
import re
import csv
import os

with open('helpers/prompt.txt') as prompt, open('helpers/function.yml') as function:
    prompt = prompt.read()
    function = yaml.safe_load(function.read())
    model = 'gpt-3.5-turbo'

results = {}
with open('input/catalog_numbers.txt') as file, open('output-append.csv', 'a', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=['catalogNumber', 'imgurl', 'verbatimLabel', 'eventDate'] + list(function['function']['parameters']['properties'].keys()))
    writer.writeheader()
    i = 0
    
    for catalog in file:
        print(f'----{i}----')
        catalog = catalog.strip() + '/1'
        occurrence_id = os.getenv('OCCURENCE_ID_PREFIX') + catalog
        url = get_smallest_img_from_gbif(catalog)
        # ocr = get_first_annotation(f'resolvable_object_id={occurrence_id}&source=gcv_ocr_text')
        # if ocr:
            # ocr_text = ocr['annotation']
        # else:
        print(f'{catalog} - {url}')
        # ocr = detect_text_from_url(url)
        ocr_text, ocr_pages = process_image_from_url(url)
        print(f'detected text: {ocr_text}')
        annotate(id=occurrence_id, source='gcv_ocr_pages', notes=url, annotation=ocr_pages)
        annotate(id=occurrence_id, source='gcv_ocr_text', notes=url, annotation=ocr_text)
        # flat = flatten(ocr['pages'])
        # annotate(id=occurrence_id, source='gcv_ocr_flat', notes=url, annotation=flat)
        ocr_text = ocr_text

        ocr_text = norway_text_exclusion(ocr_text, 'O-B-', catalog)

        gpt = gpt_standardise_text(ocr_text, prompt, function, model)
        annotate(id=occurrence_id, source=model, notes='', annotation=gpt)

        if 'verbatimDateCollected' in gpt:
            gpt['eventDate'] = norway_date_parse(gpt['verbatimDateCollected'])

        if 'isExsiccata' not in gpt:
            if 'xsiccata' in ocr_text.lower():
                gpt['isExsiccata'] = 'true'
        
        if 'verbatimCollectors' in gpt:
            gpt['verbatimCollectors'] = re.sub(r'leg\.?\s*', '', gpt['verbatimCollectors'], flags=re.IGNORECASE)
        results[catalog] = {**{'verbatimLabel':ocr_text, 'imgurl': url}, **gpt}
        writer.writerow({**{'catalogNumber': catalog}, **results[catalog]})
        i += 1
        
df = pd.DataFrame.from_dict(results, orient='index')
df.to_csv('output.csv')
import pdb; pdb.set_trace()
