import re
from typing import List
import nltk
import pickle
import pycountry

with open('/srv/code/genera.pkl', 'rb') as f:
    GENERA = pickle.load(f)

with open('/srv/code/tajik-collectors.pkl', 'rb') as f:
    TAJIK_COLLECTORS = pickle.load(f)
with open('/srv/code/russian-collectors.pkl', 'rb') as f:
    RUSSIAN_COLLECTORS = pickle.load(f)
COLLECTORS = TAJIK_COLLECTORS | RUSSIAN_COLLECTORS

def lines(text):
    return re.split('\n', text)

def verbatim_identification(lines, genus):
    first_words_per_line = [_get_latin_words(line)[0] for line in lines]
    
    # Usual scenario has the genus as the first word of the line containing the scientific name line
    for line_index, first_word in enumerate(first_words_per_line):
        if first_word.lower() == genus.lower():
            return line_index, ' '.join(_get_latin_words(lines[line_index]))
    
    # Sometimes scientific name is not the first word in a line, but is in the line somewhere
    for line in lines:
        if genus in line:
            return line_index, ' '.join(_get_latin_words(line))
    
    # Fuzzy matching for first word in line, perhaps the given genus has a spelling mistake
    distances = [nltk.edit_distance(genus, word) for word in first_words_per_line]
    closest_distance, line_index = min((val, idx) for (idx, val) in enumerate(distances))
    if closest_distance < 3:
        name_parts = _get_latin_words(lines[line_index])
        name_parts[0] = genus
        return line_index, ' '.join(name_parts)
    
    return None, None

def verbatim_identification_no_genus(lines):
    first_words_per_line = [_get_latin_words(line)[0] for line in lines]

    # Then genus is probably just completely wrong, search for any line with a first word that is a genus
    for first_word, line_index in enumerate(first_words_per_line):
        if first_word in GENERA:
            return line_index, ' '.join(_get_latin_words(lines[line_index])), first_word
    
    # Fuzzy match for any genus at any first word in a line
    distances = []
    for line_index, first_word in enumerate(first_words_per_line):
        word_distances = {}
        for genus in GENERA:
            word_distances[genus] = nltk.edit_distance(genus, first_word)
        closest_genus, closest_distance = min(word_distances.items(), key=lambda x: x[1])
        distances.append({'genus': closest_genus, 'distance': closest_distance, 'line_index': line_index})
    
    closest = min(distances, key=lambda x: x['distance'])
    if closest['distance'] < 3:
        line_index = closest['line_index']
        text = ' '.join(_get_latin_words(lines[line_index]))
        text = text.replace(first_words_per_line[line_index], closest['genus'])
        return line_index, text, closest['genus']
    
    return None, None, None

def elevation(lines):
    numbers = r'([1-9][0-9]{2,3}(-[1-9][0-9]{2,3})?)'
    units = r'([mм]|ft)'
    non_digit_la = r'(?!\d)'
    non_digit_lb = r'(?<!\d)'
    prefix = r'(alt|h|altitude|Высотанадуровнемморя)[\-\.:]*' # Высота над уровнем моря = Height above sea level

    for line in lines:
        unspaced_line = line.replace(' ', '')

        matches = re.search(f'{prefix}({numbers}{units}?){non_digit_la}', unspaced_line, re.IGNORECASE|re.UNICODE)
        if matches:
            return matches.group(2)
        
        matches = re.search(f'{prefix}{numbers}{non_digit_la}', unspaced_line, re.IGNORECASE|re.UNICODE)
        if matches:
            return matches.group(2)
        
        matches = re.search(f'[\n\s]+{numbers}\s*{units}', line, re.IGNORECASE|re.UNICODE)
        if matches:
            return matches.group(0).replace(' ', '')

        matches = re.search(f'[24][-:]+({numbers}{units}?){non_digit_la}', unspaced_line, re.IGNORECASE|re.UNICODE)
        if matches:
            return matches.group(1)
    
    unspaced = ''.join([l.replace(' ', '') for l in lines])

    matches = re.search(f'{prefix}({numbers}{units}?){non_digit_la}', unspaced, re.IGNORECASE|re.UNICODE)
    if matches:
        return matches.group(2)

    matches = re.search(f'{non_digit_lb}({numbers}{units}?){prefix}', unspaced, re.IGNORECASE|re.UNICODE)
    if matches:
        return matches.group(1)

    return None

def min_max_elevation_in_meters(text):  # Has spaces stripped
    if not text:
        return None, None
    number_matches = re.findall('[1-9][0-9]{2,3}', text)
    max = number_matches.pop() 
    min = number_matches.pop() if number_matches else max
    units = re.search('([mм]|ft)', text)
    if units and units.group(0) == 'ft':
        min = round(int(min) / 3.281)
        max = round(int(max) / 3.281)
    return str(min), str(max)

def record_number(lines):
    for line in lines:
        matches = re.search('(no|№)[\.\s\:]*(\d+)', line, re.IGNORECASE|re.UNICODE)
        if matches:
            return matches.group(2)
    return None

def year(lines):
    for line in lines:
        matches = re.search('\n[\s\n\:\.]?((1[789][0-9]|20[0-3])\d)', line)
        if matches:
            return matches.group(1)
        return None

def names(lines):
    for line in lines:
        collected = ['collected', 'coll.', 'coll:', 'collector']
        for phrase in collected:
            matches = re.search(phrase, line, re.IGNORECASE)
            if matches:
                return line.split(matches.group(0))[-1].strip()
    
    for line in lines:
        words = [x for x in _get_latin_words(line) if len(x) > 4]
        for word in words:
            if word in COLLECTORS:
                return word
    return None

def country(lines):
    for line in lines:
        common_countries = ['Tajikistan', 'Afghanistan', 'China', 'Russia', 'Kazakhstan']
        for country in common_countries:
            if country.lower() in line.lower():
                return country
        
        for country in pycountry.countries:
            if country.name.lower() in line.lower():
                return country.name

def _get_latin_words(line: str) -> List[str]:
    only_words = re.sub('[^A-Za-z()\s]', '', line)
    stripped_spaces = re.sub('\s+', ' ', only_words)
    return re.split('\s', stripped_spaces.strip())

def ipt_friendly_string(s):
    return s.replace('\n', '#').replace("'", '').replace('"', '')