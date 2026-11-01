# Vesna #380 step 1: DRY RUN (changes nothing). Run from Unreal's Python box: type this file's full path + Enter.
import sys, os, unreal
R = r'C:\Users\hossa\Documents\agent-office\handoffs\vesna-trade-361\build'
p = os.path.join(R, 'setup_vesnatrade_ue.py'); sys.argv = ['x']
src = open(p, encoding='utf-8').read()
exec(compile(src, p, 'exec'), {'__name__': '__main__', '__file__': p})
rep = open(os.path.join(R, 'setup_vesnatrade.txt'), encoding='utf-8', errors='replace').read()
unreal.log('VESNA DRY RUN REPORT\n' + rep)
unreal.log('VESNA: ' + ('STOP: something is MISSING, see above' if any(l.startswith('MISSING') for l in rep.splitlines()) else 'OK -> run p2_apply.py'))
