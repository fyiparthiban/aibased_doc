import requests

try:
    r = requests.get('http://127.0.0.1:8003/health', timeout=5)
    print(r.status_code)
    print(r.text)
except Exception as e:
    print('ERROR', e)
