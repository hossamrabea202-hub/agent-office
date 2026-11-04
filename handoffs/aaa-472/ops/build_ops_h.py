# #472 fix H (i5): the rest of the lost literals t3d_lost_all.js found, values only. Kept: 0 that became the C++ default 1 on an Add / Subtract (F12's bug), the swarm's spawn offsets, and
# 3 false flags that came back true. Left out on purpose: name collisions (BP_Crossbow, BP_CommanderHUD), later tuning (BP_DayNight, BPC_TentacleStrike, BPC_CastleScroll, ORE / FOOD text scale),
# attach bWeldSimulatedBodies (does nothing without physics), MakeColor alpha (not sure of the intent).   python build_ops_h.py <lost.json> <paths.json>
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
lost, paths = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
KEEP_FN = ('Add_DoubleDouble', 'Subtract_DoubleDouble', 'Add_IntInt')
BOOLS = {('wxRainLoop20', 'bAutoDestroy'), ('mpFade63', 'DestroyOwnerAfterFade'), ('vInputGameUI85', 'bHideCursorDuringCapture')}
out = {}
for bp, rows in lost.items():
    if bp in ('BP_RealmWasp', 'BP_HalfHorseZombie', 'BP_Crossbow', 'BP_CommanderHUD', 'BP_DayNight', 'BPC_TentacleStrike', 'BPC_CastleScroll', 'BP_ZombieHUD'): continue
    keep = []
    for n, pin, want, have, fn, src in rows:
        zero = fn in KEEP_FN and pin == 'B' and float(want) == 0 and float(have) == 1
        swarm = bp == 'BP_ZombieWaveManager' and fn == 'RandomFloatInRange'
        if zero or swarm or (n, pin) in BOOLS or any(n == b[0] and pin.startswith(b[1][:12]) for b in BOOLS): keep.append([n, pin, want])
    if keep: out[bp] = keep
for bp, keep in out.items():
    name = 'ops_H_%s.json' % bp
    json.dump({'fix': 'H', 'bp': paths[bp], 'vars': [], 'nodes': [], 'links': [], 'remove': [], 'set_live': keep, 'dx': 0, 'dy': 0}, open(os.path.join(HERE, name), 'w'), indent=0)
    print(name, len(keep), [k[0] + '.' + k[1] for k in keep][:6])
print(len(out), 'Blueprints,', sum(len(v) for v in out.values()), 'values')
