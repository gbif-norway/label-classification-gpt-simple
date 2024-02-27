from google.cloud import vision
from google.protobuf.json_format import MessageToDict
import json
import requests
from skimage import io
from skimage.transform import resize
import io as python_io
import os
import tempfile
from tenacity import retry, stop_after_attempt, wait_chain, wait_fixed


@retry(stop=stop_after_attempt(10), wait=wait_chain(*[wait_fixed(3) for i in range(3)] + [wait_fixed(9)]))
def download_image(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        # Use tempfile to create a temporary file
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_img.write(response.content)
        temp_img.close()
        return temp_img.name
    else:
        raise Exception(f"Error downloading image: Status code {response.status_code}")

def crop_image_skimage(image_path, bottom_crop_px):
    img = io.imread(image_path)
    cropped_img = img[:-bottom_crop_px, :]
    return cropped_img

@retry(stop=stop_after_attempt(10), wait=wait_chain(*[wait_fixed(3) for i in range(3)] + [wait_fixed(9)]))
def detect_text_in_cropped_image_skimage(cropped_img):
    img_byte_arr = python_io.BytesIO()
    io.imsave(img_byte_arr, cropped_img, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    vision_client = vision.ImageAnnotatorClient()
    image_context = vision.ImageContext(language_hints=['no', 'la'])
    image = vision.Image(content=img_byte_arr)
    response = vision_client.text_detection(image=image, image_context=image_context)
    return response

def process_image_from_url(image_url, bottom_crop_px=400):
    temp_image_path = download_image(image_url)
    try:
        cropped_img = crop_image_skimage(temp_image_path, bottom_crop_px)
        text_detection_response = detect_text_in_cropped_image_skimage(cropped_img)
    finally:
        os.remove(temp_image_path)  # Ensure the temporary file is deleted

    pages_json = MessageToDict(text_detection_response.full_text_annotation._pb)
    return text_detection_response.full_text_annotation.text, pages_json['pages']

def detect_text_from_url(image_url):
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