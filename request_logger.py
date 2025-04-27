#!/usr/bin/env python3
"""
HTTP Request Logger - patches the requests library to log all HTTP calls
"""

import os
import json
import logging
import datetime
from functools import wraps

# Configure logging
log_file = 'http_requests.log'
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('http_logger')

def monkey_patch_requests():
    """
    Patch the requests library to log all requests and responses
    """
    import requests
    from requests import sessions
    
    # Save the original request method
    original_request = sessions.Session.request
    
    @wraps(original_request)
    def request_wrapper(self, method, url, **kwargs):
        # Log the request
        request_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        
        # Create log entry for request
        request_data = {
            'id': request_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'type': 'request',
            'method': method,
            'url': url,
        }
        
        # Add headers (but redact authorization tokens)
        if 'headers' in kwargs:
            headers_copy = dict(kwargs['headers'])
            if 'authorization' in headers_copy:
                headers_copy['authorization'] = '[REDACTED]'
            request_data['headers'] = headers_copy
        
        # Add query parameters
        if 'params' in kwargs:
            request_data['params'] = kwargs['params']
        
        # Add json payload if present
        if 'json' in kwargs:
            request_data['json'] = kwargs['json']
        
        # Log the request
        logger.info(f"OUTGOING REQUEST: {json.dumps(request_data, default=str)}")
        
        # Make the actual request
        response = original_request(self, method, url, **kwargs)
        
        # Log the response
        response_data = {
            'id': request_id,  # Link to the request
            'timestamp': datetime.datetime.now().isoformat(),
            'type': 'response',
            'status_code': response.status_code,
            'url': response.url,
            'elapsed': str(response.elapsed),
        }
        
        # Add response headers
        response_data['headers'] = dict(response.headers)
        
        # Try to add response content for reasonable-sized responses
        try:
            if int(response.headers.get('content-length', 0)) < 10000:
                try:
                    response_data['content'] = response.json()
                except:
                    # Not JSON, so add a snippet of text or indicate binary
                    content_type = response.headers.get('content-type', '')
                    if 'text' in content_type or 'json' in content_type:
                        response_data['content'] = response.text[:500] + ('...' if len(response.text) > 500 else '')
                    else:
                        response_data['content'] = '[binary data]'
        except:
            response_data['content'] = '[error reading content]'
        
        # Log the response
        logger.info(f"INCOMING RESPONSE: {json.dumps(response_data, default=str)}")
        
        return response
    
    # Replace the original request method with our wrapper
    sessions.Session.request = request_wrapper
    
    print(f"✅ HTTP logging enabled - all requests will be logged to {os.path.abspath(log_file)}")

# Apply the monkey patch when this module is imported
monkey_patch_requests() 