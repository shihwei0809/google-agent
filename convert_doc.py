import win32com.client, os

word = win32com.client.Dispatch('Word.Application')
word.Visible = False

dir_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統'
files = [
    'C50110-INV-02 進出貨作業管理辦法(3.0版).doc',
    'C50110-INV-02-01 儲槽進出貨作業方法(3.1版).doc'
]

for file in files:
    doc_path = os.path.join(dir_path, file)
    docx_path = doc_path + 'x'
    if os.path.exists(doc_path):
        print(f'Converting {doc_path} to docx...')
        try:
            doc = word.Documents.Open(doc_path)
            doc.SaveAs(docx_path, FileFormat=16) # 16 = wdFormatXMLDocument
            doc.Close()
            print(f'Success: {docx_path}')
        except Exception as e:
            print(f'Error converting {doc_path}: {e}')

word.Quit()
