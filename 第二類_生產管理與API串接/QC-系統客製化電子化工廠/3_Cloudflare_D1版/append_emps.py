path_sql = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\schema.sql'
path_emps = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\emps_insert.sql'

with open(path_sql, 'r', encoding='utf-8') as f:
    sql = f.read()

with open(path_emps, 'r', encoding='utf-8') as f:
    emps = f.read()

if "INSERT OR IGNORE INTO Employees" not in sql:
    sql += "\n\n" + emps

with open(path_sql, 'w', encoding='utf-8') as f:
    f.write(sql)
