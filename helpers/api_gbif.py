import requests

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