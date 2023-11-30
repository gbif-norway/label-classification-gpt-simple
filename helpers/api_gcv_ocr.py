from google.cloud import vision
import json


def detect_text(image_url):
    vision_client = vision.ImageAnnotatorClient()
    print(f'Detecting text in image: {image_url}')
    response = vision_client.annotate_image({
        'image': {'source': {'image_uri': image_url}},
        'features': [{'type_': vision.Feature.Type.TEXT_DETECTION}],
        'image_context': {'language_hints': ['no', 'la']},
    })
    response_json = vision.AnnotateImageResponse.to_json(response)
    response_dict = json.loads(response_json)
    try: 
        fta = response_dict['fullTextAnnotation']
    except:
        import pdb; pdb.set_trace()
    return fta