import urllib.request
try:
    req = urllib.request.Request('https://image.pollinations.ai/prompt/safe%20factory%20worker?width=640&height=400', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        print("Status:", response.status)
        print("Content-Type:", response.headers.get('Content-Type'))
        print("Length:", len(response.read()))
except Exception as e:
    print('Error:', e)
