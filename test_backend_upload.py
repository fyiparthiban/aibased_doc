from pathlib import Path
import requests

print('root', requests.get('http://127.0.0.1:8003/').status_code)
print('health', requests.get('http://127.0.0.1:8003/health').status_code)
print('query', requests.post('http://127.0.0.1:8003/query', json={'question': 'Hello'}).status_code)

path = Path('temp_upload_test.txt')
path.write_text('This is a backend upload test document.')

with open(path, 'rb') as f:
    files = {'files': f}
    r = requests.post('http://127.0.0.1:8003/upload-documents', files=files)
    print('upload status', r.status_code)
    print('upload text', r.text)
    print('request url', r.request.url)
    print('request method', r.request.method)
    print('request headers', r.request.headers)

path.unlink()
