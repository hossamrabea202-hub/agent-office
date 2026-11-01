# Offline check (#411): for every function the generated graph calls, compare its pin names with the same function in
# today's real exports (BP_ZombieHUD / BP_ArmoryHUD / BPC_VesnaTrade). Prints mismatches; silent functions = not found.
import re, sys, glob
sys.path.insert(0, 'castle-scroll-411')
from t3d_parse import parse, member
gen = parse('castle-scroll-411/build/BPC_CastleScroll_graph.txt')
ref = {}
for f in glob.glob('exports/adjustedfilm/*/*.txt'):
    if 'table' in f: continue
    for n in parse(f).values():
        m = member(n)
        if m and m not in ref: ref[m] = sorted(p[0] for p in n['pins'].values())
seen = set()
for n in gen.values():
    m = member(n)
    if not m or m in seen: continue
    seen.add(m)
    mine = sorted(p[0] for p in n['pins'].values())
    if m not in ref: print('NOT IN EXPORTS  %-34s %s' % (m, mine)); continue
    miss = set(mine) - set(ref[m]); extra = set(ref[m]) - set(mine)
    if miss or extra: print('DIFF %-30s mine-only %s  real-only %s' % (m, sorted(miss), sorted(extra)))
print('checked %d functions' % len(seen))
