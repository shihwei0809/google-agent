import urllib.request
try:
    with urllib.request.urlopen('http://localhost:18082/index.html', timeout=2) as response:
        html = response.read().decode('utf-8')
        if '員工教育訓練測驗產生器' in html:
            print("OK, generator loaded successfully!")
        else:
            print("Missing title text")
except Exception as e:
    print('Error:', e)
