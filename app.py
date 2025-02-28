import requests
import hashlib
import urllib.parse
import os
from flask import Flask, request, jsonify, render_template
from collections.abc import MutableMapping
import json
from datetime import datetime
from dotenv import load_dotenv
import threading
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)

# PBX API configuration from environment variables
PBX_URL = os.environ.get('PBX_URL', 'https://lensa.while1.biz/api/cdr')
PBX_API_TOKEN = os.environ.get('PBX_API_TOKEN', '')
PBX_API_KEY = os.environ.get('PBX_API_KEY', '')

# Self-ping function to prevent Render spin down
def keep_alive():
    while True:
        try:
            time.sleep(600)  # Ping every 10 minutes
            requests.get("http://127.0.0.1:5000/")  # Ping the index route
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")

# Start keep-alive in a separate thread
threading.Thread(target=keep_alive, daemon=True).start()

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
    
    # Format dates with time as required by the API
    start_date = f"{start_date} 00:00:00"
    end_date = f"{end_date} 23:59:59"
    
    # Get pagination parameter
    page = int(request.args.get('page', 1))
    
    # Get filter parameters
    call_status = request.args.get('call_status')
    caller_id = request.args.get('caller_id')
    call_code = request.args.get('call_code')
    
    # Set up the filters and other parameters exactly as shown in API docs
    params = {
        'page': page,
        'filters': {
            'date_between': [start_date, end_date],
            'project_id': None,
            'user_id': None,
            'inbound_route_id': None,
            'direction': None,
            'call_status': None,
            'telephone_like': None,
            'telephone': None,
            'source': None,
            'destination': None,
            'hour_between': None,
            'from_id': None,
            'uniqueid': None,
            'linkedid': None,
            'has_transcription': None,
            'has_monitor_file': None,
            'has_recording_file': None,
            'external_id': None
        }
    }
    
    # Add other filters if provided in the request
    if caller_id and caller_id.strip():
        params['filters']['telephone_like'] = caller_id.strip()
        
    if call_code and call_code.strip():
        params['filters']['code'] = call_code.strip()
        
    if call_status and call_status.strip():
        # Make sure to use exactly the values from the API documentation
        # The API specifically mentions: NO ANSWER, CONGESTION, FAILED, BUSY, ANSWERED
        params['filters']['call_status'] = call_status.strip()
    
    # Debug logging
    print(f"Debug - API Request parameters: {json.dumps(params, indent=2)}")
    
    # Remove None values as they're not needed by the API
    # This ensures we're sending a clean request that matches the API expectations
    for key in list(params['filters'].keys()):
        if params['filters'][key] is None:
            del params['filters'][key]
    
    # Flatten the parameters and generate the API hash
    flat_params = flatten(params, False, '[', ']')
    api_hash = generate_api_hash(flat_params, PBX_API_KEY)
    
    # Add the api_hash to the params
    flat_params['api_hash'] = api_hash
    
    # HTTP Headers
    headers = {
        "Authorization": f"Bearer {PBX_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Make the POST request to the PBX API
        print(f"Debug - Sending request to: {PBX_URL}")
        print(f"Debug - Request body: {json.dumps(flat_params, indent=2)}")
        
        response = requests.post(PBX_URL, json=flat_params, headers=headers)
        
        if response.status_code != 200:
            print(f"Debug - API Error: {response.status_code}, {response.text}")
            return jsonify({
                "error": f"API Error: {response.status_code}",
                "message": response.text
            }), response.status_code
        
        # Parse response
        api_response = response.json()
        
        # Debug response
        result_count = len(api_response.get('results', []))
        print(f"Debug - Received {result_count} results")
        
        if result_count > 0:
            # Log all statuses to verify filtering
            statuses = [call.get('call_status') for call in api_response.get('results', [])[:10]]
            print(f"Debug - First 10 call statuses before filtering: {statuses}")
        
        # *** THIS IS WHERE YOU ADD THE CLIENT-SIDE FILTERING CODE ***
        # Apply client-side filtering since the API doesn't properly filter by status
        if call_status and 'results' in api_response:
            # Filter results client-side
            filtered_results = [call for call in api_response.get('results', []) 
                              if call.get('call_status') == call_status]
            
            print(f"Debug - Filtered from {len(api_response.get('results', []))} to {len(filtered_results)} results")
            
            # Update the API response with filtered results
            api_response['results'] = filtered_results
            
            # Update pagination information
            if 'pagination' in api_response:
                api_response['pagination']['row_count'] = len(filtered_results)
        
        # Do the same for call_code if needed
        if call_code and 'results' in api_response:
            filtered_results = [call for call in api_response.get('results', []) 
                              if call.get('code') == call_code]
            
            api_response['results'] = filtered_results
            
            if 'pagination' in api_response:
                api_response['pagination']['row_count'] = len(filtered_results)
        
        # Return the modified API response
        return jsonify(api_response)
            
    except Exception as e:
        print(f"Exception in API call: {str(e)}")
        return jsonify({
            "error": "Server Error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    # Run the application on all interfaces (important for Docker)
    app.run(debug=False, host='0.0.0.0', port=5000)