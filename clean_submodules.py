import subprocess
out = subprocess.check_output(['git', 'ls-files', '-s'])
for line in out.split(b'\n'):
    if line.startswith(b'160000'):
        path = line.split(b'\t')[1].strip()
        if path.startswith(b'\"'):
            path = path[1:-1].decode('unicode_escape').encode('latin1').decode('utf-8')
        else:
            path = path.decode('utf-8')
        print('Removing:', path)
        subprocess.call(['git', 'rm', '--cached', path])
