from helpers.api_gcv_ocr import detect_text
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

results = {}
with open('input/catalog_numbers.txt') as file, open('output-append.csv', 'a', newline='') as csvfile: