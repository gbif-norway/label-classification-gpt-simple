from helpers.api_gcv_ocr import detect_text
from helpers.api_annotater import annotate, delete_annotation, get_first_annotation
from helpers.api_openai import gpt_standardise_text
from helpers.date_parser import custom_date_parse
from helpers.custom import text_exclusion
from helpers.api_gbif import get_smallest_img_from_gbif
import pandas as pd
import yaml
import re
import csv


with open('helpers/prompt.txt') as prompt, open('helpers/function.yml') as function:
    prompt = prompt.read()
    function = yaml.safe_load(function.read())

results = {}
with open('input/catalog_numbers.txt') as file, open('output-append.csv', 'a', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=['catalogNumber', 'imgurl', 'verbatimLabel', 'eventDate'] + list(function['function']['parameters']['properties'].keys()))
    writer.writeheader()
    i = 0
    
    for catalog in file:
        print(f'----{i}----')
        catalog = catalog.strip()
        occurrence_id = 'urn:catalog:O:V:' + catalog
        url = get_smallest_img_from_gbif(catalog, 'e45c7d91-81c6-4455-86e3-2965a5739b1f')
        ocr = get_first_annotation(f'resolvable_object_id={occurrence_id}&source=gcv_ocr_text')
        if ocr:
            ocr_text = ocr['annotation']
        else:
            print(f'{catalog} - {url}')
            ocr = detect_text(url)
            print(f'detected text: {ocr["text"]}')
            annotate(id=occurrence_id, source='gcv_ocr_pages', notes=url, annotation=ocr['pages'])
            annotate(id=occurrence_id, source='gcv_ocr_text', notes=url, annotation=ocr['text'])
            flat = flatten(ocr['pages'])
            annotate(id=occurrence_id, source='gcv_ocr_flat', notes=url, annotation=flat)
            ocr_text = ocr['text']

        ocr_text = text_exclusion(ocr_text)

        gpt = gpt_standardise_text(ocr_text, prompt, function, 'gpt-3.5-turbo-1106')
        annotate(id=occurrence_id, source='gpt-4', notes=ocr['id'], annotation=gpt)

        if 'verbatimDateCollected' in gpt:
            gpt['eventDate'] = custom_date_parse(gpt['verbatimDateCollected'])

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
