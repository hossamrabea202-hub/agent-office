# #283 Cannon scroll map (adjustedfilm, 2026-10-31; owner idea): ordering a cannon at the artillery yard (#230) opens a
# motion-graphics parchment map; the player clicks where the cannon goes. Ordered cannons can be moved; starter cannons
# (the ones in the level at Play) are locked.
#   "<blender python>" -I gen_cannonmap283.py -> BPC_CannonMap_graph.txt, VARIABLES_BPVar.txt, VARIABLES.md,
#        CannonOrder_Map_graph.txt + manifest_cannonorder.json (BP_CannonOrder: O opens the map),
#        MotionFX_Map_graph.txt + manifest_motionfx_map.json (BPC_MotionFX draws the map every HUD frame)
# BPC_CannonMap (hero component "CannonMap"):
#   BeginPlay  remembers every BP_Cannon already in the level (StarterCannons, locked) and spawns BP_MapCapture 150 m over
#              the castle centre (orthographic, 400 m wide).
#   OpenMap    pause, mouse cursor on, capture the map once, scroll sound; Mode 1 (unrolling 0.6 s) -> 2 (choosing).
#   DrawMap(Hud, SizeX, SizeY) every frame while open:
#     the scroll (M_ScrollMap: Unroll ease-out 0.6 s, the inked map fades in 0.45-0.85 s)
#     infographic: three numbered steps slide in 40 ms apart along the top edge, the current one in gold:
#       1 Click a spot on the map   2 ENTER or CONFIRM   3 The crew brings the cannon
#     a pulsing gold "click here" ring on a demo spot in the field until the first mark
#     cannon icons: gold rings = ordered (click one to move it), grey = starter (locked)
#     click on the map: NavMesh check -> red ring + an ink X (mark sound); unreachable -> "The crew cannot reach that spot"
#     CONFIRM button (bottom centre, pulses) or ENTER: new cannon -> pay Price (800) and send the #230 convoy from the
#       artillery yard; a selected cannon -> it is packed (removed) and a convoy brings it from its spot; facing away from
#       the castle centre. Esc closes without paying. Closing rolls the scroll up 0.4 s.
import math, os, sys, json, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

COMP, HUDC = CLS('ActorComponent'), CLS('HUD')
UI = '/Game/CastleDefender/UI/CannonMap/'
P_CM = UI + 'BPC_CannonMap'
P_MC = UI + 'BP_MapCapture'
P_CANNON = '/Game/CastleDefender/Gameplay/Cannon/BP_Cannon'
P_ORDER, P_CONVOY = '/Game/CastleDefender/Gameplay/Castle/BP_CannonOrder', '/Game/CastleDefender/Gameplay/Castle/BP_CannonConvoy'
P_ZHUD, P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD', '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
CMC_, MCC = BPC(P_CM, 'BPC_CannonMap'), BPC(P_MC, 'BP_MapCapture')
CANNONC, ORDERC, CONVOYC = BPC(P_CANNON, 'BP_Cannon'), BPC(P_ORDER, 'BP_CannonOrder'), BPC(P_CONVOY, 'BP_CannonConvoy')
ZHUDC, NOTC = BPC(P_ZHUD, 'BP_ZombieHUD'), BPC(P_NOTICE, 'BP_NoticeHUD')
CAPC, MATL, MIDC, SOUND = CLS('SceneCaptureComponent2D'), CLS('KismetMaterialLibrary'), CLS('MaterialInstanceDynamic'), CLS('SoundBase')
FONT = '/Game/CastleDefender/UI/Fonts/Font_Cinzel.Font_Cinzel'
FONTC = '"/Script/CoreUObject.Class\'/Script/Engine.Font\'"'
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
V2D = '"/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector2D\'"'
OBJV = lambda c: ob('v', c)
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}
F = lambda n, default='0.0', out=False: fl(n, default=default, out=out)
INK, GOLD, RED = (0.22, 0.14, 0.08), (1.0, 0.72, 0.30), (0.62, 0.08, 0.05)
def col(r, g, b_, a=1.0): return '(R=%f,G=%f,B=%f,A=%f)' % (r, g, b_, a)
OW = 40000.0


class B9(bpkit.B):
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def div(s, a, c, x, y, da='0.0', db='1.0'): return s.d2('Divide_DoubleDouble', a, c, x, y, da=da, db=db)
    def sat(s, v, x, y): return s.clamp(v, '0.0', '1.0', x, y)
    def lin(s, t, t0, dur, x, y): return s.sat(s.div(s.sub(t, None, x, y, db=repr(t0)), None, x + 180, y, db=repr(dur)), x + 360, y)
    def sin(s, a, x, y): return s.math('Sin', [(D('A', default='0.0'), a)], D('ReturnValue', out=True), x, y)
    def eqi(s, a, v, x, y): return s.icmp('EqualEqual_IntInt', a, None, x, y, db=str(v))
    def colr(s, r, g, b_, a, x, y, dr='1.0', dg='1.0', db_='1.0'):
        return s.math('MakeColor', [(fl('R', default=dr), r), (fl('G', default=dg), g), (fl('B', default=db_), b_), (fl('A', default='1.0'), a)], st('ReturnValue', LC, out=True), x, y)
    def rgba(s, c, a, x, y):
        if isinstance(a, (int, float)):
            return s.math('MakeColor', [(fl('R', default=repr(c[0])), None), (fl('G', default=repr(c[1])), None), (fl('B', default=repr(c[2])), None),
                                        (fl('A', default=repr(float(a))), None)], st('ReturnValue', LC, out=True), x, y)
        return s.colr(None, None, None, a, x, y, dr=repr(c[0]), dg=repr(c[1]), db_=repr(c[2]))
    def item(s, arrsrc, pin, idx, x, y):
        n = s.name('Item'); s.G.node(n, 'K2Node_GetArrayItem', [], [arr(dict(pin, name='Array')), it('Dimension 1', default='0'), dict(pin, name='Output', out=True)], x, y)
        s.wire(arrsrc, n, 'Array'); s.wire(idx, n, 'Dimension 1'); return (n, 'Output')
    def getall(s, path, cls, x, y):
        return s.lib(GS, 'GetAllActorsOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), arr(ob('OutActors', cls, out=True))], x, y, tag='All' + path.split('/')[-1][3:])
    def actor_of_(s, path, cls, x, y):
        return s.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, cpath(path)), ob('ReturnValue', cls, out=True)], x, y, tag='Find' + path.split('/')[-1][3:])
    def loc(s, actor, x, y):
        n = s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'); return (n, 'ReturnValue')
    def pc(s, x, y):
        return (s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC'), 'ReturnValue')
    def key(s, k, x, y):
        n = s.call(PCON, 'WasInputKeyJustPressed', [st('Key', KEY, default=k), bo('ReturnValue', out=True, default='false')], x, y, target=s.pc(x - 200, y), pure=True, const=True, tag='Key' + k[:5])
        return (n, 'ReturnValue')
    def hud_cast(s, cls, label, x, y):
        hud = s.call(PCON, 'GetHUD', [ob('ReturnValue', CLS('HUD'), out=True)], x - 150, y + 300, target=s.pc(x - 350, y + 300), pure=True, const=True, tag='GetHUD')
        nc = s.name('As' + label.replace(' ', '')); cast(s.G, nc, cls, 'As' + label, x, y); s.wire((hud, 'ReturnValue'), nc, 'Object'); return nc, (nc, 'As' + label)
    def notice(s, text, x, y):
        nc, nh = s.hud_cast(NOTC, 'BP Notice HUD', x, y)
        pn = s.call(NOTC, 'PushNotice', [S('Text', default=text), it('Tier', default='1')], x + 300, y, target=nh, tag='Notice')
        s.G.link(nc, 'then', pn, 'execute'); return nc, pn
    def sound(s, name, x, y, vol='0.800000'):
        return s.lib(GS, 'PlaySound2D', [WC(), dict(ob('Sound', SOUND), dobj=UI + '%s.%s' % (name, name)), fl('VolumeMultiplier', default=vol)], x, y, tag=name[4:])
    def mid_scalar(s, mid, param, val, x, y, dv='0.0'):
        n = s.call(MIDC, 'SetScalarParameterValue', [NAME_('ParameterName', param), fl('Value', default=dv)], x, y, target=mid, tag='S' + param)
        s.wire(val, n, 'Value'); return n
    def drawmat(s, hud, mid, X, Y, W, H, x, y, tag):
        n = s.call(HUDC, 'DrawMaterial', [ob('Material', MATI), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('MaterialU'), F('MaterialV'),
                   F('MaterialUWidth', '1.0'), F('MaterialVHeight', '1.0'), F('Scale', '1.0'), bo('bScalePosition', default='false'), F('Rotation'),
                   st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], x, y, target=hud, tag=tag)
        for p, v in (('Material', mid), ('ScreenX', X), ('ScreenY', Y), ('ScreenW', W), ('ScreenH', H)): s.wire(v, n, p)
        return n
    def text(s, hud, txt, colsrc, X, Y, scale, x, y, tag='Txt', dtxt=''):
        n = s.call(HUDC, 'DrawText', [S('Text', default=dtxt), st('TextColor', LC, default=col(1, 1, 1)), F('ScreenX'), F('ScreenY'), dict(ob('Font', FONTC), dobj=FONT),
                   F('Scale', '1.0'), bo('bScalePosition', default='false')], x, y, target=hud, tag=tag)
        for p, v in (('Text', txt), ('TextColor', colsrc), ('ScreenX', X), ('ScreenY', Y), ('Scale', scale)): s.wire(v, n, p)
        return n
    def rect(s, hud, colsrc, X, Y, W, H, x, y, tag='Rect'):
        n = s.call(HUDC, 'DrawRect', [st('RectColor', LC, default=col(0, 0, 0, 0)), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH')], x, y, target=hud, tag=tag)
        for p, v in (('RectColor', colsrc), ('ScreenX', X), ('ScreenY', Y), ('ScreenW', W), ('ScreenH', H)): s.wire(v, n, p)
        return n
    def make_mid(s, path, x, y, tag):
        return s.lib(MATL, 'CreateDynamicMaterialInstance', [WC(), dict(ob('Parent', MATI), dobj=path), NAME_('OptionalName', 'None'),
                     {'name': 'CreationFlags', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EMIDCreationFlags\'"', 'default': 'None'},
                     ob('ReturnValue', MIDC, out=True)], x, y, tag=tag)
    def me(s, member, x, y, pins=()):
        return s.call_self(member, list(pins), x, y, COMP, tag='Call' + member)


def event_override(G, nm, parent, member, params, x, y):
    G.node(nm, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="%s")' % (parent, member), 'bOverrideFunction=True'],
           [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="%s")' % (parent, member)}, ex('then', True)]
           + [dict(p, out=True) for p in params], x, y)
    return nm


def write(G, name):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    if bad: raise SystemExit('%s bad links: %s' % (name, bad[:10]))
    names = [n[0] for n in G.nodes]; dup = {n for n in names if names.count(n) > 1}
    if dup: raise SystemExit('%s duplicate names: %s' % (name, sorted(dup)[:10]))
    open(os.path.join(HERE, name), 'w', newline='\r\n').write(G.render()); print('%s: nodes %d, links %d' % (name, len(G.nodes), len(G.links)))


G = Graph(); b = B9(G, 'cm')
g = b.get
centre = lambda x, y: g('CastleCentre', V('v'), x, y)
# ================================================================================================= BeginPlay
event_override(G, 'BP', COMP, 'ReceiveBeginPlay', [], 0, 0)
ga = b.getall(P_CANNON, CANNONC, 300, 0); G.link('BP', 'then', ga, 'execute')
ss = b.set('StarterCannons', arr(OBJV(ACT)), (ga, 'OutActors'), 650, 0); G.link(ga, 'then', ss, 'execute')
cpos = b.v2('Add_VectorVector', centre(700, 300), None, 900, 300, db='0.000000,0.000000,15000.000000')
sp = spawn(b, P_MC, MCC, transform(b, cpos, 1100, 300), 950, 0); G.link(ss, 'then', sp, 'execute')
ssc = b.set('MapCap', OBJV(ACT), (sp, 'ReturnValue'), 1300, 0); G.link(sp, 'then', ssc, 'execute')
fc = b.call(ACT, 'GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.SceneCaptureComponent2D'), NAME_('Tag', 'MapCapture'),
            arr(ob('ReturnValue', CAPC, out=True))], 1400, 300, target=g('MapCap', OBJV(ACT), 1250, 300), pure=True, const=True, tag='FindCap')
scp = b.set('Cap', OBJV(CAPC), b.item((fc, 'ReturnValue'), ob('v', CAPC), None, 1650, 300), 1600, 0); G.link(ssc, 'then', scp, 'execute')
last = scp; X = 1900
for var, path in (('ScrollMID', UI + 'M_ScrollMap.M_ScrollMap'), ('GoldMID', UI + 'M_MapRing.M_MapRing'), ('GreyMID', UI + 'M_MapRing.M_MapRing'),
                  ('MarkMID', UI + 'M_MapRing.M_MapRing'), ('DemoMID', UI + 'M_MapRing.M_MapRing')):
    m_ = b.make_mid(path, X, 0, 'Make' + var); s_ = b.set(var, OBJV(MIDC), (m_, 'ReturnValue'), X + 300, 0)
    G.link(last, 'then', m_, 'execute'); G.link(m_, 'then', s_, 'execute'); last = s_; X += 600
for var, c_, solid in (('GreyMID', (0.35, 0.33, 0.30, 0.9), '1.0'), ('MarkMID', RED + (1.0,), '1.0'), ('DemoMID', GOLD + (1.0,), '0.0')):
    n = b.call(MIDC, 'SetVectorParameterValue', [NAME_('ParameterName', 'Col'), st('Value', LC, default=col(*c_))], X, 0, target=g(var, OBJV(MIDC), X - 150, 250), tag='Col' + var)
    G.link(last, 'then', n, 'execute'); last = n; X += 300
    n = b.mid_scalar(g(var, OBJV(MIDC), X - 150, 250), 'Solid', None, X, 0, dv=solid); G.link(last, 'then', n, 'execute'); last = n; X += 300

# ================================================================================================= OpenMap / CloseMap
Y = 900
b.event('OpenMap', [], 0, Y)
bm = b.branch(b.eqi(g('Mode', INT, 0, Y + 300), 0, 200, Y + 300), 300, Y, tag='IfClosed'); G.link('OpenMap', 'then', bm, 'execute')
rnow = lambda x, y: (b.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], x, y, pure=True, tag='RealNow'), 'ReturnValue')
chain = [b.set('Mode', it('v', default='1'), None, 600, Y), b.set('OpenT', DBL, rnow(600, Y + 300), 850, Y), b.set('HasMark', BOOL, None, 1100, Y),
         b.set('Sel', OBJV(ACT), None, 1350, Y)]
vc = b.branch(b.valid(g('Cap', OBJV(CAPC), 1500, Y + 300), 1650, Y + 300), 1600, Y, tag='IfCap')
cap = b.call(CAPC, 'CaptureScene', [], 1900, Y - 200, target=g('Cap', OBJV(CAPC), 1750, Y - 50), tag='CaptureMap')
G.link(bm, 'then', chain[0], 'execute'); b.chain(*chain); G.link(chain[-1], 'then', vc, 'execute'); G.link(vc, 'then', cap, 'execute')
mg = b.seq('AfterCap', 1, 2200, Y); G.link(vc, 'else', mg, 'execute'); G.link(cap, 'then', mg, 'execute')
pz = b.lib(GS, 'SetGamePaused', [WC(), bo('bPaused', default='true'), bo('ReturnValue', out=True, default='false')], 2500, Y, tag='Pause')
cur = b.setm('bShowMouseCursor', PCON, bo('v', default='true'), None, b.pc(2700, Y + 300), 2800, Y)
so = b.sound('SFX_Scroll_Open', 3100, Y)
G.link(mg, 'then_0', pz, 'execute'); b.chain(pz, cur, so)
Y = 1700
b.event('CloseMap', [], 0, Y)
bc = b.branch(b.eqi(g('Mode', INT, 0, Y + 300), 2, 200, Y + 300), 300, Y, tag='IfOpen'); G.link('CloseMap', 'then', bc, 'execute')
c1 = b.set('Mode', it('v', default='3'), None, 600, Y); c2 = b.set('CloseT', DBL, rnow(600, Y + 300), 850, Y)
up = b.lib(GS, 'SetGamePaused', [WC(), bo('bPaused', default='false'), bo('ReturnValue', out=True, default='false')], 1100, Y, tag='Unpause')
c3 = b.setm('bShowMouseCursor', PCON, bo('v', default='false'), None, b.pc(1300, Y + 300), 1400, Y)
c4 = b.sound('SFX_Scroll_Close', 1700, Y)
G.link(bc, 'then', c1, 'execute'); b.chain(c1, c2, up, c3, c4)

# ================================================================================================= ConfirmMap
Y = 2500
b.event('ConfirmMap', [], 0, Y)
mark = lambda x, y: g('Mark', V('v'), x, y)
yaw_rot = b.math('FindLookAtRotation', [(V('Start'), centre(200, Y + 1500)), (V('Target'), mark(200, Y + 1600))], st('ReturnValue', ROT, out=True), 400, Y + 1550)
yaw = b.math('BreakRotator', [(st('InRot', ROT, default='0, 0, 0'), yaw_rot)], fl('Yaw', out=True, default='0.0'), 600, Y + 1550)
G.nodes[-1][3].insert(1, fl('Roll', out=True, default='0.0')); G.nodes[-1][3].insert(2, fl('Pitch', out=True, default='0.0'))
sel = lambda x, y: g('Sel', OBJV(ACT), x, y)
bs = b.branch(b.valid(sel(200, Y + 300), 350, Y + 300), 400, Y, tag='IfMove'); G.link('ConfirmMap', 'then', bs, 'execute')
# move an ordered cannon: a convoy picks it up where it stands
mloc = b.loc(sel(600, Y - 100), 800, Y - 100)
spm = spawn(b, P_CONVOY, CONVOYC, transform(b, b.v2('Add_VectorVector', mloc, None, 1000, Y - 100, db='0.000000,0.000000,100.000000'), 1200, Y - 100), 700, Y - 400)
G.link(bs, 'then', spm, 'execute')
dsel = b.call(ACT, 'K2_DestroyActor', [], 1500, Y - 400, target=sel(1350, Y - 250), tag='PackCannon'); G.link(spm, 'then', dsel, 'execute')
scm = b.call(CONVOYC, 'StartConvoy', [V('Target'), D('Yaw', default='0.0')], 1800, Y - 400, target=(spm, 'ReturnValue'), tag='StartMove')
b.wire(mark(1650, Y - 200), scm, 'Target'); b.wire(yaw, scm, 'Yaw'); G.link(dsel, 'then', scm, 'execute')
nm1, pm1 = b.notice('The crew packs the cannon and moves it to the new spot.', 2100, Y - 400); G.link(scm, 'then', nm1, 'execute')
cl1 = b.me('CloseMap', 2700, Y - 400); G.link(pm1, 'then', cl1, 'execute'); G.link(nm1, 'CastFailed', cl1, 'execute')
# a new cannon: pay, convoy from the artillery yard
zc, zh = b.hud_cast(ZHUDC, 'BP Zombie HUD', 700, Y + 300); G.link(bs, 'else', zc, 'execute')
gold = lambda x, y: b.getm('Gold', ZHUDC, INT, zh, x, y)
price = lambda x, y: g('Price', it('v', default='800'), x, y)
bg = b.branch(b.icmp('GreaterEqual_IntInt', gold(1000, Y + 600), price(1000, Y + 700), 1200, Y + 650), 1000, Y + 300, tag='IfGold'); G.link(zc, 'then', bg, 'execute')
nng, png = b.notice('Not enough gold for a cannon.', 1300, Y + 800); G.link(bg, 'else', nng, 'execute')
pay = b.setm('Gold', ZHUDC, INT, b.i2('Subtract_IntInt', gold(1300, Y + 600), price(1300, Y + 700), 1500, Y + 650), zh, 1350, Y + 300); G.link(bg, 'then', pay, 'execute')
fy = b.actor_of_(P_ORDER, ORDERC, 1650, Y + 300); G.link(pay, 'then', fy, 'execute')
yard = (fy, 'ReturnValue')
yfw = b.call(ACT, 'GetActorForwardVector', [V('ReturnValue', out=True)], 1800, Y + 750, target=yard, pure=True, const=True, tag='YardFwd')
yl = b.v2('Add_VectorVector', b.loc(yard, 1800, Y + 600), b.math('Multiply_VectorFloat', [(V('A'), (yfw, 'ReturnValue')), (D('B', default='300.0'), None)], V('ReturnValue', out=True), 2000, Y + 750), 2200, Y + 650)
start = b.selvec(yl, b.v2('Add_VectorVector', b.loc(b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 2000, Y + 900, pure=True, tag='Hero') and
                                                    (G.nodes[-1][0], 'ReturnValue'), 2200, Y + 900), None, 2400, Y + 900, db='300.000000,0.000000,0.000000'),
                 b.valid(yard, 2200, Y + 1000), 2600, Y + 800)
spn = spawn(b, P_CONVOY, CONVOYC, transform(b, start, 2800, Y + 800), 1950, Y + 300); G.link(fy, 'then', spn, 'execute')
scn = b.call(CONVOYC, 'StartConvoy', [V('Target'), D('Yaw', default='0.0')], 2300, Y + 300, target=(spn, 'ReturnValue'), tag='StartNew')
b.wire(mark(2150, Y + 500), scn, 'Target'); b.wire(yaw, scn, 'Yaw'); G.link(spn, 'then', scn, 'execute')
nn, pn = b.notice('Cannon ordered - the crew is on the way.', 2600, Y + 300); G.link(scn, 'then', nn, 'execute')
cl2 = b.me('CloseMap', 3200, Y + 300); G.link(pn, 'then', cl2, 'execute'); G.link(nn, 'CastFailed', cl2, 'execute')
G.link(zc, 'CastFailed', cl2, 'execute'); G.link(png, 'then', cl2, 'execute'); G.link(nng, 'CastFailed', cl2, 'execute')

# ================================================================================================= DrawMap
Y0 = 4600
b.event('DrawMap', [ob('Hud', HUDC), it('SizeX'), it('SizeY')], 0, Y0)
hud = ('DrawMap', 'Hud')
W, H = b.i2d(('DrawMap', 'SizeX'), 200, Y0 + 300), b.i2d(('DrawMap', 'SizeY'), 200, Y0 + 400)
sc = b.div(H, None, 400, Y0 + 400, db='1080.0')
mode = lambda x, y: g('Mode', INT, x, y)
bo_ = b.branch(b.icmp('Greater_IntInt', mode(200, Y0 + 200), None, 400, Y0 + 200, db='0'), 400, Y0, tag='IfMap'); G.link('DrawMap', 'then', bo_, 'execute')
seq = b.seq('MapSeq', 5, 700, Y0); G.link(bo_, 'then', seq, 'execute')
rn = rnow(200, Y0 + 600)
a = b.sub(rn, g('OpenT', DBL, 200, Y0 + 700), 400, Y0 + 650)
ca = b.lin(b.sub(rn, g('CloseT', DBL, 200, Y0 + 850), 400, Y0 + 800), 0.0, 0.4, 600, Y0 + 800)
uo = b.lin(a, 0.0, 0.6, 600, Y0 + 650)
uo = b.sub(None, b.mul(b.mul(b.sub(None, uo, 1000, Y0 + 650, da='1.0'), b.sub(None, uo, 1000, Y0 + 700, da='1.0'), 1200, Y0 + 650),
                    b.sub(None, uo, 1000, Y0 + 750, da='1.0'), 1400, Y0 + 650), 1600, Y0 + 650, da='1.0')        # ease-out cubic
closing = b.eqi(mode(1400, Y0 + 850), 3, 1600, Y0 + 850)
unroll = b.self_(b.sub(None, ca, 1800, Y0 + 800, da='1.0'), uo, closing, 2000, Y0 + 700)
reveal = b.mul(b.lin(a, 0.45, 0.4, 1800, Y0 + 950), unroll, 2200, Y0 + 900)
qw, qh = b.mul(W, None, 600, Y0 + 1100, db='0.82'), b.mul(H, None, 600, Y0 + 1200, db='0.86')
qx, qy = b.mul(W, None, 600, Y0 + 1300, db='0.09'), b.mul(H, None, 600, Y0 + 1400, db='0.07')
ax, aw = b.add(qx, b.mul(qw, None, 800, Y0 + 1500, db='0.08'), 1000, Y0 + 1500), b.mul(qw, None, 800, Y0 + 1600, db='0.84')
ay, ah = b.add(qy, b.mul(qh, None, 800, Y0 + 1700, db='0.12'), 1000, Y0 + 1700), b.mul(qh, None, 800, Y0 + 1800, db='0.76')
ma = b.div(aw, ah, 1200, Y0 + 1650)

# then_0: mode steps
X = 1000
b1 = b.branch(b.b2('BooleanAND', b.eqi(mode(X, Y0 - 300), 1, X + 200, Y0 - 300), b.dcmp('GreaterEqual_DoubleDouble', a, None, X + 200, Y0 - 200, db='1.05'), X + 400, Y0 - 250),
              X + 200, Y0 - 500, tag='IfOpened')
G.link(seq, 'then_0', b1, 'execute')
m2 = b.set('Mode', it('v', default='2'), None, X + 500, Y0 - 700); G.link(b1, 'then', m2, 'execute')
b2_ = b.branch(b.b2('BooleanAND', closing, b.dcmp('GreaterEqual_DoubleDouble', ca, None, X + 600, Y0 - 300, db='1.0'), X + 800, Y0 - 300), X + 700, Y0 - 500, tag='IfRolledUp')
G.link(b1, 'else', b2_, 'execute')
m0 = b.set('Mode', INT, None, X + 1000, Y0 - 700); G.link(b2_, 'then', m0, 'execute')

# then_1: the scroll
smid = lambda x, y: g('ScrollMID', OBJV(MIDC), x, y)
ch = []
XX = 2600
for prm, val in (('Unroll', unroll), ('Reveal', reveal), ('Aspect', b.div(qw, qh, XX, Y0 + 300)), ('MapAspect', ma)):
    ch.append(b.mid_scalar(smid(XX, Y0 + 200), prm, val, XX + 100, Y0)); XX += 300
ch.append(b.drawmat(hud, smid(XX, Y0 + 200), qx, qy, qw, qh, XX + 100, Y0, 'DrawScroll')); XX += 400
G.link(seq, 'then_1', ch[0], 'execute'); b.chain(*ch)

# world <-> screen on the map
def to_screen(wloc, x, y):
    bw = b.brk(wloc, x, y); bc_ = b.brk(centre(x, y + 200), x, y + 300)
    lu = b.add(b.div(b.sub(bw['Y'], bc_['Y'], x + 200, y), None, x + 400, y, db=repr(OW)), None, x + 600, y, db='0.5')
    mv = b.sub(None, b.div(b.sub(bw['X'], bc_['X'], x + 200, y + 150), None, x + 400, y + 150, db=repr(OW)), x + 600, y + 150, da='0.5')
    lv = b.add(b.mul(b.sub(mv, None, x + 800, y + 150, db='0.5'), ma, x + 1000, y + 150), None, x + 1200, y + 150, db='0.5')
    return b.add(ax, b.mul(lu, aw, x + 800, y), x + 1000, y), b.add(ay, b.mul(lv, ah, x + 1400, y + 150), x + 1600, y + 150), lu, lv
mouse = b.call(PCON, 'GetMousePosition', [F('LocationX', out=True), F('LocationY', out=True), bo('ReturnValue', out=True, default='false')], 2600, Y0 + 2400,
               target=b.pc(2400, Y0 + 2400), pure=True, const=True, tag='Mouse')
mx, my = (mouse, 'LocationX'), (mouse, 'LocationY')
lu_m = b.div(b.sub(mx, ax, 2800, Y0 + 2400), aw, 3000, Y0 + 2400)
lv_m = b.div(b.sub(my, ay, 2800, Y0 + 2500), ah, 3000, Y0 + 2500)
inarea = b.b2('BooleanAND', b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', lu_m, None, 3200, Y0 + 2400), b.dcmp('Less_DoubleDouble', lu_m, None, 3200, Y0 + 2450, db='1.0'), 3400, Y0 + 2420),
              b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', lv_m, None, 3200, Y0 + 2500), b.dcmp('Less_DoubleDouble', lv_m, None, 3200, Y0 + 2550, db='1.0'), 3400, Y0 + 2520), 3600, Y0 + 2470)
mvm = b.add(b.div(b.sub(lv_m, None, 3200, Y0 + 2650, db='0.5'), ma, 3400, Y0 + 2650), None, 3600, Y0 + 2650, db='0.5')
bcm = b.brk(centre(3400, Y0 + 2800), 3600, Y0 + 2800)
wmouse = b.vec(b.add(bcm['X'], b.mul(b.sub(None, mvm, 3800, Y0 + 2650, da='0.5'), None, 4000, Y0 + 2650, db=repr(OW)), 4200, Y0 + 2650),
               b.add(bcm['Y'], b.mul(b.sub(lu_m, None, 3800, Y0 + 2750, db='0.5'), None, 4000, Y0 + 2750, db=repr(OW)), 4200, Y0 + 2750), bcm['Z'], 4400, Y0 + 2700)
# confirm button rect
bw_, bh_ = b.mul(sc, None, 2600, Y0 + 3000, db='260.0'), b.mul(sc, None, 2600, Y0 + 3100, db='52.0')
bx_ = b.sub(b.mul(W, None, 2800, Y0 + 3000, db='0.5'), b.mul(bw_, None, 2800, Y0 + 3100, db='0.5'), 3000, Y0 + 3050)
by_ = b.sub(b.add(qy, qh, 2800, Y0 + 3200), b.mul(sc, None, 2800, Y0 + 3300, db='70.0'), 3000, Y0 + 3250)
onbtn = b.b2('BooleanAND', b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', mx, bx_, 3200, Y0 + 3000), b.dcmp('Less_DoubleDouble', mx, b.add(bx_, bw_, 3200, Y0 + 3100), 3400, Y0 + 3050), 3600, Y0 + 3020),
             b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', my, by_, 3200, Y0 + 3200), b.dcmp('Less_DoubleDouble', my, b.add(by_, bh_, 3200, Y0 + 3300), 3400, Y0 + 3250), 3600, Y0 + 3220), 3800, Y0 + 3100)

# then_2: input (only while choosing)
X = 1000; Y2 = Y0 + 4200
choosing = b.eqi(mode(X, Y2 + 200), 2, X + 200, Y2 + 200)
bi = b.branch(choosing, X + 300, Y2, tag='IfChoosing'); G.link(seq, 'then_2', bi, 'execute')
besc = b.branch(b.key('Escape', X + 500, Y2 + 300), X + 600, Y2, tag='IfEsc'); G.link(bi, 'then', besc, 'execute')
G.link(besc, 'then', b.me('CloseMap', X + 900, Y2 - 300), 'execute')
lmb = b.key('LeftMouseButton', X + 700, Y2 + 450)
conf = b.b2('BooleanAND', g('HasMark', BOOL, X + 900, Y2 + 600), b.b2('BooleanOR', b.key('Enter', X + 900, Y2 + 700), b.b2('BooleanAND', lmb, onbtn, X + 1100, Y2 + 800), X + 1300, Y2 + 750), X + 1500, Y2 + 650)
bcf = b.branch(conf, X + 900, Y2, tag='IfConfirm'); G.link(besc, 'else', bcf, 'execute')
cfm = b.sound('SFX_Map_Confirm', X + 1200, Y2 - 300); G.link(bcf, 'then', cfm, 'execute')
G.link(cfm, 'then', b.me('ConfirmMap', X + 1500, Y2 - 300), 'execute')
bclk = b.branch(b.b2('BooleanAND', lmb, inarea, X + 1500, Y2 + 450), X + 1300, Y2, tag='IfClick'); G.link(bcf, 'else', bclk, 'execute')
# click: an ordered cannon under the mouse? -> select it
sf = b.set('Picked', BOOL, None, X + 1600, Y2); G.link(bclk, 'then', sf, 'execute')
gc = b.getall(P_CANNON, CANNONC, X + 1850, Y2); G.link(sf, 'then', gc, 'execute')
fe = b.foreach(CANNONC, X + 2200, Y2); G.link(gc, 'then', fe, 'Exec'); b.wire((gc, 'OutActors'), fe, 'Array')
el = (fe, 'Array Element')
sx_, sy_, _lu, _lv = to_screen(b.loc(el, X + 2100, Y2 + 400), X + 2300, Y2 + 400)
near = b.dcmp('Less_DoubleDouble', b.math('Vector2D_Distance' if False else 'Vector_Distance2D', [(V('V1'), b.vec(sx_, sy_, None, X + 4000, Y2 + 450)), (V('V2'), b.vec(mx, my, None, X + 4000, Y2 + 600))],
              D('ReturnValue', out=True), X + 4200, Y2 + 500), b.mul(sc, None, X + 4200, Y2 + 650, db='22.0'), X + 4400, Y2 + 550)
ac = b.name('IsStarter')
G.node(ac, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'bIsConstFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Contains")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'object', 'obj': ACT, 'container': 'Array', 'ref': True, 'const': True},
        {'name': 'ItemToFind', 'cat': 'object', 'obj': ACT, 'ref': True}, bo('ReturnValue', out=True, default='false')], X + 4200, Y2 + 800)
b.wire(g('StarterCannons', arr(OBJV(ACT)), X + 4000, Y2 + 800), ac, 'TargetArray'); b.wire(el, ac, 'ItemToFind')
pickc = b.b2('BooleanAND', near, b.bnot((ac, 'ReturnValue'), X + 4400, Y2 + 800), X + 4600, Y2 + 650)
bpk = b.branch(pickc, X + 2600, Y2, tag='IfPick'); G.link(fe, 'LoopBody', bpk, 'execute')
s_sel = b.set('Sel', OBJV(ACT), el, X + 2900, Y2 - 200); s_pk = b.set('Picked', bo('v', default='true'), None, X + 3150, Y2 - 200)
G.link(bpk, 'then', s_sel, 'execute'); G.link(s_sel, 'then', s_pk, 'execute')
# after the loop: no cannon picked -> place the mark (NavMesh check)
bnp = b.branch(b.bnot(g('Picked', BOOL, X + 2600, Y2 + 1100), X + 2800, Y2 + 1100), X + 2700, Y2 + 900, tag='IfGround'); G.link(fe, 'Completed', bnp, 'execute')
prj = b.lib(NAVSYS, 'K2_ProjectPointToNavigation', [WC(), V('Point'), V('ProjectedLocation', out=True), ob('NavData', NAVDATA), {'name': 'FilterClass', 'cat': 'class', 'obj': NAVFILT},
            V('QueryExtent', default='300.000000,300.000000,20000.000000'), bo('ReturnValue', out=True, default='false')], X + 2900, Y2 + 1200, pure=True, tag='OnNav')
b.wire(wmouse, prj, 'Point')
bnv = b.branch((prj, 'ReturnValue'), X + 3000, Y2 + 900, tag='IfReachable'); G.link(bnp, 'then', bnv, 'execute')
smk = b.set('Mark', V('v'), (prj, 'ProjectedLocation'), X + 3300, Y2 + 700); shm = b.set('HasMark', bo('v', default='true'), None, X + 3550, Y2 + 700)
mks = b.sound('SFX_Map_Mark', X + 3800, Y2 + 700)
G.link(bnv, 'then', smk, 'execute'); b.chain(smk, shm, mks)
smg = b.set('MsgUntil', DBL, b.add(rn, None, X + 3200, Y2 + 1250, db='2.5'), X + 3300, Y2 + 1050); G.link(bnv, 'else', smg, 'execute')

# then_3: cannon icons
X = 1000; Y3 = Y0 + 6400
bre = b.branch(b.dcmp('Greater_DoubleDouble', reveal, None, X, Y3 + 300, db='0.5'), X + 200, Y3, tag='IfRevealed'); G.link(seq, 'then_3', bre, 'execute')
gold_mid = lambda x, y: g('GoldMID', OBJV(MIDC), x, y)
ag = b.mid_scalar(gold_mid(X + 400, Y3 + 300), 'Age', b.mul(rn, None, X + 400, Y3 + 400, db='0.8'), X + 500, Y3); G.link(bre, 'then', ag, 'execute')
gc2 = b.getall(P_CANNON, CANNONC, X + 800, Y3); G.link(ag, 'then', gc2, 'execute')
fe2 = b.foreach(CANNONC, X + 1150, Y3); G.link(gc2, 'then', fe2, 'Exec'); b.wire((gc2, 'OutActors'), fe2, 'Array')
el2 = (fe2, 'Array Element')
sx2, sy2, _l, _v = to_screen(b.loc(el2, X + 1100, Y3 + 400), X + 1300, Y3 + 400)
ac2 = b.name('IsStarter')
G.node(ac2, 'K2Node_CallArrayFunction', ['bIsPureFunc=True', 'bIsConstFunc=True', 'FunctionReference=(MemberParent=%s,MemberName="Array_Contains")' % KARR],
       [selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'object', 'obj': ACT, 'container': 'Array', 'ref': True},
        {'name': 'ItemToFind', 'cat': 'object', 'obj': ACT, 'ref': True}, bo('ReturnValue', out=True, default='false')], X + 3000, Y3 + 800)
b.wire(g('StarterCannons', arr(OBJV(ACT)), X + 2800, Y3 + 800), ac2, 'TargetArray'); b.wire(el2, ac2, 'ItemToFind')
isz = b.mul(sc, None, X + 3000, Y3 + 1000, db='34.0')
ihalf = b.mul(isz, None, X + 3200, Y3 + 1000, db='0.5')
ix, iy = b.sub(sx2, ihalf, X + 3200, Y3 + 400), b.sub(sy2, ihalf, X + 3200, Y3 + 550)
bst = b.branch((ac2, 'ReturnValue'), X + 1500, Y3, tag='IfStarter'); G.link(fe2, 'LoopBody', bst, 'execute')
d1 = b.drawmat(hud, g('GreyMID', OBJV(MIDC), X + 1700, Y3 - 100), ix, iy, isz, isz, X + 1800, Y3 - 300, 'StarterIcon'); G.link(bst, 'then', d1, 'execute')
t1 = b.text(hud, None, b.rgba(INK, 0.9, X + 1900, Y3 - 50), b.add(sx2, ihalf, X + 1900, Y3 + 50), b.sub(sy2, ihalf, X + 1900, Y3 + 150),
            b.mul(sc, None, X + 1900, Y3 + 250, db='0.22'), X + 2100, Y3 - 300, tag='StarterLbl', dtxt='fixed')
G.link(d1, 'then', t1, 'execute')
d2 = b.drawmat(hud, gold_mid(X + 1700, Y3 + 200), ix, iy, isz, isz, X + 1800, Y3 + 100, 'OrderedIcon'); G.link(bst, 'else', d2, 'execute')
issel = b.math('EqualEqual_ObjectObject', [(ob('A', OBJ), el2), (ob('B', OBJ), g('Sel', OBJV(ACT), X + 1900, Y3 + 500))], bo('ReturnValue', out=True), X + 2100, Y3 + 450)
t2 = b.text(hud, b.selstr(None, None, issel, X + 2100, Y3 + 350, da='moving', db='yours'), b.rgba(INK, 0.9, X + 2100, Y3 + 250), b.add(sx2, ihalf, X + 2100, Y3 + 150),
            b.sub(sy2, ihalf, X + 2300, Y3 + 150), b.mul(sc, None, X + 2300, Y3 + 250, db='0.22'), X + 2300, Y3 + 100, tag='OrderedLbl')
G.link(d2, 'then', t2, 'execute')

# then_4: marker, demo pulse, infographic, confirm button, message
X = 1000; Y4 = Y0 + 8400
ink = lambda a_, x, y: b.rgba(INK, a_, x, y)
step_y = b.add(qy, b.mul(qh, None, X, Y4 + 300, db='0.045'), X + 200, Y4 + 300)
ts = b.mul(sc, None, X, Y4 + 400, db='0.30')
cur_step = b.math('SelectInt', [(it('A', default='2'), None), (it('B', default='1'), None), (bo('bPickA', default='false'), g('HasMark', BOOL, X, Y4 + 500))], it('ReturnValue', out=True), X + 200, Y4 + 500)
ch = []
XX = X + 400
for i, txt in enumerate(['1   Click a spot on the map', '2   ENTER or CONFIRM', '3   The crew brings the cannon']):
    ai = b.mul(b.lin(a, 0.75 + 0.04 * i, 0.3, XX, Y4 + 700), b.sub(None, b.mul(b.math('Conv_BoolToDouble', [(bo('InBool', default='false'), closing)], D('ReturnValue', out=True), XX, Y4 + 900),
               None, XX + 200, Y4 + 900, db='1.0'), XX + 400, Y4 + 900, da='1.0'), XX + 600, Y4 + 800)
    active = b.eqi(cur_step, i + 1, XX, Y4 + 1000)
    cc = b.colr(b.self_(None, None, active, XX + 200, Y4 + 1100, da=repr(GOLD[0]), db=repr(INK[0])), b.self_(None, None, active, XX + 200, Y4 + 1200, da=repr(GOLD[1] * 0.8), db=repr(INK[1])),
                b.self_(None, None, active, XX + 200, Y4 + 1300, da=repr(GOLD[2] * 0.5), db=repr(INK[2])), ai, XX + 400, Y4 + 1200)
    tx = b.add(b.add(qx, b.mul(qw, None, XX, Y4 + 1400, db=repr(0.10 + 0.28 * i)), XX + 200, Y4 + 1400), b.mul(b.sub(None, ai, XX, Y4 + 1500, da='1.0'), b.mul(sc, None, XX, Y4 + 1600, db='30.0'), XX + 200, Y4 + 1500), XX + 400, Y4 + 1450)
    ch.append(b.text(hud, None, cc, tx, step_y, ts, XX + 300, Y4, tag='Step%d' % (i + 1), dtxt=txt)); XX += 700
G.link(seq, 'then_4', ch[0], 'execute'); b.chain(*ch)
# legend line at the bottom edge
leg = b.text(hud, None, ink(b.mul(reveal, None, XX, Y4 + 300, db='0.85'), XX + 200, Y4 + 300), b.add(qx, b.mul(qw, None, XX, Y4 + 400, db='0.10'), XX + 200, Y4 + 400),
             b.sub(b.add(qy, qh, XX, Y4 + 500), b.mul(qh, None, XX, Y4 + 600, db='0.085'), XX + 200, Y4 + 550), b.mul(sc, None, XX, Y4 + 700, db='0.22'), XX + 400, Y4,
             tag='Legend', dtxt='Gold ring: your cannon - click it, then a new spot, to move it.     Grey: starter cannons stay.     Esc: close')
G.link(ch[-1], 'then', leg, 'execute'); XX += 700
# demo pulse until the first mark (a field spot right of the castle)
bdm = b.branch(b.b2('BooleanAND', b.bnot(g('HasMark', BOOL, XX, Y4 + 300), XX + 200, Y4 + 300), b.dcmp('Greater_DoubleDouble', reveal, None, XX, Y4 + 400, db='0.9'), XX + 400, Y4 + 350), XX + 200, Y4, tag='IfDemo')
G.link(leg, 'then', bdm, 'execute')
dm = lambda x, y: g('DemoMID', OBJV(MIDC), x, y)
dage = b.mid_scalar(dm(XX + 400, Y4 + 200), 'Age', b.mul(rn, None, XX + 400, Y4 + 500, db='0.9'), XX + 500, Y4 - 200); G.link(bdm, 'then', dage, 'execute')
dsz = b.mul(sc, None, XX + 600, Y4 + 600, db='90.0')
ddx = b.sub(b.add(ax, b.mul(aw, None, XX + 600, Y4 + 700, db='0.72'), XX + 800, Y4 + 700), b.mul(dsz, None, XX + 800, Y4 + 800, db='0.5'), XX + 1000, Y4 + 750)
ddy = b.sub(b.add(ay, b.mul(ah, None, XX + 600, Y4 + 900, db='0.55'), XX + 800, Y4 + 900), b.mul(dsz, None, XX + 800, Y4 + 1000, db='0.5'), XX + 1000, Y4 + 950)
ddraw = b.drawmat(hud, dm(XX + 700, Y4 + 300), ddx, ddy, dsz, dsz, XX + 800, Y4 - 200, 'DemoPulse'); G.link(dage, 'then', ddraw, 'execute')
dtx = b.text(hud, None, b.rgba(GOLD, 1.0, XX + 1000, Y4 + 1100), b.add(ddx, dsz, XX + 1100, Y4 + 1200), b.add(ddy, b.mul(dsz, None, XX + 1100, Y4 + 1300, db='0.35'), XX + 1300, Y4 + 1250),
             b.mul(sc, None, XX + 1300, Y4 + 1350, db='0.26'), XX + 1100, Y4 - 200, tag='DemoTxt', dtxt='click here')
G.link(ddraw, 'then', dtx, 'execute'); XX += 1500
# the mark: red ring + an ink X, and the CONFIRM button
bmk = b.branch(g('HasMark', BOOL, XX, Y4 + 300), XX + 200, Y4, tag='IfMark')
G.link(bdm, 'else', bmk, 'execute'); G.link(dtx, 'then', bmk, 'execute')
mx2, my2, _a, _b = to_screen(g('Mark', V('v'), XX, Y4 + 500), XX + 200, Y4 + 500)
msz = b.mul(sc, None, XX + 1800, Y4 + 700, db='46.0')
mdraw = b.drawmat(hud, g('MarkMID', OBJV(MIDC), XX + 400, Y4 + 300), b.sub(mx2, b.mul(msz, None, XX + 2000, Y4 + 700, db='0.5'), XX + 2200, Y4 + 650),
                  b.sub(my2, b.mul(msz, None, XX + 2000, Y4 + 800, db='0.5'), XX + 2200, Y4 + 800), msz, msz, XX + 500, Y4 - 200, 'MarkRing')
G.link(bmk, 'then', mdraw, 'execute')
xt = b.text(hud, None, b.rgba(RED, 1.0, XX + 2200, Y4 + 900), b.sub(mx2, b.mul(sc, None, XX + 2200, Y4 + 1000, db='11.0'), XX + 2400, Y4 + 1000),
            b.sub(my2, b.mul(sc, None, XX + 2200, Y4 + 1100, db='20.0'), XX + 2400, Y4 + 1100), b.mul(sc, None, XX + 2400, Y4 + 1200, db='0.5'), XX + 800, Y4 - 200, tag='InkX', dtxt='X')
G.link(mdraw, 'then', xt, 'execute')
pulse = b.add(b.mul(b.sin(b.mul(rn, None, XX + 900, Y4 + 1400, db='5.0'), XX + 1100, Y4 + 1400), None, XX + 1300, Y4 + 1400, db='0.12'), None, XX + 1500, Y4 + 1400, db='0.88')
brd = b.rect(hud, b.rgba(GOLD, 1.0, XX + 1100, Y4 + 1500), b.sub(bx_, b.mul(sc, None, XX + 1100, Y4 + 1600, db='3.0'), XX + 1300, Y4 + 1600),
             b.sub(by_, b.mul(sc, None, XX + 1100, Y4 + 1700, db='3.0'), XX + 1300, Y4 + 1700), b.add(bw_, b.mul(sc, None, XX + 1100, Y4 + 1800, db='6.0'), XX + 1300, Y4 + 1800),
             b.add(bh_, b.mul(sc, None, XX + 1100, Y4 + 1900, db='6.0'), XX + 1300, Y4 + 1900), XX + 1100, Y4 - 200, tag='BtnFrame')
G.link(xt, 'then', brd, 'execute')
bfc = b.rect(hud, b.colr(b.mul(pulse, None, XX + 1500, Y4 + 1500, db='0.30'), b.mul(pulse, None, XX + 1500, Y4 + 1600, db='0.18'), b.mul(pulse, None, XX + 1500, Y4 + 1700, db='0.08'), None, XX + 1700, Y4 + 1600),
             bx_, by_, bw_, bh_, XX + 1400, Y4 - 200, tag='BtnFace')
G.link(brd, 'then', bfc, 'execute')
btx = b.text(hud, b.selstr(None, None, b.valid(g('Sel', OBJV(ACT), XX + 1700, Y4 + 2000), XX + 1900, Y4 + 2000), XX + 2100, Y4 + 1950, da='MOVE CANNON', db='CONFIRM  (800 gold)'),
             b.rgba(GOLD, 1.0, XX + 1900, Y4 + 2100), b.add(bx_, b.mul(sc, None, XX + 1900, Y4 + 2200, db='22.0'), XX + 2100, Y4 + 2200),
             b.add(by_, b.mul(sc, None, XX + 1900, Y4 + 2300, db='13.0'), XX + 2100, Y4 + 2300), b.mul(sc, None, XX + 2100, Y4 + 2400, db='0.28'), XX + 1700, Y4 - 200, tag='BtnText')
G.link(bfc, 'then', btx, 'execute'); XX += 2600
# message (unreachable spot)
bmsg = b.branch(b.dcmp('Less_DoubleDouble', rn, g('MsgUntil', DBL, XX, Y4 + 300), XX + 200, Y4 + 300), XX + 200, Y4, tag='IfMsg')
G.link(bmk, 'else', bmsg, 'execute'); G.link(btx, 'then', bmsg, 'execute')
mtx = b.text(hud, None, b.rgba(RED, 1.0, XX + 300, Y4 + 400), b.add(qx, b.mul(qw, None, XX + 300, Y4 + 500, db='0.36'), XX + 500, Y4 + 500),
             b.sub(b.add(qy, qh, XX + 300, Y4 + 600), b.mul(qh, None, XX + 300, Y4 + 700, db='0.16'), XX + 500, Y4 + 650), b.mul(sc, None, XX + 500, Y4 + 800, db='0.30'),
             XX + 500, Y4 - 200, tag='MsgTxt', dtxt='The crew cannot reach that spot')
G.link(bmsg, 'then', mtx, 'execute')
write(G, 'BPC_CannonMap_graph.txt')
VARS = [('Mode', 'int', '0', '0 closed, 1 unrolling, 2 choosing, 3 rolling up'), ('OpenT', 'real', '0.0', 'real time opened'), ('CloseT', 'real', '0.0', 'real time closing started'),
        ('HasMark', 'bool', 'false', 'a spot is marked'), ('Mark', 'vector', '0,0,0', 'the marked spot (on the NavMesh)'), ('Sel', 'obj:Actor', '', 'the ordered cannon being moved'),
        ('Picked', 'bool', 'false', 'scratch: this click picked a cannon'), ('MsgUntil', 'real', '0.0', 'shows "cannot reach" until'),
        ('Price', 'int', '800', 'gold for a new cannon (same as #230)'), ('StarterCannons', 'arr:Actor', '', 'cannons in the level at Play: locked'),
        ('CastleCentre', 'vector', '2300.000000,1725.000000,0.000000', 'map centre (the #41 castle box centre)'), ('MapCap', 'obj:Actor', '', 'BP_MapCapture'),
        ('Cap', 'obj:SceneCaptureComponent2D', '', 'its capture'), ('ScrollMID', 'obj:MaterialInstanceDynamic', '', ''), ('GoldMID', 'obj:MaterialInstanceDynamic', '', ''),
        ('GreyMID', 'obj:MaterialInstanceDynamic', '', ''), ('MarkMID', 'obj:MaterialInstanceDynamic', '', ''), ('DemoMID', 'obj:MaterialInstanceDynamic', '', '')]

# ================================================================================================= BP_CannonOrder: O opens the map
G = Graph(); b = B9(G, 'mapo')
pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 0, 300, pure=True, tag='Hero')
fcm = b.call(ACT, 'GetComponentByClass', [{'name': 'ComponentClass', 'cat': 'class', 'obj': CLS('ActorComponent'), 'dobj': cpath(P_CM)}, ob('ReturnValue', CMC_, out=True)],
             200, 300, target=(pp, 'ReturnValue'), pure=True, const=True, tag='FindMap')
bv = b.branch(b.valid((fcm, 'ReturnValue'), 400, 300), 300, 0, tag='MapIfValid')
om = b.call(CMC_, 'OpenMap', [], 600, 0, target=(fcm, 'ReturnValue'), tag='MapOpen'); G.link(bv, 'then', om, 'execute')
write(G, 'CannonOrder_Map_graph.txt')
json.dump({'blueprint': 'BP_CannonOrder', '_built_on': 'handoffs/deploy-cannon-230/BP_CannonOrder_graph.txt (checkking #239, not pasted yet: export it after pasting)',
           'pastes': [{'file': 'CannonOrder_Map_graph.txt', 'offset': [400, 2600]}],
           'rewires': [{'from': 'coIfInRange12.then', 'to': bv + '.execute', 'replace': True,
                        'note': 'O in range opens the scroll map (the map takes the gold on CONFIRM); the old pad/gold chain stays but is no longer reached'}]},
          open(os.path.join(HERE, 'manifest_cannonorder.json'), 'w'), indent=1)

# ================================================================================================= BPC_MotionFX: draw the map
G = Graph(); b = B9(G, 'mm')
ms = b.seq('MapDrawSeq', 2, 0, 0)
own = b.name('Owner'); callfn(G, own, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=0, y=300, self_hidden=True)
fcm = b.call(ACT, 'GetComponentByClass', [{'name': 'ComponentClass', 'cat': 'class', 'obj': CLS('ActorComponent'), 'dobj': cpath(P_CM)}, ob('ReturnValue', CMC_, out=True)],
             200, 300, target=(own, 'ReturnValue'), pure=True, const=True, tag='FindMap')
bv = b.branch(b.valid((fcm, 'ReturnValue'), 400, 300), 300, 200, tag='MapIfValid'); G.link(ms, 'then_1', bv, 'execute')
dmc = b.call(CMC_, 'DrawMap', [ob('Hud', HUDC), it('SizeX', default='0'), it('SizeY', default='0')], 600, 200, target=(fcm, 'ReturnValue'), tag='MapDraw')
G.link(bv, 'then', dmc, 'execute')
write(G, 'MotionFX_Map_graph.txt')
json.dump({'blueprint': 'BPC_MotionFX', '_built_on': 'handoffs/reveal-aaa-268/BPC_MotionFX_v2_graph.txt (#269; export it after pasting)',
           'pastes': [{'file': 'MotionFX_Map_graph.txt', 'offset': [0, -1200]}],
           'rewires': [{'from': 'DrawReveal.then', 'to': 'MapDrawSeq.execute', 'replace': True, 'note': 'was -> RevealSeq'},
                       {'from': 'MapDrawSeq.then_0', 'to': 'RevealSeq.execute', 'note': 'the reveal first, unchanged'},
                       {'from': 'DrawReveal.Hud', 'to': dmc + '.Hud'}, {'from': 'DrawReveal.SizeX', 'to': dmc + '.SizeX'}, {'from': 'DrawReveal.SizeY', 'to': dmc + '.SizeY'}]},
          open(os.path.join(HERE, 'manifest_motionfx_map.json'), 'w'), indent=1)


# ================================================================================================= BPVar lines
def vt(kind):
    if kind == 'real': return 'PinCategory="real",PinSubCategory="double"'
    if kind in ('int', 'bool'): return 'PinCategory="%s"' % kind
    if kind == 'vector': return 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"'
    if kind.startswith('arr:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'",ContainerType=Array' % kind[4:]
    if kind.startswith('obj:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % kind[4:]
    raise ValueError(kind)
used = {p for n in Graph().nodes for p in n[2]}
bpv = lambda n, k, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'cannonmap283/' + n).hex.upper(), vt(k), n, d)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# BPC_CannonMap (#283) - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' + '\n'.join(bpv(*v[:3]) for v in VARS) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# BPC_CannonMap variables (BPVar lines in VARIABLES_BPVar.txt)\n\n| Name | Default | Meaning |\n|---|---|---|\n')
    for n, _k, d, m in VARS: f.write('| %s | %s | %s |\n' % (n, d or '-', m))
print('BPVar lines:', len(VARS))
