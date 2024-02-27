import requests
import os
from tenacity import retry, stop_after_attempt, wait_chain, wait_fixed


@retry(stop=stop_after_attempt(10), wait=wait_chain(*[wait_fixed(3) for i in range(3)] + [wait_fixed(9)]))
def get_smallest_img_from_gbif(catalog_number):
    response = requests.get(f'https://api.gbif.org/v1/occurrence/search?datasetKey={os.getenv('DATASET_ID')}&catalogNumber={catalog_number}')
    if response.status_code != 200:
        raise Exception

    data = response.json()
    smallest_image_url = None
    smallest_size = float('inf')

    for record in data.get('results', []):
        for media in record.get('media', []):
            if media.get('type') == 'StillImage':
                image_url = media.get('identifier')
                # try:
                image_response = requests.get(image_url, stream=True)
                image_size = len(image_response.content)
                if image_size < smallest_size:
                    smallest_size = image_size
                    smallest_image_url = image_url
                # except requests.RequestException as e:
                    # print(f'Failed to get image {image_url} - {catalog_number}: {e}')

    return smallest_image_url