import sys
import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the dictionary mapping
content = content.replace('"tank_var": tank_var,', '"qty_var": qty_var,')

# Fix population logic from records
content = content.replace('if "tank_var" in row_e and rec.get("tank"):', 'if "qty_var" in row_e and rec.get("qty"):')
content = content.replace('row_e["tank_var"].set(rec["tank"])', 'row_e["qty_var"].set(rec["qty"])')

# Fix UI clearing logic
content = content.replace('entry["tank_var"].set("")', 'entry["qty_var"].set("")')

# Fix on_batch_change logic which used to calculate tank
# Def signature: def on_batch_change(self, batch_var, tank_var):
# We just disable on_batch_change since we don't calculate tank anymore
content = content.replace('tank = get_tank_from_batch(batch)', 'tank = ""')
# And just don't set it if it's qty_var. Or let's rename it to qty_var in the params
content = content.replace('def on_batch_change(self, batch_var, tank_var):', 'def on_batch_change(self, batch_var, qty_var):')
content = content.replace('tank_var.set(tank)', '# qty_var.set(tank) # no auto calculation for qty')

# Fix bindings
content = content.replace('lambda *args: self.on_batch_change(batch_var, tank_var)', 'lambda *args: self.on_batch_change(batch_var, qty_var)')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
