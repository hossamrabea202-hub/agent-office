# #390 WinterKeep snow trails: BPC_SnowTrails EventGraph (adjustedfilm, 2026-11-01). RESEARCH.md section 4.
#   "<blender python>" -I gen_snowtrails.py  ->  BPC_SnowTrails_graph.txt + VARIABLES_BPVar.txt (then fix_impure.py)
# BPC_SnowTrails (ActorComponent on BP_WK_Snow, one per WinterKeep level; made by winterkeep_ue.py --step trails):
#   BeginPlay   clear RT_WK_TrailA/B to white (= untouched snow), timers Refresh (1 s) and TrailTick (0.05 s).
#   Refresh     Chars = up to 8 Characters within 30 m of the player (GetAllActorsOfClass once a second, not per tick).
#   TrailTick   window origin = player XY snapped to 25 cm (8 texels: the shift copy stays texel-exact, no blur);
#               TrailParams = (shift U, shift V, 0.05 s, 0); Stamp0..15 = unused; every char: foot_l / foot_r bone lower
#               than PlantZ (14 cm) above the mesh origin = planted -> Stamp<n> = (U, V, forward X, forward Y), 7 cm ahead
#               of the ankle; DrawMaterialToRenderTarget(B, M_WK_TrailUpdate), (A, M_WK_TrailCopy); Origin + TrailOrigin.
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE

ROOT = '/Game/CastleDefender/WinterKeep'
MPC = ROOT + '/MPC_WK_Snow.MPC_WK_Snow'
RT_A, RT_B = ROOT + '/Trails/RT_WK_TrailA.RT_WK_TrailA', ROOT + '/Trails/RT_WK_TrailB.RT_WK_TrailB'
M_UPD, M_CPY = ROOT + '/Trails/M_WK_TrailUpdate.M_WK_TrailUpdate', ROOT + '/Trails/M_WK_TrailCopy.M_WK_TrailCopy'
COMP, KRL, MATL = CLS('ActorComponent'), CLS('KismetRenderingLibrary'), CLS('KismetMaterialLibrary')
MPC_CLS, RTC = CLS('MaterialParameterCollection'), CLS('TextureRenderTarget2D')
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}
F = lambda n, default='0.0', out=False: fl(n, default=default, out=out)
CHARS = arr(ob('v', CHARC))
SIZE, SNAP, DT, MAXC = 6400.0, 25.0, 0.05, 8
def col(r, g, b_, a): return '(R=%f,G=%f,B=%f,A=%f)' % (r, g, b_, a)

G = Graph(); b = bpkit.B(G, 't')

def mpc_vec(param, colsrc, x, y, name_src=None, dcol=col(0, 0, 0, 0)):
    n = b.name('Set' + param)
    callfn(G, n, MATL, 'SetVectorParameterValue', [WC(), dict(ob('Collection', MPC_CLS), dobj=MPC), NAME_('ParameterName', param),
           st('ParameterValue', LC, default=dcol)], x=x, y=y, self_hidden=True)
    b.wire(colsrc, n, 'ParameterValue'); b.wire(name_src, n, 'ParameterName'); return n
def color(r, g_, b_, a, x, y, dr='0.0', dg='0.0', db='0.0', da='0.0'):
    return b.math('MakeColor', [(F('R', dr), r), (F('G', dg), g_), (F('B', db), b_), (F('A', da), a)], st('ReturnValue', LC, out=True), x, y)
def d2(m, a, c, x, y, db='0.0'): return b.d2(m, a, c, x, y, db=db)
def pawn(x, y): return (b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], x, y, pure=True, tag='Hero'), 'ReturnValue')
def loc(actor, x, y): return (b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'), 'ReturnValue')
def snapped(x, y):
    """player XY snapped to 25 cm -> {'X','Y'} handles"""
    p = b.brk(loc(pawn(x, y), x + 200, y), x + 400, y)
    return {c: b.math('GridSnap_Float', [(D('Location'), p[c]), (D('GridSize', default=repr(SNAP)), None)], D('ReturnValue', out=True), x + 600, y + (0 if c == 'X' else 120)) for c in 'XY'}
def stamp_name(idx, x, y):
    s = b.math('Conv_IntToString', [(it('InInt'), idx)], S('ReturnValue', out=True), x, y)
    cc = b.concat(None, s, x + 200, y, da='Stamp')
    n = b.name('ToName'); callfn(G, n, CLS('KismetStringLibrary'), 'Conv_StringToName', [S('InString'), dict(NAME_('ReturnValue'), out=True)], pure=True, x=x + 400, y=y, self_hidden=True)
    b.wire(cc, n, 'InString'); return (n, 'ReturnValue')
def draw(rt, mat, x, y, tag):
    return b.lib(KRL, 'DrawMaterialToRenderTarget', [WC(), dict(ob('TextureRenderTarget', RTC), dobj=rt), dict(ob('Material', MATI), dobj=mat)], x, y, tag=tag)
def clear(rt, x, y, tag):
    return b.lib(KRL, 'ClearRenderTarget2D', [WC(), dict(ob('TextureRenderTarget', RTC), dobj=rt), st('ClearColor', LC, default=col(1, 1, 1, 1))], x, y, tag=tag)

# ============================================================ BeginPlay
G.node('tBegin', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
ca, cb = clear(RT_A, 250, 0, 'ClearA'), clear(RT_B, 550, 0, 'ClearB')
t1 = b.timer('Refresh', 850, 0, dtime='1.0', loop=True)
t2 = b.timer('TrailTick', 1200, 0, dtime=repr(DT), loop=True)
b.chain('tBegin', ca, cb, t1, t2)

# ============================================================ Refresh: up to 8 characters within 30 m
Y = 600
b.event('Refresh', [], 0, Y)
ga = b.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, '/Script/Engine.Character'), arr(ob('OutActors', CHARC, out=True))], 250, Y, tag='AllChars')
cl = b.name('ClearChars')
G.node(cl, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Clear")' % KARR],
       [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}], 550, Y)
b.wire(b.get('Chars', CHARS, 400, Y + 200), cl, 'TargetArray')
fe = b.foreach(CHARC, 800, Y); G.link(ga, 'OutActors', fe, 'Array')
# the snowfall shells of BP_WK_Snow ride on the camera (re-attaching each second is a no-op once attached)
own = b.name('Owner'); callfn(G, own, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=-200, y=Y - 250, self_hidden=True)
cam = b.lib(GS, 'GetPlayerCameraManager', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CLS('PlayerCameraManager'), out=True)], -200, Y - 400, pure=True, tag='Cam')
RULE = lambda n, d: {'name': n, 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EAttachmentRule\'"', 'default': d}
att = b.call(ACT, 'K2_AttachToActor', [ob('ParentActor', ACT), NAME_('SocketName', 'None'), RULE('LocationRule', 'SnapToTarget'), RULE('RotationRule', 'KeepWorld'),
             RULE('ScaleRule', 'KeepWorld'), bo('bWeldSimulatedBodies', default='false'), bo('ReturnValue', out=True, default='false')], 100, Y - 300, target=(own, 'ReturnValue'), tag='RideCam')
b.wire((cam, 'ReturnValue'), att, 'ParentActor')
b.chain('Refresh', att, ga, cl, (fe, 'Exec'))
dist = b.call(ACT, 'GetDistanceTo', [ob('OtherActor', ACT), F('ReturnValue', out=True)], 1000, Y + 250, target=(fe, 'Array Element'), pure=True, const=True, tag='Dist')
b.wire(pawn(800, Y + 400), dist, 'OtherActor')
near = b.dcmp('Less_DoubleDouble', (dist, 'ReturnValue'), None, 1250, Y + 250, db='3000.0')
room = b.icmp('Less_IntInt', b.alen('Chars', ob('v', CHARC), 1000, Y + 450), None, 1450, Y + 450, db=str(MAXC))
ok = b.branch(b.b2('BooleanAND', near, room, 1650, Y + 300), 1100, Y, tag='IfNear')
G.link(fe, 'LoopBody', ok, 'execute')
ad = b.aadd('Chars', ob('v', CHARC), (fe, 'Array Element'), 1400, Y)
G.link(ok, 'then', ad, 'execute')

# ============================================================ TrailTick
Y = 1400
b.event('TrailTick', [], 0, Y)
pv = b.branch(b.valid(pawn(0, Y + 200), 200, Y + 200), 250, Y, tag='IfHero')
G.link('TrailTick', 'then', pv, 'execute')
o = b.brk(b.get('Origin', VECT, 300, Y + 500), 500, Y + 500)
sn = snapped(300, Y + 750)
shift = {c: d2('Divide_DoubleDouble', d2('Subtract_DoubleDouble', sn[c], o[c], 1100, Y + 500 + i * 130), None, 1300, Y + 500 + i * 130, db=repr(SIZE))
         for i, c in enumerate('XY')}
sp = mpc_vec('TrailParams', color(shift['X'], shift['Y'], None, None, 1500, Y + 500, db=repr(DT)), 500, Y)
G.link(pv, 'then', sp, 'execute')
# every stamp unused (x = -10) ...
fl16 = b.name('ForLoop')
G.node(fl16, 'K2Node_MacroInstance', ['MacroGraphReference=(%s)' % FORLOOP],
       [ex(), it('FirstIndex', default='0'), it('LastIndex', default='15'), ex('LoopBody', True), it('Index', out=True), ex('Completed', True)], 800, Y)
G.link(sp, 'then', fl16, 'execute')
clr = mpc_vec('Stamp', None, 1100, Y - 300, name_src=stamp_name((fl16, 'Index'), 800, Y - 450), dcol=col(-10, -10, 0, 0))
G.link(fl16, 'LoopBody', clr, 'execute')
s0 = b.set('Slot', INT, None, 1100, Y); G.link(fl16, 'Completed', s0, 'execute')
# ... then the planted feet of every near character
fc = b.foreach(CHARC, 1350, Y); b.wire(b.get('Chars', CHARS, 1200, Y + 200), fc, 'Array'); G.link(s0, 'then', fc, 'Exec')
sq = b.seq(b.name('Feet'), 2, 1650, Y); G.link(fc, 'LoopBody', sq, 'execute')
X0 = 1900
for k, foot in enumerate(('FootL', 'FootR')):
    y = Y + 2200 + k * 1300
    ch = (fc, 'Array Element')
    mesh = b.getm('Mesh', CHARC, ob('v', SKEL), ch, X0, y + 300)
    fp = b.call(SCENE, 'GetSocketLocation', [NAME_('InSocketName'), V('ReturnValue', out=True)], X0 + 250, y + 300, target=mesh, pure=True, const=True, tag='Foot')
    b.wire(b.get(foot, NAME_('v'), X0, y + 450), fp, 'InSocketName')
    mp = b.call(SCENE, 'K2_GetComponentLocation', [V('ReturnValue', out=True)], X0 + 250, y + 550, target=mesh, pure=True, const=True, tag='MeshLoc')
    fz, mz = b.brk((fp, 'ReturnValue'), X0 + 500, y + 300), b.brk((mp, 'ReturnValue'), X0 + 500, y + 550)
    low = b.dcmp('Less_DoubleDouble', d2('Subtract_DoubleDouble', fz['Z'], mz['Z'], X0 + 700, y + 400), b.get('PlantZ', DBL, X0 + 700, y + 550), X0 + 900, y + 450)
    free = b.icmp('Less_IntInt', b.get('Slot', INT, X0 + 700, y + 650), None, X0 + 900, y + 650, db='16')
    br = b.branch(b.b2('BooleanAND', low, free, X0 + 1100, y + 500), X0, y, tag='IfPlanted')
    G.link(sq, 'then_%d' % k, br, 'execute')
    fwd = (b.call(ACT, 'GetActorForwardVector', [V('ReturnValue', out=True)], X0 + 250, y + 800, target=ch, pure=True, const=True, tag='Fwd'), 'ReturnValue')
    ahead = b.v2('Add_VectorVector', (fp, 'ReturnValue'), b.math('Multiply_VectorFloat', [(V('A'), fwd), (D('B', default='7.0'), None)], V('ReturnValue', out=True), X0 + 500, y + 800), X0 + 700, y + 800)
    pa, fw = b.brk(ahead, X0 + 900, y + 800), b.brk(fwd, X0 + 900, y + 1000)
    uv = {c: d2('Add_DoubleDouble', d2('Divide_DoubleDouble', d2('Subtract_DoubleDouble', pa[c], sn[c], X0 + 1100, y + 800 + i * 120), None, X0 + 1300, y + 800 + i * 120, db=repr(SIZE)),
                None, X0 + 1500, y + 800 + i * 120, db='0.5') for i, c in enumerate('XY')}
    st_ = mpc_vec('Stamp', color(uv['X'], uv['Y'], fw['X'], fw['Y'], X0 + 1700, y + 800), X0 + 300, y,
                  name_src=stamp_name(b.get('Slot', INT, X0, y - 200), X0 + 150, y - 200))
    G.link(br, 'then', st_, 'execute')
    inc = b.set('Slot', INT, b.i2('Add_IntInt', b.get('Slot', INT, X0 + 500, y - 300), None, X0 + 700, y - 300, db='1'), X0 + 700, y)
    G.link(st_, 'then', inc, 'execute')
# after the loop: update + copy, then move the window
du, dc = draw(RT_B, M_UPD, 1650, Y - 700, 'DrawUpdate'), draw(RT_A, M_CPY, 1950, Y - 700, 'DrawCopy')
so = b.set('Origin', VECT, b.vec(sn['X'], sn['Y'], None, 2100, Y - 450), 2250, Y - 700)
to = mpc_vec('TrailOrigin', color(sn['X'], sn['Y'], None, None, 2400, Y - 450), 2550, Y - 700)
G.link(fc, 'Completed', du, 'execute'); b.chain(du, dc, so, to)

out = os.path.join(HERE, 'BPC_SnowTrails_graph.txt')
open(out, 'w', newline='\r\n').write(G.render())
print('BPC_SnowTrails_graph.txt: nodes %d, links %d' % (len(G.nodes), len(G.links)))
VARS = [('Chars', 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Character\'",ContainerType=Array', ''),
        ('Origin', 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"', '0,0,0'),
        ('Slot', 'PinCategory="int"', '0'), ('FootL', 'PinCategory="name"', 'foot_l'), ('FootR', 'PinCategory="name"', 'foot_r'),
        ('PlantZ', 'PinCategory="real",PinSubCategory="double"', '14.0')]
bpv = lambda n, t, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'snowtrails390/' + n).hex.upper(), t, n, d)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# #390 BPC_SnowTrails - paste one line at a time on the VARIABLES header, then Compile\n' + '\n'.join(bpv(*v) for v in VARS) + '\n')
print('BPVar lines: %d' % len(VARS))
