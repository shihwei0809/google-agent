import win32com.client, os

word = win32com.client.Dispatch('Word.Application')
word.Visible = False

dir_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統'
files = {
    'C50110-INV-02': 'C50110-INV-02 進出貨作業管理辦法(3.0版).doc',
    'C50110-INV-02-01': 'C50110-INV-02-01 儲槽進出貨作業方法(3.1版).doc'
}

for prefix, file in files.items():
    doc_path = os.path.join(dir_path, file)
    try:
        doc = word.Documents.Open(doc_path)
        text = doc.Content.Text
        doc.Close()
        with open(f'C:\GOOGLE ANGET\{prefix}.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Extracted text for {prefix}')
    except Exception as e:
        print(f'Error extracting {doc_path}: {e}')

word.Quit()
