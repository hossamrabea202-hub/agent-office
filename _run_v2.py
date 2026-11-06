import traceback
try:
    exec(compile(open(r'C:\Users\hossa\Documents\agent-office\CastleDecals2\castle_v2_apply.py', encoding='utf-8').read(), 'v2', 'exec')); r = 'OK'
except BaseException: r = traceback.format_exc()
open(r'C:\Users\hossa\Documents\agent-office\_run_v2.txt', 'w').write(r); print('RUNV2', r[-300:])
