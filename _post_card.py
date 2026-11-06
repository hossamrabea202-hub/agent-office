import subprocess
r = subprocess.run(['gh', 'issue', 'create', '--repo', 'hossamrabea202-hub/agent-office', '--title',
                    'AAA redesign: satchel + Book of Skills pickup reveal (replaces #231) - laptop i5 / any agent',
                    '--body-file', r'C:\Users\hossa\Documents\agent-office\_card_mg.md'],
                   capture_output=True, text=True, creationflags=0x08000000)
open(r'C:\Users\hossa\Documents\agent-office\_post_card.txt', 'w').write('%s\n%s\n%s' % (r.returncode, r.stdout, r.stderr))
print('CARD', r.returncode, r.stdout.strip(), r.stderr[-300:])
