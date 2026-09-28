path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.split('\n')
# Check if submitJudge has D1 endpoint or just GAS+API
for i, l in enumerate(lines):
    if 'D1_API' in l or 'action=completeSample' in l or '/api/index' in l:
        print(f"Line {i}: {l.strip()}")
# Also check how the D1 variant sends to backend
for i, l in enumerate(lines):
    if 'CF_PAGES' in l or 'IS_D1' in l or 'D1_URL' in l or '/api?' in l:
        print(f"Line {i}: {l.strip()}")
# Check what the constant URL is
for i, l in enumerate(lines):
    if 'const API_URL' in l or 'const GAS' in l or 'let GAS' in l:
        print(f"Line {i}: {l.strip()}")
