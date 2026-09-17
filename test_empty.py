import urllib.request
import json
import codecs

data = json.dumps({
    'records': [{'po': 'test', 'date': '2026-09-18', 'batch': '26916E3191', 'loc': '18P3B'}],
    'do3in1': True, 'doTransport': False, 'doLorry': True
}).encode('utf-8')

req = urllib.request.Request('http://localhost:8002/api/generate_all_zip', data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        pass
except:
    pass

try:
    with codecs.open('c_log.txt', 'r', 'utf-8') as f:
        print(f.read())
except Exception as e:
    print("Log not found")
