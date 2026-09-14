import urllib.request
try:
    with urllib.request.urlopen('http://localhost:18082/index.html') as response:
        html = response.read()
        print('Status:', response.status)
        print('First 100:', repr(html[:100]))
        print('Last 100:', repr(html[-100:]))
except Exception as e:
    print('Error:', e)
