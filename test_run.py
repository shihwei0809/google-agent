import urllib.request
import json
import codecs

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

data = json.dumps({
    'records': [{'po': 'test', 'date': '2026-09-18', 'batch': '26916E3191', 'loc': '18P3B', 'tank': 'E319'}],
    'do3in1': True, 'doTransport': False, 'doLorry': True
}).encode('utf-8')

req = urllib.request.Request('http://localhost:8002/api/generate_all_zip', data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        with open('out.zip', 'wb') as f:
            f.write(response.read())
except Exception as e:
    print('Err:', e)
