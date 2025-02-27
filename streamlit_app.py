import streamlit as st
import requests
import hashlib
import urllib.parse
import os
import pandas as pd
from collections.abc import MutableMapping
from datetime import datetime, timedelta

# Title
st.title('PBX Call Records Viewer')

# Define functions
def flatten(dictionary, parent_key=False, separator='[', separator_suffix=']'):
    """
    Turn a nested dictionary into a flattened dictionary
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
    query_string = urllib.parse.urlencode(params) + api_key
    api_hash = hashlib.md5(query_string.encode('utf-8')).hexdigest()
    return api_hash

def get_calls(start_date, end_date, caller_id=None, call_code=None, call_status=None):
    """
    Get call data from PBX API
    """
    # PBX API configuration from environment variables or secrets
    PBX_URL = os.environ.get('PBX_URL')
    PBX_API_TOKEN = os.environ.get('PBX_API_TOKEN')
    PBX_API_KEY = os.environ.get('PBX_API_KEY')
    
    # Set up the filters and parameters
    params = {
        'page': 1,
        'filters': {
            'date_between': [start_date, end_date],
        }
    }
    
    # Add other filters if provided
    if caller_id:
        params['filters']['caller_id_like'] = caller_id
    if call_code:
        params['filters']['code'] = call_code
    if call_status:
        params['filters']['call_status'] = call_status
    
    # Flatten parameters and generate hash
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
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Server Error: {str(e)}")
        return None

# Create sidebar with filters
st.sidebar.header('Filters')

# Date filters
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        datetime.now() - timedelta(days=7)
    )
with col2:
    end_date = st.date_input(
        "End Date",
        datetime.now()
    )

# Other filters
caller_id = st.sidebar.text_input('Caller ID', '')

call_code = st.sidebar.selectbox(
    'Call Code',
    ['', 'outbound', 'incoming', 'inbound_ivr', 'originate-call-api']
)

call_status = st.sidebar.selectbox(
    'Call Status',
    ['', 'ANSWERED', 'NO ANSWER', 'BUSY', 'FAILED']
)

# Reset button
if st.sidebar.button('Reset Filters', key='reset'):
    st.session_state.button_clicked = False
    # Force a rerun to clear displayed data
    st.experimental_rerun()

# Store if button was clicked in session state
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

# Apply filters button
if st.sidebar.button('Apply Filters'):
    st.session_state.button_clicked = True

# Only fetch and display data if button was clicked
if st.session_state.button_clicked:
    # Format dates
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get data
    with st.spinner('Loading data...'):
        data = get_calls(
            start_date_str, 
            end_date_str, 
            caller_id, 
            call_code, 
            call_status
        )
    
    if data and not data.get('has_error', False):
        # Extract results
        calls = data.get('results', [])
        
        if calls:
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(calls)
            
            # Display statistics
            st.header('Call Statistics')
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Calls", len(df))
            
            with col2:
                answered_calls = len(df[df['call_status'] == 'ANSWERED'])
                st.metric("Answered Calls", answered_calls)
            
            with col3:
                missed_calls = len(df) - answered_calls
                st.metric("Missed Calls", missed_calls)
            
            with col4:
                # Calculate average duration for calls with duration
                df_with_duration = df[df['duration'].notna()]
                if len(df_with_duration) > 0:
                    # Convert duration strings to seconds for calculation
                    duration_seconds = []
                    for duration in df_with_duration['duration']:
                        try:
                            parts = duration.split(':')
                            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                            duration_seconds.append(seconds)
                        except:
                            duration_seconds.append(0)
                    
                    avg_seconds = sum(duration_seconds) / len(duration_seconds)
                    avg_duration = f"{int(avg_seconds // 3600):02d}:{int((avg_seconds % 3600) // 60):02d}:{int(avg_seconds % 60):02d}"
                else:
                    avg_duration = "00:00:00"
                
                st.metric("Avg Duration", avg_duration)
            
            # Display data
            st.header('Call Records')
            
            # Format the DataFrame for display
            display_df = df[['time', 'direction', 'source', 'destination', 
                            'call_status', 'duration', 'user_fullname', 
                            'project', 'code']].copy()
            
            # Rename columns for better readability
            display_df.columns = ['Time', 'Direction', 'Source', 'Destination', 
                                'Status', 'Duration', 'User', 'Project', 'Code']
            
            # Add recording links if available
            if 'monitor_url' in df.columns:
                display_df['Recording'] = df['monitor_url'].apply(
                    lambda x: '✓' if pd.notna(x) and x != '' else '✗'
                )
            
            # Format dates
            display_df['Time'] = pd.to_datetime(display_df['Time']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Display the table
            st.dataframe(display_df, use_container_width=True)
            
            # Option to download as CSV
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download as CSV",
                csv,
                "call_records.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.info('No calls found for the selected filters.')
    else:
        st.error('Failed to load data or API returned an error.')
else:
    # Initial state or after reset
    st.info('Select filters and click "Apply Filters" to view call records.')