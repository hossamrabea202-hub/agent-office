# #317 Colossus stands outside (TGA, 2026-10-31; owner W:). Paste + manifest for BP_ZombieWallBreaker (10-30b export).
# Cause: BeginPlay scales the breaker x3.9-5.8 but keeps the 32 cm capsule radius, so it is 125-186 cm "wide": it cannot
#   get within 380 cm of its breach spot's AttackPoint against the wall (BreakerThink only smashes inside 380) and it
#   cannot fit the breach hole afterwards, so it stands outside.
# Fix 1: capsule radius = 45 / GiantScale (45 cm in the world at any size; the body may clip the wall a little).
# Fix 2: stuck watchdog in BreakerThink's "still far" branch: if it moves slower than 20 cm/s for 8 ticks (4 s), it is
#   teleported 300 cm short of the AttackPoint on its own side (same height), so the smash always starts.
#   python gen317.py
import os, sys, json
sys.dont_write_bytecode = True
HERE317 = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE317, '..', 'farm-223', 'gen223.py'), encoding='utf-8').read()
_g = _src[:_src.index('# ================================================================ BP_FarmPlot')].replace('HERE = os.path.dirname(os.path.abspath(__file__))', 'HERE = HERE317')
__file__ = os.path.join(HERE317, '..', 'farm-223', 'gen223.py'); exec(_g); __file__ = os.path.join(HERE317, 'gen317.py')
HERE = HERE317

G = Graph(); b = B(G, 'cz'); b.imp = B(G, 'czQ')
gs = b.get('GiantScale', D('v'), 0, 0)
cap = b.d2('Divide_DoubleDouble', None, gs, 200, 0, da='45.0')                         # -> BP_CapS.InRadius (manifest)
# watchdog (BreakerThink far branch)
vel = b.call(ACT, 'GetVelocity', [V('ReturnValue', out=True)], 0, 300, pure=True, const=True, tag='Vel')
spd = b.math('VSize', [(V('A'), (vel, 'ReturnValue'))], D('ReturnValue', out=True), 200, 300)
slow = b.branch(b.dcmp('Less_DoubleDouble', spd, None, 400, 400, db='20.0'), 600, 300, 'IfSlow')
inc = b.set('StuckTicks', it('v'), b.i2('Add_IntInt', b.get('StuckTicks', it('v'), 700, 600), None, 900, 600, db='1'), 900, 300)
G.link(slow, 'then', inc, 'execute')
stuck = b.branch(b.icmp('GreaterEqual_IntInt', b.get('StuckTicks', it('v'), 1100, 600), None, 1300, 600, db='8'), 1200, 300, 'IfStuck')
G.link(inc, 'then', stuck, 'execute')
me = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1200, 800, pure=True, const=True, tag='Me')
away = b.v2('Subtract_VectorVector', (me, 'ReturnValue'), None, 1400, 800)              # B <- TK_APL (manifest)
nrm = b.math('Normal', [(V('A'), away), (fl('Tolerance', default='0.000100'), None)], V('ReturnValue', out=True), 1600, 800)
off = b.math('Multiply_VectorFloat', [(V('A'), nrm), (fl('B', default='300.0'), None)], V('ReturnValue', out=True), 1800, 800)
dst = b.v2('Add_VectorVector', off, None, 2000, 800)                                    # B <- TK_APL (manifest)
db_ = b.brk(dst, 2200, 800); mb = b.brk((me, 'ReturnValue'), 2200, 1000)
goal = b.vec(db_['X'], db_['Y'], mb['Z'], 2400, 900)
rot = b.call(ACT, 'K2_GetActorRotation', [st('ReturnValue', ROT, out=True)], 2400, 1100, pure=True, const=True, tag='Rot')
tp = b.call(ACT, 'K2_TeleportTo', [V('DestLocation'), st('DestRotation', ROT, default='0, 0, 0'), bo('ReturnValue', out=True)], 1500, 300, tag='Tele')
b.wire(goal, tp, 'DestLocation'); b.wire((rot, 'ReturnValue'), tp, 'DestRotation'); G.link(stuck, 'then', tp, 'execute')
r0 = b.set('StuckTicks', it('v', default='0'), None, 1800, 300); G.link(tp, 'then', r0, 'execute')
r1 = b.set('StuckTicks', it('v', default='0'), None, 900, 100); G.link(slow, 'else', r1, 'execute')   # moving: reset, then walk
write('BP_ZombieWallBreaker_Fix317_graph.txt', G)
nm = lambda t: t if isinstance(t, str) else t[0]
man = {'blueprint': 'BP_ZombieWallBreaker', 'pastes': ['BP_ZombieWallBreaker_Fix317_graph.txt'], 'rewires': [
    {'from': '%s.ReturnValue' % nm(cap), 'to': 'BP_CapS.InRadius', 'note': 'capsule radius 45 / GiantScale (was 32 -> 125-186 cm when scaled)'},
    {'from': 'TK_IfFar.then', 'to': '%s.execute' % slow, 'replace': True, 'note': 'still far: check if stuck first (was -> MV_Go)'},
    {'from': '%s.else' % stuck, 'to': 'MV_Go.execute', 'note': 'not stuck long enough: keep walking'},
    {'from': '%s.then' % r1, 'to': 'MV_Go.execute', 'note': 'moving fine: keep walking'},
    {'from': 'TK_APL.ReturnValue', 'to': '%s.B' % nm(away), 'note': 'AttackPoint location'},
    {'from': 'TK_APL.ReturnValue', 'to': '%s.B' % nm(dst), 'note': 'AttackPoint location'}]}
json.dump(man, open(os.path.join(HERE, 'manifest_wallbreaker.json'), 'w'), indent=1)
print('gen317 ok', slow, stuck, nm(cap))
