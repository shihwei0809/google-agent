path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_cfg = """      await env.DB.prepare("INSERT OR IGNORE INTO System_Config (config_key, config_value) VALUES ('OPTIONS_JUDGE_RESULTS', 'PASS:合格放行, FAIL:不合格退回')").run();"""
new_cfg = """      await env.DB.prepare("INSERT OR IGNORE INTO System_Config (config_key, config_value) VALUES ('OPTIONS_JUDGE_RESULTS', 'PASS:合格放行, FAIL:不合格退回')").run();
      await env.DB.prepare("INSERT OR IGNORE INTO System_Config (config_key, config_value) VALUES ('T100_IGNORE_PRODUCTS', 'IPAHQ')").run();"""

text = text.replace(old_cfg, new_cfg)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
