path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace getSamples
text = text.replace('fetch(`${GAS_API_URL}?action=getSamples`)', 'fetch(`${GAS_API_URL}?action=getSamples&_t=${Date.now()}`, { cache: "no-store" })')

# Replace getConfig
text = text.replace('fetch(`${GAS_API_URL}?action=getConfig`)', 'fetch(`${GAS_API_URL}?action=getConfig&_t=${Date.now()}`, { cache: "no-store" })')

# Replace getEmployees
text = text.replace('fetch(`${GAS_API_URL}?action=getEmployees`)', 'fetch(`${GAS_API_URL}?action=getEmployees&_t=${Date.now()}`, { cache: "no-store" })')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
