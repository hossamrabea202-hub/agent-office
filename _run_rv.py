import runpy, traceback, sys
P = r'C:\Users\hossa\Documents\agent-office\_latest\handoffs\reveal-aaa-268\setup_reveal268_ue.py'
sys.argv = [P]
try: runpy.run_path(P, run_name='__main__'); r = 'OK'
except BaseException: r = traceback.format_exc()[-1500:]
try: r += '\n---\n' + open(r'C:\Users\hossa\Documents\agent-office\_latest\handoffs\reveal-aaa-268\setup_reveal268.txt').read()[-2500:]
except Exception: pass
open(r'C:\Users\hossa\Documents\agent-office\_run_rv.txt', 'w').write(r); print('RUNRV', r[:200])
