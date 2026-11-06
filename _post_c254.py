import subprocess, unreal
r = subprocess.run(['gh', 'issue', 'comment', '254', '--repo', 'hossamrabea202-hub/agent-office', '--body-file', r'C:\Users\hossa\Documents\agent-office\_c254.md'], capture_output=True, text=True, creationflags=0x08000000)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(r'C:\Users\hossa\Documents\agent-office\_post_c254.txt', 'w').write('%s %s %s' % (r.returncode, r.stdout, r.stderr))
