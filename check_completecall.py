path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.split('\n')
# Check submitJudge calls - find where it does the D1 fetch
for i, l in enumerate(lines):
    if 'action: \'completeSample\'' in l or 'action: "completeSample"' in l:
        with open('dump_completecall.txt', 'w', encoding='utf-8') as fw:
            fw.write("\n".join(lines[i-5:i+20]))
        print(f"Found at line {i}")
        break
