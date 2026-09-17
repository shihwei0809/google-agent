import codecs
def get_coa_logic_local():
    with codecs.open(r'd:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8-sig') as f:
        lines = f.readlines()
    ret = []
    in_loop = False
    for line in lines:
        if 'for file_path in file_paths:' in line:
            in_loop = True
        if in_loop:
            ret.append(line.rstrip())
            if 'except Exception as e' in line:
                break
    return ret

def get_coa_logic_server():
    with codecs.open(r'd:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\server.py', 'r', 'utf-8-sig') as f:
        lines = f.readlines()
    ret = []
    in_loop = False
    for line in lines:
        if 'for coa_file in COA_FILE_CACHE:' in line:
            in_loop = True
        if in_loop:
            ret.append(line.rstrip())
            if 'except Exception as e' in line:
                break
    return ret

print("Local length:", len(get_coa_logic_local()))
print("Server length:", len(get_coa_logic_server()))
