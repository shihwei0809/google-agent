import sys

with open(r'C:\GOOGLE ANGET\勝一三合一單產生系統\main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Remove COA and GCP buttons (robust substring match)
    if '上傳 COA 截圖' in line and 'tk.Button' in line: continue
    if '貼上 COA 截圖' in line and 'tk.Button' in line: continue
    if '設定 GCP 金鑰' in line and 'tk.Button' in line: continue
    
    # Remove expected/revised time inputs
    if 'text="預計到廠時間:"' in line and 'tk.Label' in line: continue
    if 'text="修正到廠時間:"' in line and 'tk.Label' in line: continue
    if 'self.batch_expected_var = tk.StringVar()' in line: continue
    if 'self.batch_revised_var = tk.StringVar()' in line: continue
    if 'self.batch_expected_entry =' in line: continue
    if 'self.batch_revised_entry =' in line: continue
    if 'self.batch_expected_entry.pack' in line: continue
    if 'self.batch_revised_entry.pack' in line: continue
    if 'command=lambda: self.apply_batch_to_all(self.batch_expected_var' in line: continue
    if 'command=lambda: self.apply_batch_to_all(self.batch_revised_var' in line: continue
    
    new_lines.append(line)

with open(r'C:\GOOGLE ANGET\勝一三合一單產生系統\main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Final robust cleanup done")
