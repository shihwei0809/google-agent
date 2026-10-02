import os, sys

def fix():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Just rip out the gen_lorry_var check and make it unconditional
    # Actually, let's just make it do the logic no matter what, and let's add a massive debug dump!
    
    # I will replace the "if getattr(self, 'gen_lorry_var', None) and self.gen_lorry_var.get():" with "if True:"
    content = content.replace('if getattr(self, "gen_lorry_var", None) and self.gen_lorry_var.get():', 'if True:')
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("PATCHED UNCONDITIONAL")
fix()
