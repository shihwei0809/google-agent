with open(r'd:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\static\index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
in_func = False
for line in lines:
    if 'document.getElementById("btnGenerateAll").addEventListener' in line:
        in_func = True
    if in_func:
        print(line.rstrip())
        if line.strip() == '});':
            in_func = False
