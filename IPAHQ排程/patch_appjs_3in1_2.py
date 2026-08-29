import re

file_path = 'C:/GOOGLE ANGET/IPAHQ排程/public/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Replace download3in1 function
old_download = """window.download3in1 = async function(id) {
  try {
    const res = await fetch(`/api/orders/${id}/tsmc-3in1`);"""

# Try regex instead for robustness
js = re.sub(
    r'window\.download3in1\s*=\s*async\s*function\(id\)\s*\{\s*try\s*\{\s*const\s*res\s*=\s*await\s*fetch\(`/api/orders/\$\{id\}/tsmc-3in1`\);',
    r"""window.download3in1 = async function(id, batch) {
  if (id === 'null' || !id) {
      id = 'batch:' + batch;
  }
  try {
    const res = await fetch(`/api/orders/${encodeURIComponent(id)}/tsmc-3in1`);""",
    js
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("Regex replace applied.")
