import subprocess
r = subprocess.run(['gh', 'issue', 'comment', '266', '--repo', 'hossamrabea202-hub/agent-office', '--body-file', r'C:\Users\hossa\Documents\agent-office\_c266.md'], capture_output=True, text=True, creationflags=0x08000000)
open(r'C:\Users\hossa\Documents\agent-office\_post_c266.txt', 'w').write('%s\n%s\n%s' % (r.returncode, r.stdout, r.stderr))
