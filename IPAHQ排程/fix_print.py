with open('C:\\GOOGLE ANGET\\IPAHQ排程\\generate_3in1.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the OLD print (SUCCESS:...) line and replace with output_path print
old_print = '        print(f"SUCCESS:{matched_loc}:{tank_no}")'
new_print = '        # Print the actual file path so Node.js can download it\n        print(output_path)'

if old_print in content:
    content = content.replace(old_print, new_print)
    print('Fixed OLD print statement')
elif 'print(output_path)' in content:
    print('Already fixed')
else:
    print('Not found - check manually')

with open('C:\\GOOGLE ANGET\\IPAHQ排程\\generate_3in1.py', 'w', encoding='utf-8') as f:
    f.write(content)
