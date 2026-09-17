import urllib.request
try:
    with urllib.request.urlopen('http://localhost:8002/api/test_cache') as response:
        print(response.read().decode())
except Exception as e:
    print(e)
