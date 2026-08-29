with open('C:\\GOOGLE ANGET\\IPAHQ排程\\generate_3in1.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the end of the program — everything after "if __name__ == '__main__':\n    main()\n" is dead
marker = "if __name__ == '__main__':\n    main()\n"
idx = content.find(marker)
if idx != -1:
    content = content[:idx + len(marker)]
    print('Truncated at marker. File now has', content.count('\n'), 'lines')
else:
    print('Marker not found!')

with open('C:\\GOOGLE ANGET\\IPAHQ排程\\generate_3in1.py', 'w', encoding='utf-8') as f:
    f.write(content)
