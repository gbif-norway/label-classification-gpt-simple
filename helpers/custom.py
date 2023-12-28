import re

def text_exclusion(ocr_text, catalog):
    for_exclusion = [f'V {catalog}', '\\s*'.join(catalog), r'Herb. Oslo \(O\)', r'Herb. Univers. Osloensis', r'Herb. Univers. Osloënsis', r'Herb. Univers. Osloensis\s+\d\d\d\d', r'Herb. Univers. Osloënsis\s+\d\d\d\d', r'Planta Scandinavica', r'Flora Suecica', r'Flora Norvegica', r'Herb. Univers. Christianiensis.']
    for exclude in for_exclusion:
        ocr_text = re.sub(exclude, '', ocr_text, flags=re.IGNORECASE)
    return ocr_text