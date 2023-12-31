import os
import json
import requests
from typing import Dict, Any


ANNOTATE_URI = 'https://annotater.svc.gbif.no/'
ANNOTATE_KEY = os.getenv('ANNOTATER_API_KEY')

def annotate(id, annotation, source, notes):
    headers = {'Authorization': f'Token {ANNOTATE_KEY}', 'Content-Type': 'application/json'}
    data = {'resolvable_object_id': id, 'annotation': annotation, 'source': source, 'notes': notes}
    response = requests.post(ANNOTATE_URI, headers=headers, json=data)
    return response.json()

def delete_annotation(id):
    headers = {'Authorization': f'Token {ANNOTATE_KEY}', 'Content-Type': 'application/json'}
    response = requests.delete(f'{ANNOTATE_URI}{id}', headers=headers)
    if response.status_code == 200 or response.status_code == 204:
        print("Successfully deleted.")
    else:
        print(f"Failed to delete. Status code: {response.status_code}, Response: {response.text}")

def get_first_annotation(filter_string):
    response = requests.get(ANNOTATE_URI + '?' + filter_string)
    data = response.json()
    return data['results'][0] if data['results'] else None

def get_annotations_filtered(filter_string):
    url = ANNOTATE_URI + '?' + filter_string
    all_results = []
    while url:
        print(url)
        response = requests.get(url)
        data = response.json()
        all_results.extend(data['results'])
        url = data['next']
    return all_results