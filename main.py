import requests
from helpers.api_gcv_ocr import detect_text
from helpers.api_annotater import annotate, delete_annotation
from helpers.api_openai import gpt_standardise_text
import pandas as pd
import yaml
import re
import csv


def get_smallest_img_from_gbif(catalog_number, dataset):
    params = { 'datasetKey': dataset, 'catalogNumber': catalog_number }
    response = requests.get('https://api.gbif.org/v1/occurrence/search', params=params)
    if response.status_code != 200:
        import pdb; pdb.set_trace()

    data = response.json()
    smallest_image_url = None
    smallest_size = float('inf')

    for record in data.get('results', []):
        for media in record.get('media', []):
            if media.get('type') == 'StillImage':
                image_url = media.get('identifier')
                try:
                    image_response = requests.get(image_url, stream=True)
                    image_size = len(image_response.content)
                    if image_size < smallest_size:
                        smallest_size = image_size
                        smallest_image_url = image_url
                except requests.RequestException as e:
                    print(f'Failed to get image {image_url}: {e}')

    return smallest_image_url

# for id in range(2497, 2552):
#     delete_annotation(id)

with open('helpers/prompt.txt') as prompt, open('helpers/function.yml') as function:
    prompt = prompt.read()
    function = yaml.safe_load(function.read())

results = {}
with open('input/catalog_numbers.txt') as file, open('output-append.csv', 'a', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=['catalogNumber', 'imgurl', 'verbatimLabel'] + list(function['function']['parameters']['properties'].keys()))
    writer.writeheader()
    i = 0
    
    for catalog in file:
        print(f'----{i}----')
        catalog = catalog.strip()
        url = get_smallest_img_from_gbif(catalog, 'e45c7d91-81c6-4455-86e3-2965a5739b1f')
        occurrence_id = 'urn:catalog:O:V:' + catalog
        print(f'{catalog} - {url}')
        ocr = detect_text(url)
        print(f'detected text: {ocr["text"]}')
        annotate(id=occurrence_id, source='gcv_ocr_pages', notes=url, annotation=ocr['pages'])
        annotate(id=occurrence_id, source='gcv_ocr_text', notes=url, annotation=ocr['text'])
        # flat = flatten(ocr['pages'])
        # annotate(id=occurrence_id, source='gcv_ocr_flat', notes=url, annotation=flat)

        for_exclusion = ['Herb. Oslo (O)', 'Herb. Univers. Osloensis', 'Herb. Univers. Osloënsis', 'Planta Scandinavica', 'Flora Suecica', 'Flora Norvegica']
        for exclude in for_exclusion:
            ocr['text'] = re.sub(re.escape(exclude), '', ocr['text'], flags=re.IGNORECASE)

            gpt = gpt_standardise_text(ocr['text'], prompt, function)
        annotate(id=occurrence_id, source='gpt-4', notes=url, annotation=gpt)
        results[catalog] = {**{'verbatimLabel': ocr['text'], 'imgurl': url}, **gpt}
        writer.writerow({**{'catalogNumber': catalog}, **results[catalog]})
        i += 1
        
df = pd.DataFrame.from_dict(results, orient='index')
df.to_csv('output.csv')
import pdb; pdb.set_trace()