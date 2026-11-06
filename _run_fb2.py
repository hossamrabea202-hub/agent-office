import traceback, runpy
try:
    runpy.run_path(r'C:\Users\hossa\Downloads\flesh-brute-prepared\import_fleshbrute_master2.py', run_name='__main__'); r = 'OK'
except BaseException: r = traceback.format_exc()
open(r'C:\Users\hossa\Documents\agent-office\_run_fb2.txt', 'w').write(r); print('RUNFB', r[-300:])
