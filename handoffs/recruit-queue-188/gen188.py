# #188 Recruit queue + loading bar above the barracks NPC (laptop2, 2026-10-30). Generates the Blueprint paste for
# BP_BarracksHUD's EventGraph. Run with any Python 3:  python gen188.py  ->  BarracksHUD_RecruitQueue_graph.txt
#
# What it adds (all in BP_BarracksHUD, no new Blueprint):
#   Enqueue(Kind)        custom event: if the queue holds < 3, append Kind (0 sword, 1 crossbow, 2 commander)
#   SpawnRecruit(Kind)   custom event: runs the ORIGINAL spawn nodes (CX_229 sword, CX_240 crossbow, CX_3310 commander),
#                        so everything downstream of them (gold, army list, sounds) is unchanged
#   QTick                a block inserted at the top of DrawHUD (CX_1 -> QTick -> CX_2): starts the timer for the head
#                        of the queue (soldier RecruitSeconds, commander 3x), spawns it when the time is up, pops it,
#                        and draws the bar above BP_NPC_Barracks: faded white track, a coloured fill per kind
#                        (sword gold, crossbow steel-blue, commander crimson), plus 1-2 small ticks for the queued ones.
# Rewires (manifest.json): CX_228.then -> Enq0 (was CX_229), CX_228.else -> Enq1 (was CX_240), CX_3296.then -> Enq2
# (was CX_3310), CX_1.then -> QTick (was CX_2), QTick end -> CX_2; SpawnRecruit's branches -> CX_229/CX_240/CX_3310.
# Variables to add by hand (BPVar lines in VARIABLES.md): RQ (int array), RQStart (float 0), RQDur (float 0),
# RecruitSeconds (float 6.0).
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))      # (bpkit's star-import overwrote it)

HUD = CLS('HUD')
P_NPC = '/Game/CastleDefender/Characters/NPC/Barracks/BP_NPC_Barracks'
NPC = BPC(P_NPC, 'BP_NPC_Barracks')
G = Graph(); b = B(G, 'rq')
Y = 0

def lc(r, g, bl, a, x, y):
    """MakeColor literal (LinearColor) for DrawRect."""
    return b.math('MakeColor', [(D('R', default=str(r)), None), (D('G', default=str(g)), None), (D('B', default=str(bl)), None), (D('A', default=str(a)), None)], st('ReturnValue', LC, out=True), x, y)
def rect(color, sx, sy, sw, sh, x, y, tag):
    n = b.call_self('DrawRect', [st('RectColor', LC), fl('ScreenX', default='0.0'), fl('ScreenY', default='0.0'), fl('ScreenW', default='0.0'), fl('ScreenH', default='0.0')], x, y, HUD, tag=tag)
    b.wire(color, n, 'RectColor'); b.wire(sx, n, 'ScreenX'); b.wire(sy, n, 'ScreenY'); b.wire(sw, n, 'ScreenW'); b.wire(sh, n, 'ScreenH'); return n
def pins(name): return next(n[3] for n in G.nodes if n[0] == name)
def setdef(name, **kv):
    for p in pins(name):
        if p['name'] in kv: p['default'] = kv[p['name']]
def aremove(arrvar, pin, idx, x, y):
    a = b.get(arrvar, arr(pin), x, y + 150); n = b.name('Rem' + arrvar)
    G.node(n, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Remove")' % KARR],
           [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}, it('IndexToRemove', default='0')], x, y)
    b.wire(a, n, 'TargetArray'); b.wire(idx, n, 'IndexToRemove'); return n

# ---- Enqueue(Kind): len(RQ) < 3 -> add ----
b.event('Enqueue', [it('Kind')], 0, Y)
room = b.icmp('Less_IntInt', b.alen('RQ', INT, 250, Y + 150), None, 600, Y + 150, db='3')
br = b.branch(room, 800, Y, 'IfRoom')
add = b.aadd('RQ', INT, ('Enqueue', 'Kind'), 1050, Y)
b.chain('Enqueue', br); G.link(br, 'then', add, 'execute')
# the three callers the rewires point at (CX_228.then / .else, CX_3296.then)
ENQ = [b.call_self('Enqueue', [it('Kind', default=str(k))], 0, Y + 400 + 120 * k, HUD, tag='Enq%d' % k) for k in range(3)]

# ---- SpawnRecruit(Kind): branch to the original spawn nodes (links added by the manifest) ----
Y2 = 900
b.event('SpawnRecruit', [it('Kind')], 0, Y2)
is0 = b.icmp('EqualEqual_IntInt', ('SpawnRecruit', 'Kind'), None, 250, Y2 + 150, db='0'); br0 = b.branch(is0, 500, Y2, 'IsSword')
is1 = b.icmp('EqualEqual_IntInt', ('SpawnRecruit', 'Kind'), None, 650, Y2 + 150, db='1'); br1 = b.branch(is1, 900, Y2, 'IsXbow')
b.chain('SpawnRecruit', br0); G.link(br0, 'else', br1, 'execute')
SP_SWORD, SP_XBOW, SP_CMD = br0, br1, br1      # br0.then -> CX_229, br1.then -> CX_240, br1.else -> CX_3310 (manifest)

# ---- QTick: inserted at the top of DrawHUD ----
Y3 = 1500
seq = b.seq('QTickIn', 3, 0, Y3)            # then_0 timer logic, then_1 draw, then_2 -> CX_2 (manifest)
n_ = b.alen('RQ', INT, 250, Y3 + 400)
has = b.icmp('Greater_IntInt', n_, None, 600, Y3 + 400, db='0')
bh = b.branch(has, 800, Y3, 'IfQueued'); G.link(seq, 'then_0', bh, 'execute')
start = b.get('RQStart', DBL, 1000, Y3 + 300)
idle = b.dcmp('EqualEqual_DoubleDouble', start, None, 1250, Y3 + 300, db='0.0')
bi = b.branch(idle, 1450, Y3, 'IfIdle'); G.link(bh, 'then', bi, 'execute')
# idle -> start now, duration by kind (commander = 3x)
now = b.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], 1500, Y3 + 500, pure=True, tag='Now')
s1 = b.set('RQStart', DBL, (now, 'ReturnValue'), 1700, Y3)
head = b.aget('RQ', INT, None, 1700, Y3 + 650)
iscmd = b.icmp('EqualEqual_IntInt', head, None, 2000, Y3 + 650, db='2')
secs = b.get('RecruitSeconds', DBL, 2000, Y3 + 800)
tripl = b.d2('Multiply_DoubleDouble', secs, None, 2200, Y3 + 800, db='3.0')
dur = b.self_(tripl, secs, iscmd, 2450, Y3 + 700)
s2 = b.set('RQDur', DBL, dur, 2000, Y3)
G.link(bi, 'then', s1, 'execute'); G.link(s1, 'then', s2, 'execute')
# running -> done?
el = b.d2('Subtract_DoubleDouble', (now, 'ReturnValue'), start, 1700, Y3 + 200)
done = b.dcmp('GreaterEqual_DoubleDouble', el, b.get('RQDur', DBL, 1700, Y3 + 120), 2000, Y3 + 200)
bd = b.branch(done, 2300, Y3 + 150, 'IfDone'); G.link(bi, 'else', bd, 'execute')
call = b.call_self('SpawnRecruit', [it('Kind', default='0')], 2600, Y3 + 150, HUD, tag='DoSpawn'); b.wire(head, call, 'Kind')
rem = aremove('RQ', INT, None, 2900, Y3 + 150)
s3 = b.set('RQStart', DBL, None, 3200, Y3 + 150)
G.link(bd, 'then', call, 'execute'); G.link(call, 'then', rem, 'execute'); G.link(rem, 'then', s3, 'execute')
# draw: bar above the NPC (world + 230 cm -> Project), only while something is queued
bh2 = b.branch(has, 800, Y3 + 1000, 'IfDraw'); G.link(seq, 'then_1', bh2, 'execute')
npc = b.actor_of(P_NPC, NPC, 1000, Y3 + 1200)
loc = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1300, Y3 + 1200, target=(npc, 'ReturnValue'), pure=True, const=True, tag='NpcLoc')
up = b.v2('Add_VectorVector', (loc, 'ReturnValue'), None, 1550, Y3 + 1200, db='0, 0, 230')
scr = b.call_self('Project', [V('Location'), V('ReturnValue', out=True)], 1800, Y3 + 1200, HUD, pure=True, const=True, tag='Project'); b.wire(up, scr, 'Location')
sc = b.brk((scr, 'ReturnValue'), 2050, Y3 + 1200)
x0 = b.d2('Subtract_DoubleDouble', sc['X'], None, 2300, Y3 + 1150, db='60.0')
prog = b.clamp(b.d2('Divide_DoubleDouble', el, b.get('RQDur', DBL, 2300, Y3 + 1400), 2550, Y3 + 1350), '0.0', '1.0', 2750, Y3 + 1350)
fillw = b.d2('Multiply_DoubleDouble', prog, None, 2950, Y3 + 1350, db='120.0')
track = rect(lc(1, 1, 1, 0.3, 2300, Y3 + 950), x0, sc['Y'], None, None, 3100, Y3 + 1000, 'Track')
setdef(track, ScreenW='120.0', ScreenH='8.0')
# fill colour by kind: 0 gold, 1 steel blue, 2 crimson
c0 = lc(0.95, 0.75, 0.25, 0.9, 2300, Y3 + 1600); c1 = lc(0.45, 0.65, 0.95, 0.9, 2300, Y3 + 1700); c2 = lc(0.85, 0.15, 0.2, 0.9, 2300, Y3 + 1800)
is1b = b.icmp('EqualEqual_IntInt', head, None, 2550, Y3 + 1650, db='1')
cA = b.math('SelectColor', [(st('A', LC), c1), (st('B', LC), c0), (bo('bPickA', default='false'), is1b)], st('ReturnValue', LC, out=True), 2750, Y3 + 1650)
cB = b.math('SelectColor', [(st('A', LC), c2), (st('B', LC), cA), (bo('bPickA', default='false'), iscmd)], st('ReturnValue', LC, out=True), 2950, Y3 + 1650)
fill = rect(cB, x0, sc['Y'], fillw, None, 3400, Y3 + 1000, 'Fill')
setdef(fill, ScreenH='8.0')
# queued ticks: small squares right of the bar for item 2 and 3
x1 = b.d2('Add_DoubleDouble', x0, None, 3300, Y3 + 1500, db='128.0'); x2 = b.d2('Add_DoubleDouble', x0, None, 3300, Y3 + 1600, db='140.0')
m1 = b.icmp('Greater_IntInt', n_, None, 3300, Y3 + 1700, db='1'); m2 = b.icmp('Greater_IntInt', n_, None, 3300, Y3 + 1800, db='2')
bt1 = b.branch(m1, 3700, Y3 + 1000, 'IfTwo'); bt2 = b.branch(m2, 4300, Y3 + 1000, 'IfThree')
t1 = rect(lc(1, 1, 1, 0.5, 3700, Y3 + 1300), x1, sc['Y'], None, None, 4000, Y3 + 1000, 'Tick1'); t2 = rect(lc(1, 1, 1, 0.5, 4300, Y3 + 1300), x2, sc['Y'], None, None, 4600, Y3 + 1000, 'Tick2')
setdef(t1, ScreenW='8.0', ScreenH='8.0'); setdef(t2, ScreenW='8.0', ScreenH='8.0')
G.link(bh2, 'then', track, 'execute'); G.link(track, 'then', fill, 'execute'); G.link(fill, 'then', bt1, 'execute'); G.link(bt1, 'then', t1, 'execute'); G.link(t1, 'then', bt2, 'execute'); G.link(bt2, 'then', t2, 'execute')
QTICK_OUT = (seq, 'then_2')

open(os.path.join(HERE, 'BarracksHUD_RecruitQueue_graph.txt'), 'w', encoding='utf-8').write(G.render())
print('wrote BarracksHUD_RecruitQueue_graph.txt', len(G.nodes), 'nodes', len(G.links), 'links')
print('ENQ', ENQ, 'SPAWN', SP_SWORD, SP_XBOW, SP_CMD)
import json
json.dump({'blueprint': 'BP_BarracksHUD', 'pastes': ['BarracksHUD_RecruitQueue_graph.txt'], 'rewires': [
  {'from': 'CX_228.then', 'to': ENQ[0] + '.execute', 'replace': True, 'note': 'was -> CX_229 sword spawn'},
  {'from': 'CX_228.else', 'to': ENQ[1] + '.execute', 'replace': True, 'note': 'was -> CX_240 crossbow spawn'},
  {'from': 'CX_3296.then', 'to': ENQ[2] + '.execute', 'replace': True, 'note': 'was -> CX_3310 commander spawn'},
  {'from': 'CX_1.then', 'to': 'QTickIn.execute', 'replace': True, 'note': 'DrawHUD -> queue tick first'},
  {'from': 'QTickIn.then_2', 'to': 'CX_2.execute', 'note': 'then the original DrawHUD chain'},
  {'from': SP_SWORD + '.then', 'to': 'CX_229.execute'}, {'from': SP_XBOW + '.then', 'to': 'CX_240.execute'}, {'from': SP_CMD + '.else', 'to': 'CX_3310.execute'}]},
  open(os.path.join(HERE, 'manifest.json'), 'w'), indent=1)
print('wrote manifest.json')
