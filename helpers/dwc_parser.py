import re
from dateutil import parser
from datetime import datetime

def norway_text_exclusion(ocr_text, catalog):
    for_exclusion = [f'V {catalog}', '\\s*'.join(catalog), r'Herb. Oslo \(O\)', r'Herb. Univers. Osloensis', r'Herb. Univers. Osloënsis', r'Herb. Univers. Osloensis\s+\d\d\d\d', r'Herb. Univers. Osloënsis\s+\d\d\d\d', r'Planta Scandinavica', r'Flora Suecica', r'Flora Norvegica', r'Herb. Univers. Christianiensis.']
    for exclude in for_exclusion:
        ocr_text = re.sub(exclude, '', ocr_text, flags=re.IGNORECASE)
    return ocr_text

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
    "XII": 12,
    "XI": 11,
    "X": 10,
    "IX": 9,
    "VIII": 8,
    "VII": 7,
    "VI": 6,
    "V": 5,
    "IV": 4,
    "III": 3,
    "II": 2,
    "I": 1
}

def norway_date_parse(date_str):
    for key, value in norwegian_months.items():
        date_str = re.sub(key, str(value), date_str, flags=re.IGNORECASE)
    for key, value in roman_numerals.items():
        date_str = re.sub(r'\b' + key + r'\b', str(value), date_str, flags=re.IGNORECASE)
    return date_parse(date_str)

def tajik_date_parse(date_str):
    return date_parse(date_str)
    
def date_parse(date_str):
    try:
        date = parser.parse(date_str, default=datetime(1, 1, 1), dayfirst=True)
        if date == datetime(1, 1, 1):
            return None
        return date
    except:
        return None

def elevation_parse(elevation):
    pass