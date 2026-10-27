"""gen_aura_lock.py (owner 2026-10-27): the hero can't stack auras. When key 4/5/6 activates an aura, the other two
get a cooldown that lasts until this one ends: AuraT_Y.G (CdUntil) = FMax(AuraT_Y.G, new OnUntil of X); R/B/A kept.
Full EventGraph replace of BP_HeroAuras = live graph (stale dropped) + 2 x (GetVec, BreakColor, FMax, MakeColor, SetVec)
after each activation set. Writes paste_heroauras_lock.t3d."""
import os, re, sys
W = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
sys.path.insert(0, W)
import kit2 as K
import t3dlib as T
from kit2 import G, BPC, link, chain
EXP = 'live_BP_HeroAuras'
raw = open(os.path.join(W, 't3d', EXP + '.t3d'), 'rb').read()
t = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8', 'ignore')
live = set(re.findall(r"Nodes\(\d+\)=\"[^']*'([^']+)'\"", t))
g = G(BPC('/Game/CastleDefender/Gameplay/Skills/Auras/BP_HeroAuras'))
N = g.load_graph(EXP, 'EventGraph')
stale = {n for n in N if n not in live}
g.nodes = [n for n in g.nodes if n.name not in stale]
for n in g.nodes:
    for p in n.pins:
        p.links = [l for l in p.links if l[0] not in stale]
N = {n.name: n for n in g.nodes}


def member(n):
    return K.member_name(n)


def tmpl(name, pin_has=None):
    for n in g.nodes:
        if member(n) == name and (pin_has is None or pin_has(n)):
            return n.name
    raise KeyError(name)


T_GET = tmpl('GetVectorParameterValue', lambda n: 'MPC_HeroAbilities' in n.p('Collection').line)
T_BRK = tmpl('BreakColor')
T_FMX = tmpl('FMax')
ACT = [('CX_241', 'AuraT_Def', 'CX_238', 'CX_235'), ('CX_260', 'AuraT_Heal', 'CX_257', 'CX_254'), ('CX_279', 'AuraT_Burn', 'CX_276', 'CX_273')]
for setx, px, onx, durx in ACT:
    sx = N[setx]
    nxt = sx.p('then').links[0][0]
    sx.unlink('then')
    prev, x, y = sx, sx.x, sx.y + 700
    for _, py, _, _ in [a for a in ACT if a[1] != px]:
        ge = g.clone(EXP, T_GET, x, y + 250).default('ParameterName', py)
        br = g.clone(EXP, T_BRK, x + 300, y + 250)
        link(ge, 'ReturnValue', br, 'InColor')
        fx = g.clone(EXP, T_FMX, x + 550, y + 300)
        link(br, 'G', fx, 'A'); link(N[onx], 'ReturnValue', fx, 'B')
        mk = g.clone(EXP, 'CX_240', x + 750, y + 250)
        link(br, 'R', mk, 'R'); link(fx, 'ReturnValue', mk, 'G'); link(br, 'B', mk, 'B')
        fa = g.clone(EXP, T_FMX, x + 550, y + 450)          # Cd shown by the bar >= this lock
        link(br, 'A', fa, 'A'); link(N[durx], 'ReturnValue', fa, 'B'); link(fa, 'ReturnValue', mk, 'A')
        st = g.clone(EXP, setx, x + 1000, y).default('ParameterName', py)
        link(mk, 'ReturnValue', st, 'ParameterValue')
        chain(prev, ge, st) if any(p.name == 'execute' for p in ge.pins) else chain(prev, st)
        prev, x = st, x + 1300
    link(prev, 'then', N[nxt], 'execute')
    print(px, '->', nxt, 'via', prev.name)
n, size = g.emit(os.path.join(W, 'auras', 'paste_heroauras_lock.t3d'))
print('nodes', n, 'chars', size, 'stale', len(stale), 'templates', T_GET, T_BRK, T_FMX)
