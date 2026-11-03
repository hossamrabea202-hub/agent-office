# #472 fix E (i5): BP_FleshBrute's Think, the same crowd fixes as BP_Zombie's fix A (no registry: it is not a BP_Zombie, so the manager's counts never included it).
import json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'fixes'))
import build_472 as A
from build_472 import *
P_B = '/Game/CastleDefender/Characters/Enemies/FleshBrute/BP_FleshBrute'
BRUTE = BPC(P_B, 'BP_FleshBrute')
STRIP = ['CX_502', 'CX_398', 'CX_57', 'G_GetGate', 'CX_81']
def gen(live):
    L = live_links(live); G = A.Graph(); b = bpkit.B(G, 'zb472e'); rw = []
    def retarget(old, new):
        for n, p in L[(old, 'ReturnValue')]: rw.append(R(new[0] + '.' + new[1], '%s.%s' % (n, p), 'was ' + old))
    f = b.actor_of(P_WM, WM, 0, 0); s = b.set('WMRef', obv(WM), (f, 'ReturnValue'), 300, 0); G.link(f, 'then', s, 'execute')
    first = L[('K2Node_Event_ZB0', 'then')][0][0]
    rw += [R('K2Node_Event_ZB0.then', f + '.execute'), R(s + '.then', first + '.execute')]
    wm = b.get('WMRef', obv(WM), 0, 1300)
    sc = b.getm('SoldierCache', WM, arr(obv(SOLDIER)), wm, 300, 1300); gc = b.getm('GateCache', WM, obv(GATE), wm, 300, 1600)
    rw += [R('CX_501.then', 'CX_503.Exec', 'skip the soldier scan'), R(sc[0] + '.SoldierCache', 'CX_503.Array'),
           R('CX_6.else', 'CX_400.execute'), R('K2Node_IfThenElse_ZB25.else', 'G_AtGate.execute'), R('CX_78.then', '%s.execute' % L[('CX_81', 'then')][0][0])]
    retarget('CX_398', wm); retarget('CX_81', wm); retarget('CX_57', gc); retarget('G_GetGate', gc)
    vs = b.valid(None, 0, 1900); v1 = b.branch(vs, 300, 1800, tag='IfSoldier')
    rw += [R('CX_503.LoopBody', v1 + '.execute'), R(v1 + '.then', 'CX_521.execute'), {'from': 'CX_503.Array Element', 'to': vs[0] + '.Object'}]
    same = eqobj(b, None, b.get('LastMoveGoal', ACTV, 0, 2500), 300, 2400)
    vel = b.call(ACT, 'GetVelocity', [V('ReturnValue', out=True)], 0, 2650, pure=True, const=True, tag='Vel')
    spd = b.math('VSize', [(V('A'), (vel, 'ReturnValue'))], D('ReturnValue', out=True), 300, 2650)
    mov = b.dcmp('Greater_DoubleDouble', spd, None, 550, 2650, db='5.0')
    age = b.d2('Subtract_DoubleDouble', b.now(0, 2850), b.get('LastMoveAt', DBL, 0, 2950), 300, 2850)
    fresh = b.dcmp('Less_DoubleDouble', age, None, 550, 2850, db='2.0')
    skip = b.b2('BooleanAND', b.b2('BooleanAND', same, mov, 800, 2500), fresh, 1050, 2600)
    im = b.branch(b.bnot(skip, 1300, 2600), 1550, 2400, tag='IfMoveNeeded')
    sg = b.set('LastMoveGoal', ACTV, None, 1900, 2400); st_ = b.set('LastMoveAt', DBL, b.now(1900, 2600), 2250, 2400); G.link(sg, 'then', st_, 'execute')
    gsrc = L[('K2Node_CallFunction_ZB28', 'Goal')][0]
    rw += [R('G_AtGate.else', im + '.execute'), R(im + '.then', 'K2Node_CallFunction_ZB28.execute'), R('K2Node_CallFunction_ZB28.then', sg + '.execute'),
           {'from': '%s.%s' % gsrc, 'to': same[0] + '.A'}, {'from': '%s.%s' % gsrc, 'to': sg + '.LastMoveGoal'}]
    def guard(srcs, nxt, y):
        g = b.branch(b.get('Dead', BOOL, 0, y + 150), 300, y, tag='IfDead')
        for sr in srcs: rw.append(R(sr, g + '.execute'))
        rw.append(R(g + '.else', nxt + '.execute'))
    guard(['CX_53.then'], 'CX_54', 3200); guard(['CX_434.then'], 'CX_437', 3500); guard(['CX_448.then'], 'CX_458', 3800); guard(['CX_93.then', 'CX_78.else'], 'CX_94', 4100)
    G.render(); json.dump({'blueprint': 'BP_FleshBrute', 'pastes': [], 'rewires': rw}, open(os.path.join(A.HERE, 'brute_manifest.json'), 'w'), indent=1)
