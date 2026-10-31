# #322 Flesh Brutes ("big mouth") in the waves (adjustedfilm, 2026-10-31; owner W:). Part 1 of the card: waves + removing the
# brutes placed at the gate. (Animation polish = part 2, needs the BP_FleshBrute export, request filed.)
#   "<blender python>" -I gen_brute322.py -> BP_BruteDirector_graph.txt, VARIABLES_BPVar.txt, VARIABLES.md
# BP_BruteDirector (one per level, placed by setup_brute322_ue.py). No edit to BP_ZombieWaveManager:
#   BeginPlay   every BP_ZombieWaveManager in the level -> Managers; LastWave[i] = its Wave now (a loaded game doesn't
#               trigger old waves); Pending[i] = 0; starts BrutePoll every 1 s (a timer by name: no self-call nodes, #254).
#   BrutePoll   for each manager i: a new wave w (Wave changed) from FromWave (3) on -> Pending[i] += min(1 + (w - FromWave)
#               / Every (2), MaxPerWave (4)): wave 3-4 = 1 brute, 5-6 = 2, 7-8 = 3, 9+ = 4. While Pending[i] > 0, one brute
#               every Stagger (9 s), so they come inside the wave, not as a clump: spawned at that manager's
#               HorseSpawnLocation (where its half-horse zombies come from) + random 3 m, 1.5 m up; falls back to the
#               manager's own location if that vector is zero.
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE

CLSV = lambda: {'name': 'v', 'cat': 'class', 'obj': ACT}
OBJV = lambda c: ob('v', c)


class B(bpkit.B):
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def timer_ev(s, fn, interval, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default='true'),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n
    def foreach_var(s, var, cls, x, y):
        n = s.foreach(cls, x, y); s.wire(s.get(var, arr(OBJV(cls)), x - 200, y + 200), n, 'Array'); return n


G = Graph(); b = B(G, 'bd')
g = b.get
# ================================================================================================= BeginPlay
G.node('bdBeginPlay', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT}, ex('then', True)], 0, 0)
ga = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(P_WM)), arr(ob('OutActors', WM, out=True))], 300, 0, tag='AllWaveManagers')
G.link('bdBeginPlay', 'then', ga, 'execute')
sm = b.set('Managers', arr(OBJV(WM)), (ga, 'OutActors'), 600, 0); G.link(ga, 'then', sm, 'execute')
fe = b.foreach_var('Managers', WM, 900, 0); G.link(sm, 'then', fe, 'Exec')
a1 = b.aadd('LastWave', INT, b.getm('Wave', WM, INT, (fe, 'Array Element'), 1100, 300), 1200, 0); G.link(fe, 'LoopBody', a1, 'execute')
a2 = b.aadd('Pending', INT, None, 1500, 0); G.link(a1, 'then', a2, 'execute')
a3 = b.aadd('NextAt', DBL, None, 1800, 0); G.link(a2, 'then', a3, 'execute')
G.link(fe, 'Completed', b.timer_ev('BrutePoll', '1.0', 1300, 400), 'execute')

# ================================================================================================= BrutePoll
Y = 1000
b.event('BrutePoll', [], 0, Y)
now = b.now(200, Y + 1600)
fl_ = b.foreach_var('Managers', WM, 300, Y); G.link('BrutePoll', 'then', fl_, 'Exec')
mgr, idx = (fl_, 'Array Element'), (fl_, 'Array Index')
w = b.getm('Wave', WM, INT, mgr, 500, Y + 300)
okm = b.branch(b.valid(mgr, 600, Y + 200), 600, Y, tag='IfMgr'); G.link(fl_, 'LoopBody', okm, 'execute')
# new wave?
neww = b.icmp('NotEqual_IntInt', w, b.aget('LastWave', INT, idx, 700, Y + 450), 900, Y + 400)
bn = b.branch(neww, 900, Y, tag='IfNewWave'); G.link(okm, 'then', bn, 'execute')
sl = b.aset('LastWave', INT, idx, w, 1100, Y - 250); G.link(bn, 'then', sl, 'execute')
bfrom = b.branch(b.icmp('GreaterEqual_IntInt', w, g('FromWave', INT, 1200, Y + 300), 1400, Y + 300), 1400, Y - 250, tag='IfBruteWave'); G.link(sl, 'then', bfrom, 'execute')
cnt = b.math('Min', [(it('A', default='0'), b.i2('Add_IntInt', b.i2('Divide_IntInt', b.i2('Subtract_IntInt', w, g('FromWave', INT, 1500, Y + 550), 1700, Y + 500),
                                                                                   g('Every', INT, 1700, Y + 650), 1900, Y + 550), None, 2100, Y + 550, db='1')),
                      (it('B', default='0'), g('MaxPerWave', INT, 2100, Y + 700))], it('ReturnValue', out=True), 2300, Y + 600)
sp = b.aset('Pending', INT, idx, b.i2('Add_IntInt', b.aget('Pending', INT, idx, 2100, Y + 850), cnt, 2500, Y + 750), 1700, Y - 250)
G.link(bfrom, 'then', sp, 'execute')
mg = b.seq('bdAfterWave', 1, 2100, Y); G.link(bn, 'else', mg, 'execute'); G.link(bfrom, 'else', mg, 'execute'); G.link(sp, 'then', mg, 'execute')
# spawn one if pending and due
due = b.b2('BooleanAND', b.icmp('Greater_IntInt', b.aget('Pending', INT, idx, 2200, Y + 1000), None, 2400, Y + 1000, db='0'),
           b.dcmp('GreaterEqual_DoubleDouble', now, b.aget('NextAt', DBL, idx, 2200, Y + 1150), 2400, Y + 1150), 2600, Y + 1050)
bdue = b.branch(due, 2400, Y, tag='IfDue'); G.link(mg, 'then_0', bdue, 'execute')
hl = b.getm('HorseSpawnLocation', WM, VECT, mgr, 2600, Y + 1300)
zero = b.math('EqualEqual_VectorVector', [(V('A'), hl), (V('B'), None), (fl('ErrorTolerance', default='1.000000'), None)], bo('ReturnValue', out=True), 2800, Y + 1300)
base = b.selvec(None, hl, zero, 3000, Y + 1350)
b.wire((b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 2800, Y + 1500, target=mgr, pure=True, const=True, tag='MgrLoc'), 'ReturnValue'), base[0], 'A')
loc = b.v2('Add_VectorVector', base, b.vec(b.rnd('-300.0', '300.0', 3000, Y + 1550), b.rnd('-300.0', '300.0', 3000, Y + 1650), None, 3200, Y + 1600, dz='150.0'), 3400, Y + 1450)
xf = transform(b, loc, 3600, Y + 1450)
spn = b.name('SpawnBrute')
G.node(spn, 'K2Node_SpawnActorFromClass', ['AdvancedPinDisplay=Hidden'],
       [ex(), ex('then', True), CLSPIN('Class', ACT, None), ob('ReturnValue', ACT, out=True), st('SpawnTransform', XFORM),
        {'name': 'CollisionHandlingOverride', 'cat': 'byte', 'obj': ENUM('ESpawnActorCollisionHandlingMethod'), 'default': 'AdjustIfPossibleButAlwaysSpawn'},
        {'name': 'TransformScaleMethod', 'cat': 'byte', 'obj': ENUM('ESpawnActorScaleMethod'), 'default': 'SelectDefaultAtRuntime', 'advanced': True},
        dict(ob('Owner', ACT), advanced=True), ob('Instigator', PAWN)], 2700, Y)
b.wire(g('BruteClass', CLSV(), 2500, Y + 200), spn, 'Class'); b.wire(xf, spn, 'SpawnTransform')
bcls = b.branch(b.math('IsValidClass', [({'name': 'Class', 'cat': 'class', 'obj': OBJ}, g('BruteClass', CLSV(), 2500, Y + 350))], bo('ReturnValue', out=True), 2700, Y + 350),
                2550, Y - 200, tag='IfClass')
G.link(bdue, 'then', bcls, 'execute'); G.link(bcls, 'then', spn, 'execute')
dp = b.aset('Pending', INT, idx, b.i2('Subtract_IntInt', b.aget('Pending', INT, idx, 3000, Y - 400), None, 3200, Y - 400, db='1'), 3000, Y - 200)
G.link(spn, 'then', dp, 'execute')
na = b.aset('NextAt', DBL, idx, b.add(now, g('Stagger', DBL, 3300, Y - 350), 3500, Y - 400), 3300, Y - 200)
G.link(dp, 'then', na, 'execute')

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
names = [n[0] for n in G.nodes]
if bad or len(names) != len(set(names)): raise SystemExit('bad links %s / dup %s' % (bad[:10], [n for n in names if names.count(n) > 1][:5]))
open(os.path.join(HERE, 'BP_BruteDirector_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BP_BruteDirector_graph.txt: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ================================================================================================= BPVar lines
VARS = [('FromWave', 'PinCategory="int"', '3', 'first wave with a brute'), ('Every', 'PinCategory="int"', '2', '+1 brute every N waves after that'),
        ('MaxPerWave', 'PinCategory="int"', '4', 'cap per wave per wave manager'),
        ('Stagger', 'PinCategory="real",PinSubCategory="double"', '9.0', 's between brutes of the same wave'),
        ('BruteClass', 'PinCategory="class",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'"', '', 'set by the setup script to BP_FleshBrute'),
        ('Managers', 'PinCategory="object",PinSubCategoryObject="%s",ContainerType=Array' % WM.strip('"').replace("'", "\\'") if False else
         'PinCategory="object",PinSubCategoryObject="/Script/Engine.BlueprintGeneratedClass\'/Game/CastleDefender/Gameplay/Castle/BP_ZombieWaveManager.BP_ZombieWaveManager_C\'",ContainerType=Array', '', 'state'),
        ('LastWave', 'PinCategory="int",ContainerType=Array', '', 'state'), ('Pending', 'PinCategory="int",ContainerType=Array', '', 'state'),
        ('NextAt', 'PinCategory="real",PinSubCategory="double",ContainerType=Array', '', 'state')]
bpv = lambda n, t, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'brute322/' + n).hex.upper(), t, n, d)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# #322 BP_BruteDirector - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' + '\n'.join(bpv(*v[:3]) for v in VARS) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #322 BP_BruteDirector variables\n\n| Name | Default | Meaning |\n|---|---|---|\n')
    for n, _t, d, m in VARS: f.write('| %s | %s | %s |\n' % (n, d or '-', m))
print('BPVar lines: %d' % len(VARS))
