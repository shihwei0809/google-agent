import win32com.client, os, io
word = win32com.client.Dispatch('Word.Application')
word.Visible = False
doc = word.Documents.Open(r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\C50110-INV-02-01 儲槽進出貨作業方法(3.1版).doc')
text = doc.Content.Text
doc.Close()
word.Quit()
with open(r'C:\GOOGLE ANGET\temp_doc.txt', 'w', encoding='utf-8') as f:
    f.write(text)
