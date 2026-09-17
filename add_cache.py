import codecs
with codecs.open(r'd:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\server.py', 'a', 'utf-8-sig') as f:
    f.write('\n@app.get("/api/test_cache")\ndef test_cache():\n    return {"len": len(COA_FILE_CACHE)}\n')
