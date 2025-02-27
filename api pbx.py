import requests
import hashlib
import urllib
from collections.abc import MutableMapping
from urllib.parse import urlencode, unquote


YOUR_PBX_URL = "https://lensa.while1.biz/api/cdr" # Replace [YOUR-PBX-URL] with your actual PBX URL
YOUR_API_TOKEN = "GfR7tVSCn|4Ug75%FGRe21"
YOUR_API_KEY = "cKTdsmwaOcCsUjvgcR6mZ"

def php_style_http_build_query(data, prefix=''):
    """
    Recursively build a query string in a style similar to PHP's http_build_query() function.

    :param data: The data dictionary or list to be encoded.
    :param prefix: The current prefix to prepend to keys.
    :return: A string that is URL-encoded in a PHP-style manner.
    """
    if isinstance(data, dict):
        items = data.items()
    elif isinstance(data, list):
        items = enumerate(data)
    else:
        return f"{prefix}={quote_plus(str(data))}"

    query_fragments = []
    for key, value in items:
        if isinstance(value, (dict, list)):
            if isinstance(data, list):
                new_prefix = f"{prefix}[]" if prefix else key
            else:
                new_prefix = f"{prefix}[{key}]" if prefix else key
            fragment = php_style_http_build_query(value, new_prefix)
        else:
            key = f"{prefix}[{key}]" if isinstance(data, dict) and prefix else key
            key = f"{prefix}[]" if isinstance(data, list) and prefix else key
            key = quote_plus(str(key))
            value = quote_plus(str(value))
            fragment = f"{key}={value}"
        query_fragments.append(fragment)

    return '&'.join(query_fragments)



def generate_api_hash(params, api_key):
    """
    Generates an MD5 hash of the query string created from the params dictionary,
    concatenated with the provided API key.
    
    :param params: Dictionary of parameters to be included in the query string.
    :param api_key: String representing the API key to be appended to the query string.
    :return: MD5 hash of the concatenated query string and API key.
    """
    # Build query string from params and append your API key
    query_string = urllib.parse.urlencode(params) + api_key
    
    # Calculate MD5 hash
    api_hash = hashlib.md5(query_string.encode('utf-8')).hexdigest()
    
    return api_hash

from collections.abc import MutableMapping
from urllib.parse import urlencode, unquote

def flatten(dictionary, parent_key=False, separator='.', separator_suffix=''):
    """
    Turn a nested dictionary into a flattened dictionary
    :param dictionary: The dictionary to flatten
    :param parent_key: The string to prepend to dictionary's keys
    :param separator: The string used to separate flattened keys
    :return: A flattened dictionary
    """

    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + separator + key + separator_suffix if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten(value, new_key, separator, separator_suffix).items())
        elif isinstance(value, list) or isinstance(value, tuple):
            for k, v in enumerate(value):
                items.extend(flatten({str(k): v}, new_key, separator, separator_suffix).items())
        else:
            items.append((new_key, value))
    return dict(items)


req = {'check': 'command', 'parameters': ({'parameter': '1', 'description': '2'}, {'parameter': '3', 'description': '4'})}
req = flatten(req, False, '[', ']')
query = urlencode(req)

# Set up the filters and other parameters as needed
params = {
    'page': 1,
    'filters': {
        'date_between': ['2025-02-01', '2025-02-01'],
        #'project_id': None,
        #'inbound_route_id': None,
        #'direction': None,
        #'call_status': None,
        #'telephone_like': None,
        #'telephone': None,
        #'source': None,
        #'destination': None,
        #'hour_between': None,
        #'from_id': None,
        #'uniqueid': None,
        #'linkedid': None,
        #'has_transcription': None,
        #'has_monitor_file': None,
        #'has_recording_file': None,
    }
}

params = flatten(params, False, '[', ']')

api_hash = generate_api_hash(params, YOUR_API_KEY)

# Add the api_hash to the params
params['api_hash'] = api_hash

# HTTP Headers
headers = {
    "Authorization": f"Bearer {YOUR_API_TOKEN}",
    "Content-Type": "application/json"  # Assuming JSON format for simplicity
}

# Make the POST request
response = requests.post(YOUR_PBX_URL, json=params, headers=headers)

# Check the response
if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.status_code}")
