# #472 crowd fix A (i5, 2026-11-03): one build for both Blueprints. Run it on the FRESH exports: it writes what the Master pastes.
#   python build_472.py <BP_ZombieWaveManager export> <BP_Zombie export>
# An export is the whole-BP .T3D or the EventGraph copy. Output next to this file: wm_merged.txt, zombie_merged.txt (+ pastes, manifests).
#
# BP_ZombieWaveManager (5 are placed; each one ran the Tick, so 5 zombie scans a frame):
#   - ReceiveTick goes. The NearGate count runs from a 0.25 s timer (RegNear), on the host manager only. The host is the manager
#     GetActorOfClass returns: the same one BP_CastleGateControl reads NearGate from and BP_Zombie reads GateBroken from.
#   - ZombieReg: live zombies. Zombies add themselves at BeginPlay and leave at EndPlay. RegRefresh (1 s, host) re-reads the world once
#     as the truth, because HalfHorse, RealmWasp and WallBreaker override BeginPlay without calling the parent.
#   - RegRefresh also fills SoldierCache, FarmerCache and GateCache, so the zombies stop scanning for them.
#   - WaveTick's two zombie counts read the host's ZombieReg.
# BP_Zombie:
#   - Think stagger (variance 0.25, chat 1270; nothing changes if already applied). WMRef cached at BeginPlay, EndPlay leaves the registry.
#   - Think reads SoldierCache / FarmerCache / WMRef / GateCache instead of 2 x GetAll + 4 x GetActorOf; IsValid guard in both loops.
#   - SimpleMoveToActor (a SYNCHRONOUS path search + abort) only when the target changed, the zombie stopped, or 2 s passed. The engine
#     re-paths a moving goal by itself (SetGoalActorObservation 100 uu), so nothing is lost.
#   - Dead guards after the 4 Delays that ran on a corpse (brute corpse teleport after CX_448, rate changes).
#   - 12 mesh SetPlayRate / SetPosition no-ops go: in AnimBP mode they only log "Currently in Animation Blueprint mode".
#     CX_97 stays: it runs after the death PlayAnimation, when the mesh is in single-node mode.
#   - The 28 orphan PlayAnimation nodes go (dead code from the montage conversion).
import json, os, re, subprocess, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'laptop2', 'bpgen')); sys.path.insert(0, HERE)
import bpkit
from bpkit import *
from t3d_strip import strip
HERE = os.path.dirname(os.path.abspath(__file__))      # bpkit's star import overwrites HERE
P_GATE, P_FARM = '/Game/CastleDefender/Gameplay/Castle/BP_CastleGateControl', '/Game/CastleDefender/Gameplay/Farm/BP_Farmer'
GATE, FARMER = BPC(P_GATE, 'BP_CastleGateControl'), BPC(P_FARM, 'BP_Farmer')
ACTV = ob('v', ACT)
def obv(c): return ob('v', c)
def getall(b, path, cls, x, y):
    return b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', cls, out=True))], x, y, tag='All' + path.split('/')[-1][3:])
def eqobj(b, a, c, x, y): return b.math('EqualEqual_ObjectObject', [(ob('A', OBJ), a), (ob('B', OBJ), c)], bo('ReturnValue', out=True), x, y)
def arrfn(b, member, tgt, item_pin, item, x, y, ret):
    n = b.name(member)
    b.G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="%s")' % (KARR, member)],
             [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True},
              {'name': item_pin, 'cat': 'wildcard', 'ref': True}, ret], x, y)
    b.wire(tgt, n, 'TargetArray'); b.wire(item, n, item_pin); return n
def out(G, name):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    if bad: raise SystemExit('bad links %s' % bad)
    open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render()); print(name, len(G.nodes), 'nodes')
def R(frm, to, note=None):
    d = {'from': frm, 'to': to, 'replace': True}
    if note: d['note'] = note
    return d

# ---------------------------------------------------------------- BP_ZombieWaveManager
def gen_wm():
    G = Graph(); b = bpkit.B(G, 'r472')
    # BeginPlay: host, then (host only) the two timers and a first fill
    f = b.actor_of(P_WM, WM, 0, 0); sh = b.set('RegHost', obv(WM), (f, 'ReturnValue'), 300, 0); G.link(f, 'then', sh, 'execute')
    cond = eqobj(b, b.get('RegHost', obv(WM), 600, 400), b.self_node(600, 550), 850, 450)
    ifh = b.branch(cond, 1100, 0, tag='IfHost')
    t1 = b.timer('RegNear', 1400, 0, dtime='0.25', loop=True); t2 = b.timer('RegRefresh', 1800, 0, dtime='1.0', loop=True)
    first = b.call_self('RegRefresh', [], 2200, 0, WM, tag='FirstFill')
    G.link(ifh, 'then', t1, 'execute'); G.link(t1, 'then', t2, 'execute'); G.link(t2, 'then', first, 'execute')
    b.event('RegNear', [], 0, 700)          # the old ReceiveTick chain hangs on it
    b.event('RegRefresh', [], 0, 1000)      # world truth once a second
    a1 = getall(b, P_ZOMBIE, ZOMBIE, 300, 1000); s1 = b.set('ZombieReg', arr(obv(ZOMBIE)), (a1, 'OutActors'), 650, 1000)
    a2 = getall(b, P_SOLDIER, SOLDIER, 1000, 1000); s2 = b.set('SoldierCache', arr(obv(SOLDIER)), (a2, 'OutActors'), 1350, 1000)
    a3 = getall(b, P_FARM, FARMER, 1700, 1000); s3 = b.set('FarmerCache', arr(obv(FARMER)), (a3, 'OutActors'), 2050, 1000)
    a4 = b.actor_of(P_GATE, GATE, 2400, 1000); s4 = b.set('GateCache', obv(GATE), (a4, 'ReturnValue'), 2750, 1000)
    b.chain(('RegRefresh', 'then'), a1, s1, a2, s2, a3, s3, a4, s4)
    # readers: own array for NearGate (host only), the host's array for the wave counts (all 5 run WaveTick)
    own = b.get('ZombieReg', arr(obv(ZOMBIE)), 0, 1400)
    hreg = b.getm('ZombieReg', WM, arr(obv(ZOMBIE)), b.get('RegHost', obv(WM), 0, 1600), 300, 1600)
    out(G, 'wm_paste.txt')
    json.dump({'blueprint': 'BP_ZombieWaveManager', 'note': '#472 registry, no per-frame scan', 'pastes': ['wm_paste.txt'], 'rewires': [
        R('WV_1.then', f + '.execute'), R(sh + '.then', 'WV_2.execute'), R('WV_2.then', ifh + '.execute'),
        R('RegNear.then', 'K2Node_IfThenElse_GT2.execute', 'was ReceiveTick'),
        R('K2Node_VariableSet_GT3.then', 'K2Node_MacroInstance_GT5.Exec', 'skip the scan'), R(own[0] + '.ZombieReg', 'K2Node_MacroInstance_GT5.Array'),
        R('WV_25.then', 'WV_29.execute', 'skip the scan'), R(hreg[0] + '.ZombieReg', 'WV_27.TargetArray'),
        R('WV_82.then', 'WV_85.execute', 'skip the scan'), R(hreg[0] + '.ZombieReg', 'CX_2.TargetArray')]},
        open(os.path.join(HERE, 'wm_manifest.json'), 'w'), indent=1)
WM_STRIP = ['K2Node_Event_GT0', 'K2Node_CallFunction_GT4', 'WV_26', 'CX_1']

# ---------------------------------------------------------------- BP_Zombie
ORPHANS = ['CX_23', 'CX_75', 'CX_195', 'CX_197', 'CX_201', 'CX_205', 'CX_209', 'CX_213', 'CX_217', 'CX_221', 'CX_250', 'CX_252', 'CX_256', 'CX_285', 'CX_287', 'CX_291',
           'CX_301', 'CX_324', 'CX_328', 'CX_343', 'CX_374', 'CX_376', 'CX_378', 'CX_428', 'CX_446', 'CX_453', 'K2Node_CallFunction_ZB14', 'K2Node_CallFunction_ZB15']
NOOPS = ['CX_168', 'CX_223', 'CX_258', 'CX_322', 'CX_345', 'CX_347', 'CX_356', 'CX_367', 'CX_430', 'CX_432', 'CX_435', 'CX_455']
Z_STRIP = ['CX_502', 'zfQAllFarmer1', 'CX_398', 'CX_57', 'G_GetGate', 'CX_81'] + ORPHANS + NOOPS

def live_links(t):
    """(node, pin) -> [(node, pin)] of a graph copy"""
    ids, raw = {}, []
    for m in re.finditer(r'^Begin Object .*?^End Object', t, re.S | re.M):
        n = re.search(r'Name="([^"]+)"', m.group(0)).group(1)
        for p in re.findall(r'CustomProperties Pin \((.*)\)', m.group(0)):
            pid, pn = re.search(r'PinId=(\w+)', p).group(1), re.search(r'PinName="([^"]+)"', p).group(1)
            lk = re.search(r'LinkedTo=\(([^)]*)\)', p)
            ids[pid] = (n, pn); raw.append(((n, pn), re.findall(r'\w+ ([0-9A-F]{32}),', lk.group(1)) if lk else []))
    return {k: [ids[x] for x in v if x in ids] for k, v in raw}

def gen_zombie(live):
    L = live_links(live); G = Graph(); b = bpkit.B(G, 'z472'); rw = []
    def retarget(old, new):                 # every consumer of a removed Find node reads the cached value instead
        for n, p in L[(old, 'ReturnValue')]: rw.append(R(new[0] + '.' + new[1], '%s.%s' % (n, p), 'was ' + old))
    def bypass(node, nxt):                  # whatever ran node now runs nxt
        for s_ in L[(node, 'execute')]: rw.append(R('%s.%s' % s_, nxt + '.execute', 'no-op ' + node))
    # BeginPlay
    f = b.actor_of(P_WM, WM, 0, 0); s = b.set('WMRef', obv(WM), (f, 'ReturnValue'), 300, 0)
    reg = b.getm('ZombieReg', WM, arr(obv(ZOMBIE)), (f, 'ReturnValue'), 300, 250)
    add = arrfn(b, 'Array_AddUnique', reg, 'NewItem', b.self_node(300, 400), 650, 0, it('ReturnValue', out=True, default='0'))
    b.chain(f, s, add)
    rw += [R('K2Node_Event_ZB0.then', f + '.execute'), R(add + '.then', 'QX_CallFunction_1.execute')]
    # EndPlay (inherited by all 4 child classes: none overrides it). Find, not WMRef: 3 children never ran this BeginPlay.
    b.override('z472EndPlay', 'ReceiveEndPlay', 0, 700)
    f2 = b.actor_of(P_WM, WM, 300, 700); ifv = b.branch(b.valid((f2, 'ReturnValue'), 300, 900), 600, 700, tag='IfWM')
    reg2 = b.getm('ZombieReg', WM, arr(obv(ZOMBIE)), (f2, 'ReturnValue'), 600, 900)
    rem = arrfn(b, 'Array_RemoveItem', reg2, 'Item', b.self_node(600, 1050), 900, 700, bo('ReturnValue', out=True, default='false'))
    b.chain(('z472EndPlay', 'then'), f2, ifv); G.link(ifv, 'then', rem, 'execute')
    # Think: caches
    wm = b.get('WMRef', obv(WM), 0, 1300)
    sc = b.getm('SoldierCache', WM, arr(obv(SOLDIER)), wm, 300, 1300); fc = b.getm('FarmerCache', WM, arr(obv(FARMER)), wm, 300, 1450)
    gc = b.getm('GateCache', WM, obv(GATE), wm, 300, 1600)
    rw += [R('CX_501.then', 'CX_503.Exec', 'skip the soldier scan'), R(sc[0] + '.SoldierCache', 'CX_503.Array'),
           R('zfBackToPlayer5.then', 'zfForEach6.Exec'), R('zfIfTargetDead3.else', 'zfForEach6.Exec'), R('zfAsFarmerTarget.CastFailed', 'zfForEach6.Exec'),
           R(fc[0] + '.FarmerCache', 'zfForEach6.Array'),
           R('CX_6.else', 'CX_400.execute'), R('K2Node_IfThenElse_ZB25.else', 'G_AtGate.execute'), R('CX_78.then', 'fzAsZombieHUD3_c1.execute')]
    retarget('CX_398', wm); retarget('CX_81', wm); retarget('CX_57', gc); retarget('G_GetGate', gc)
    # the caches can hold an actor destroyed < 1 s ago: guard both loops
    vs = b.valid(None, 0, 1900); v1 = b.branch(vs, 300, 1800, tag='IfSoldier')
    vf = b.valid(None, 0, 2150); v2 = b.branch(vf, 300, 2050, tag='IfFarmer')
    rw += [R('CX_503.LoopBody', v1 + '.execute'), R(v1 + '.then', 'CX_521.execute'), {'from': 'CX_503.Array Element', 'to': vs[0] + '.Object'},
           R('zfForEach6.LoopBody', v2 + '.execute'), R(v2 + '.then', 'zfIfRaidFarmer16.execute'), {'from': 'zfForEach6.Array Element', 'to': vf[0] + '.Object'}]
    # SimpleMoveToActor only when it is needed: skip = same target AND still moving AND asked < 2 s ago
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
    # Dead guards after the Delays that went on on a corpse (the 7 others already check Dead / do no harm: README)
    def guard(srcs, nxt, y):
        g = b.branch(b.get('Dead', BOOL, 0, y + 150), 300, y, tag='IfDead')
        for sr in srcs: rw.append(R(sr, g + '.execute'))
        rw.append(R(g + '.else', nxt + '.execute'))
    guard(['CX_53.then'], 'CX_54', 3200); guard(['CX_434.then'], 'CX_437', 3500); guard(['CX_448.then'], 'CX_458', 3800)
    guard(['CX_93.then', 'CX_78.else'], 'CX_94', 4100)
    # SetPlayRate / SetPosition no-ops: bypass the ones with something after them; the terminal ones just go (strip)
    bypass('CX_168', 'K2Node_CallFunction_ZB86'); bypass('CX_223', 'K2Node_CallFunction_ZB41'); bypass('CX_258', 'S_Wait')
    bypass('CX_430', 'CX_434'); bypass('CX_455', 'CX_457')
    out(G, 'zombie_paste.txt')
    json.dump({'blueprint': 'BP_Zombie', 'note': '#472 Think on caches, registry, move guard, Delay guards, no-op cleanup', 'pastes': ['zombie_paste.txt'], 'rewires': rw},
              open(os.path.join(HERE, 'zombie_manifest.json'), 'w'), indent=1)

# ---------------------------------------------------------------- pipeline
PY = sys.executable
def to_graph(src):
    t = open(src, encoding='utf-8', errors='replace', newline='').read()
    if re.search(r'^[ \t]+Begin Object Name="', t, re.M):    # whole-BP T3D
        dst = os.path.join(HERE, '_live_' + os.path.basename(src).split('.')[0] + '.txt')
        subprocess.check_call(['node', os.path.join(REPO, 'handoffs', 'faults-1205', 't3d_to_graph.js'), src, 'EventGraph', dst]); return dst
    return src
def build(src, manifest, stripped, out_name, post=None):
    tmp = os.path.join(HERE, '_merge_' + out_name)
    a = os.path.join(REPO, 'tools', 'applyall', 'applyall.py')
    subprocess.check_call([PY, a, 'merge', '--live', src, '--manifest', os.path.join(HERE, manifest), '--out', tmp])
    t = open(tmp, encoding='utf-8', newline='').read()
    t, gone = strip(t, stripped); print(out_name, 'removed', len(gone), 'nodes')
    if post: t = post(t)
    open(tmp, 'w', encoding='utf-8', newline='').write(t)
    final = os.path.join(HERE, out_name)
    subprocess.check_call([PY, os.path.join(REPO, 'tools', 'applyall', 'fix_impure.py'), tmp, final])
    subprocess.check_call([PY, a, 'check', final]); os.remove(tmp)
def stagger(t):
    m = re.search(r'^Begin Object [^\n]*Name="K2Node_CallFunction_ZB6".*?^End Object', t, re.S | re.M)
    b2 = re.sub(r'(PinName="InitialStartDelayVariance",.*?DefaultValue=")[^"]*"', r'\g<1>0.250000"', m.group(0), count=1)
    if b2 == m.group(0): print('stagger: already 0.25')
    return t[:m.start()] + b2 + t[m.end():]
if __name__ == '__main__':
    wm, z = to_graph(sys.argv[1]), to_graph(sys.argv[2])
    gen_wm(); gen_zombie(open(z, encoding='utf-8', errors='replace', newline='').read().replace('\r\n', '\n'))
    build(wm, 'wm_manifest.json', WM_STRIP, 'wm_merged.txt')
    build(z, 'zombie_manifest.json', Z_STRIP, 'zombie_merged.txt', stagger)
    print('OK: paste wm_merged.txt into BP_ZombieWaveManager and zombie_merged.txt into BP_Zombie')
