with open('app.py', encoding='utf-8') as f:
    content = f.read()

old = '    def hex_rgb(c):\n        return f"{c.red:02X}{c.green:02X}{c.blue:02X}"'
new = '    def hex_rgb(c):\n        return f"{c[0]:02X}{c[1]:02X}{c[2]:02X}"'

if old in content:
    content = content.replace(old, new)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed hex_rgb')
else:
    print('Pattern not found, checking current hex_rgb...')
    idx = content.find('def hex_rgb')
    print(repr(content[idx:idx+120]))
