path = r'D:\GOOGLE ANGET\三合一單網頁架機伺服器\server.py'

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '                            src_wb_l.close()\n                        except Exception as e:\n                            print(f"[COA Lorry Extraction Error] {e}")',
    '                                src_wb_l.close()\n                            except Exception as e:\n                                print(f"[COA Lorry Extraction Error] {e}")'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
