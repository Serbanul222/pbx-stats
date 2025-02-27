import requests
import hashlib
import urllib.parse
import os
from flask import Flask, request, jsonify, render_template
from collections.abc import MutableMapping
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# PBX API configuration from environment variables
PBX_URL = os.environ.get('PBX_URL', 'https://lensa.while1.biz/api/cdr')
PBX_API_TOKEN = os.environ.get('PBX_API_TOKEN', '')
PBX_API_KEY = os.environ.get('PBX_API_KEY', '')

def flatten(dictionary, parent_key=False, separator='[', separator_suffix=']'):
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

def generate_api_hash(params, api_key):
    """
    Generates an MD5 hash of the query string created from the params dictionary,
    concatenated with the provided API key.
    """
    # Build query string from params and append your API key
    query_string = urllib.parse.urlencode(params) + api_key
    
    # Calculate MD5 hash
    api_hash = hashlib.md5(query_string.encode('utf-8')).hexdigest()
    
    return api_hash

@app.route('/')
def index():
    # Render the main template
    return render_template('index.html')

@app.route('/api/calls', methods=['GET'])
def get_calls():
    # Get date parameters from request
    start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Set up the filters and other parameters
    params = {
        'page': 1,
        'filters': {
            'date_between': [start_date, end_date],
        }
    }
    
    # Add other filters if provided in the request
    caller_id = request.args.get('caller_id')
    if caller_id:
        params['filters']['caller_id_like'] = caller_id
        
    call_code = request.args.get('call_code')
    if call_code:
        params['filters']['code'] = call_code
        
    call_status = request.args.get('call_status')
    if call_status:
        params['filters']['call_status'] = call_status
    
    # Flatten the parameters and generate the API hash
    params = flatten(params, False, '[', ']')
    api_hash = generate_api_hash(params, PBX_API_KEY)
    
    # Add the api_hash to the params
    params['api_hash'] = api_hash
    
    # HTTP Headers
    headers = {
        "Authorization": f"Bearer {PBX_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Make the POST request to the PBX API
        response = requests.post(PBX_URL, json=params, headers=headers)
        
        if response.status_code == 200:
            # Return the API response as JSON
            return jsonify(response.json())
        else:
            return jsonify({
                "error": f"API Error: {response.status_code}",
                "message": response.text
            }), response.status_code
    except Exception as e:
        return jsonify({
            "error": "Server Error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    # Run the application on all interfaces (important for Docker)
    app.run(debug=False, host='0.0.0.0', port=5000)