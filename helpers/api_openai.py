from openai import OpenAI
import ast
import requests
import json
import yaml


def gpt_standardise_text(text, prompt_url, function_url):
    function = yaml.safe_load(requests.get(function_url).text)
    system_prompt = requests.get(prompt_url).text
    openai_args = {
        'model': 'gpt-4',
        'temperature': 0.2,
        'messages': [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': text}],
        'tools': [function],
        'tool_choice': {'type': 'function', 'function': {'name': function['function']['name']}}
    }
    client = OpenAI()
    chat_completion = client.chat.completions.create(**openai_args)
    fc_args = chat_completion.choices[0].message.tool_calls[0].function.arguments
    try:
        args = ast.literal_eval(fc_args)
    except (SyntaxError, ValueError):
        try:
            args = json.loads(fc_args, strict=False)  # Throws json.decoder.JSONDecodeError with strict for e.g. """{\n"code": "\nprint('test')"\n}"""
        except json.decoder.JSONDecodeError:
            import pdb; pdb.set_trace()
    return args