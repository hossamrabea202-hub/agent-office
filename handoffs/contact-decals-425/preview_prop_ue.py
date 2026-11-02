# #425 in-level preview of one prop (index from place_report.txt):  <i> spawn  |  <i> <name> [dist]  (locked-exposure shot -> cd425_<i>_<name>.png)
# Remove the spawned cards afterwards with place_contact425_ue.py --remove.
import sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/contact-decals-425/'
sys.path.insert(0, H[:-1]); import importlib, lookdev_cap; importlib.reload(lookdev_cap)
g = {'__name__': 'x'}; exec(open(H + 'place_contact425_ue.py', encoding='utf-8').read().split("if '--remove' in args")[0], g)
rows = g['plan'](); i = int(sys.argv[1]); r = rows[i]; o, nrm = r[2], r[4][2]
if sys.argv[2] == 'spawn': print('spawned', len(g['spawn'](r)))
else:
    DIST = float(sys.argv[3]) if len(sys.argv) > 3 else 170.0
    cam = o + nrm * DIST + unreal.Vector(0, 0, 10.0) + unreal.Vector(-nrm.y, nrm.x, 0) * 45.0
    lookdev_cap.shot(H + 'cd425_%d_%s.png' % (i, sys.argv[2]), cam, o + unreal.Vector(0, 0, 15.0), 1.5, 50 if DIST < 200 else 65)
