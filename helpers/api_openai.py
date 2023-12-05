from openai import OpenAI
import ast
import json

CLIENT = OpenAI()

def decode_unicode_escapes(text):
    """Decode Unicode escape sequences in a string."""
    return re.sub(
        r'\\u([0-9a-fA-F]{4})', 
        lambda m: chr(int(m.group(1), 16)), 
        text
    )

def gpt_standardise_text(text, prompt, function, model):
    openai_args = {
        'model': model,
        'temperature': 0.2,
        'messages': [{'role': 'system', 'content': prompt}, {'role': 'user', 'content': text}],
        'tools': [function],
        'tool_choice': {'type': 'function', 'function': {'name': function['function']['name']}}
    }
    chat_completion = CLIENT.chat.completions.create(**openai_args)
    fc_args = chat_completion.choices[0].message.tool_calls[0].function.arguments
    try:
        dwc_terms = ast.literal_eval(fc_args)
    except (SyntaxError, ValueError):
        try:
            dwc_terms = json.loads(fc_args, strict=False)  # Throws json.decoder.JSONDecodeError with strict for e.g. """{\n"code": "\nprint('test')"\n}"""
        except json.decoder.JSONDecodeError:
            import pdb; pdb.set_trace()
    
    allowed_terms = [x for x, y in function['function']['parameters']['properties'].items()]
    for dwc_term in dwc_terms.keys():
        if dwc_term not in allowed_terms:
            print(f'API returned a non-allowed function key: {dwc_term}, trying again')
            return gpt_standardise_text(text, prompt, function)

    dwc_terms = {key: decode_unicode_escapes(value) if isinstance(value, str) else value for key, value in dwc_terms.items()}
    return dwc_terms