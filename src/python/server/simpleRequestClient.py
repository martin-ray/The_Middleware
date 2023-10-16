import requests

# Define the URL and headers
url = 'http://localhost:8080'
headers = {
    'type': 'init',
    'offset': str(256),
    'L3Size': str(600),
    'L4Size': str(300),
    'Policy': 'LRU',
    'FileName': 'test',
}

# Send the HTTP GET request with the specified headers
response = requests.get(url, headers=headers)

# Check the response status and content
if response.status_code == 200:
    print('Request was successful.')
    print('The system got initialized')
    
else:
    print(f'Request failed with status code {response.status_code}')
