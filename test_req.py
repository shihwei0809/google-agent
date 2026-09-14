import urllib.request
try:
    with urllib.request.urlopen('http://localhost:18082/index.html') as response:
        html = response.read()
        print("Length:", len(html))
        print("Status:", response.status)
        print("Headers:", response.headers)
except Exception as e:
    print("Error:", e)
