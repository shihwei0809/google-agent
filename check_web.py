path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\1_Web_網頁版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
if 'judgeApproverText' in text:
    print("YES in 1_Web_網頁版")
else:
    print("NO in 1_Web_網頁版")
