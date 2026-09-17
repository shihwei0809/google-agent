import urllib.request
import json

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (
    '--' + boundary + '\r\n'
    'Content-Disposition: form-data; name="files"; filename="L12C53161_IPA_Lorry_TSMC 0918 15P51.csv"\r\n'
    'Content-Type: text/csv\r\n\r\n'
    'RawLotId,26916E3191\r\n'
    '--' + boundary + '--\r\n'
).encode('utf-8')

req = urllib.request.Request('http://localhost:8002/api/upload_coa_files', data=body, headers={'Content-Type': 'multipart/form-data; boundary=' + boundary})
try:
    with urllib.request.urlopen(req) as response:
        pass
except:
    pass

req = urllib.request.Request('http://localhost:8002/api/test_cache')
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except Exception as e:
    print(e)
