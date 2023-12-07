import requests
from helpers.api_gcv_ocr import detect_text
from helpers.api_annotater import annotate, delete_annotation, get_first_annotation
from helpers.api_openai import gpt_standardise_text
import pandas as pd
import yaml
import re
import csv
from dateutil import parser
from datetime import datetime

norwegian_months = {
    "januar": "January",
    "februar": "February",
    "mars": "March",
    "april": "April",
    "mai": "May",
    "juni": "June",
    "juli": "July",
    "august": "August",
    "september": "September",
    "oktober": "October",
    "november": "November",
    "desember": "December"
}
roman_numerals = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12
}

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
    writer = csv.DictWriter(csvfile, fieldnames=['catalogNumber', 'imgurl', 'verbatimLabel', 'eventDate'] + list(function['function']['parameters']['properties'].keys()))
    writer.writeheader()
    i = 0
    model = 'gpt-3.5-turbo-instruct'
    
    for catalog in file:
        print(f'----{i}----')
        catalog = catalog.strip()
        occurrence_id = 'urn:catalog:O:V:' + catalog
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

        for_exclusion = [f'V {catalog}', '\\s*'.join(catalog), r'Herb. Oslo \(O\)', r'Herb. Univers. Osloensis', r'Herb. Univers. Osloënsis', r'Herb. Univers. Osloensis\s+\d\d\d\d', r'Herb. Univers. Osloënsis\s+\d\d\d\d', r'Planta Scandinavica', r'Flora Suecica', r'Flora Norvegica', r'Herb. Univers. Christianiensis.']
        for exclude in for_exclusion:
            ocr_text = re.sub(exclude, '', ocr_text, flags=re.IGNORECASE)

        gpt = gpt_standardise_text(ocr_text, prompt, function, model)
        annotate(id=occurrence_id, source='gpt-4', notes=ocr['id'], annotation=gpt)

        if 'verbatimDateCollected' in gpt:
            date = gpt['verbatimDateCollected']
            for key, value in norwegian_months.items():
                text = re.sub(key, str(value), date, flags=re.IGNORECASE)
            for key, value in roman_numerals.items():
                text = re.sub(key, str(value), date, flags=re.IGNORECASE)
            try:
                gpt['eventDate'] = parser.parse(date, default=datetime(1, 1, 1))
            except:
                pass
        if 'isExsiccata' not in gpt:
            if 'xsiccata' in ocr_text.lower():
                gpt['isExsiccata'] = 'true'
        results[catalog] = {**{'verbatimLabel':ocr_text, 'imgurl': url}, **gpt}
        writer.writerow({**{'catalogNumber': catalog}, **results[catalog]})
        i += 1
        
df = pd.DataFrame.from_dict(results, orient='index')
df.to_csv('output.csv')
import pdb; pdb.set_trace()
