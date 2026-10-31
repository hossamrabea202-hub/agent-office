# #226 follow-up v2 (adjustedfilm, 2026-10-31): heavy rain at night puts out torches (#290), and a soldier relights them
# afterwards (#355, owner W: "if rain putt off torches, soldier lights it up later").
#   "<blender python>" -I gen_torches226.py -> Weather_Torches_graph.txt + manifest_weather_torches.json + 2 BPVar lines,
#                                              BP_TorchBearer_graph.txt + VARIABLES_TorchBearer_BPVar.txt
# v2 changes against v1 (not pasted yet): only the FIRE goes out (the torch's light + fire FX components), the iron torch
# stays on the wall (v1 hid the whole actor); and torches no longer pop back on by themselves.
# On BPC_Weather's free WxSeq.then_4: Doused target = BP_DayNight.IsNight AND CurRain > 0.6. Only when it changes:
#   doused        -> 2 of every 3 actors tagged NightLight lose their fire (light + FX hidden), remembered in DousedList
#                    (every third keeps burning: under eaves, in the gatehouse); notice "The rain puts out the torches."
#   eased, night  -> a torch-bearer soldier (BP_TorchBearer) steps out next to a soldier of the garrison (or the hero) and
#                    walks to each doused torch in turn, relighting it, then walks back and leaves
#   eased, day    -> fires restored at once (daylight: BP_DayNight hides the torches itself)
# BP_TorchBearer.Begin(Torches, Weather): every 0.4 s: walk (AI move) to the next torch; within 1.7 m (or after 25 s, if the
#   torch is out of reach) relight it, then the next. Stops early and relights the rest at once if day breaks; goes home if
#   the rain douses again (the weather keeps its own list). Home = where it appeared; destroyed there (or after 40 s).
import os, sys, json, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
P_DN = '/Game/CastleDefender/Environment/DayNight/BP_DayNight'
DNC = BPC(P_DN, 'BP_DayNight')
NOTC = BPC('/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD', 'BP_NoticeHUD')
P_WX = '/Game/CastleDefender/Environment/Weather/BPC_Weather'
WXC = BPC(P_WX, 'BPC_Weather')
P_TB = '/Game/CastleDefender/Environment/Weather/BP_TorchBearer'
TBC = BPC(P_TB, 'BP_TorchBearer')
LIGHTC, FXC, ACOMP = CLS('LightComponent'), CLS('FXSystemComponent'), CLS('ActorComponent')
ACTA = arr(ob('v', ACT))


def fire(b, torch, on, x, y):
    """torch's light + fire FX components visible on/off. Returns (first node, last node) of the exec chain."""
    nodes = []
    for k, cls in enumerate((LIGHTC, FXC)):
        gc = b.call(ACT, 'K2_GetComponentsByClass', [{'name': 'ComponentClass', 'cat': 'class', 'obj': '"/Script/CoreUObject.Class\'/Script/Engine.ActorComponent\'"',
                                                      'dobj': cls.strip('"').split("'")[1]}, arr(ob('ReturnValue', ACOMP, out=True))],
                    x + 600 * k, y + 250, target=torch, pure=True, const=True, tag='Comps')
        fe = b.foreach(ACOMP, x + 600 * k, y)
        b.wire((gc, 'ReturnValue'), fe, 'Array')
        sv = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='true' if on else 'false'), bo('bPropagateToChildren', default='true')],
                    x + 600 * k + 300, y - 150, target=(fe, 'Array Element'), tag='Fire' + ('On' if on else 'Off'))
        b.link(fe, 'LoopBody', sv, 'execute')
        nodes.append(fe)
    b.link(nodes[0], 'Completed', nodes[1], 'Exec')
    return (nodes[0], 'Exec'), (nodes[1], 'Completed')


def check_write(G, fname):
    pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
    bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
    names = [n[0] for n in G.nodes]
    if bad or len(names) != len(set(names)): raise SystemExit('%s: bad %s dup %s' % (fname, bad[:5], [n for n in names if names.count(n) > 1][:5]))
    open(os.path.join(HERE, fname), 'w', newline='\r\n').write(G.render()); print('%s: nodes %d, links %d' % (fname, len(G.nodes), len(G.links)))


def chain_in(b, src, dst):     # src: (node, pin) exec out ; dst: (node, pin) exec in
    b.link(src[0], src[1], dst[0], dst[1])


# ================================================================ BPC_Weather add-on
G = Graph(); b = bpkit.B(G, 'wt'); g = b.get
dn = lambda x, y: g('DN', ob('v', DNC), x, y)
vd = b.branch(b.valid(dn(0, 300), 150, 300), 200, 0, tag='TorchIfDN')
night = b.getm('IsNight', DNC, BOOL, dn(200, 450), 350, 450)
tgt = b.b2('BooleanAND', night, b.dcmp('Greater_DoubleDouble', g('CurRain', DBL, 350, 600), None, 550, 600, db='0.6'), 750, 500)
ch = b.branch(b.math('NotEqual_BoolBool', [(bo('A', default='false'), tgt), (bo('B', default='false'), g('Doused', BOOL, 750, 650))], bo('ReturnValue', out=True), 950, 600), 500, 0, tag='IfTorchChange')
G.link(vd, 'then', ch, 'execute')
sd = b.set('Doused', BOOL, tgt, 800, 0); G.link(ch, 'then', sd, 'execute')
bd = b.branch(g('Doused', BOOL, 1000, 200), 1050, 0, tag='IfDousedNow'); G.link(sd, 'then', bd, 'execute')
# ---- doused: put out 2 of 3, remember them
cl = b.name('ClearList')
G.node(cl, 'K2Node_CallArrayFunction', ['FunctionReference=(MemberParent=%s,MemberName="Array_Clear")' % KARR],
       [ex(), ex('then', True), selfpin(KARR, hidden=True), {'name': 'TargetArray', 'cat': 'wildcard', 'container': 'Array', 'ref': True}], 1300, -300)
b.wire(g('DousedList', ACTA, 1150, -150), cl, 'TargetArray'); G.link(bd, 'then', cl, 'execute')
ga = b.lib(GS, 'GetAllActorsWithTag', [WC(), {'name': 'Tag', 'cat': 'name', 'default': 'NightLight'}, arr(ob('OutActors', ACT, out=True))], 1550, -300, tag='FindTorches')
G.link(cl, 'then', ga, 'execute')
fe = b.foreach(ACT, 1850, -300); G.link(ga, 'then', fe, 'Exec'); b.wire((ga, 'OutActors'), fe, 'Array')
keep = b.icmp('EqualEqual_IntInt', b.i2('Percent_IntInt', (fe, 'Array Index'), None, 1950, 0, db='3'), None, 2150, 0, db='0')
bk = b.branch(keep, 2150, -300, tag='IfKeep'); G.link(fe, 'LoopBody', bk, 'execute')
ad = b.aadd('DousedList', ob('v', ACT), (fe, 'Array Element'), 2400, -450); G.link(bk, 'else', ad, 'execute')
fin, fout = fire(b, (fe, 'Array Element'), False, 2700, -450); chain_in(b, (ad, 'then'), fin)
pcn = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], 2000, 300, pure=True, tag='PC')
hud = b.call(PCON, 'GetHUD', [ob('ReturnValue', CLS('HUD'), out=True)], 2200, 300, target=(pcn, 'ReturnValue'), pure=True, const=True, tag='HUD')
nc = b.name('AsNoticeHUD'); cast(G, nc, NOTC, 'AsBP Notice HUD', 2300, 100); b.wire((hud, 'ReturnValue'), nc, 'Object'); G.link(fe, 'Completed', nc, 'execute')
pn = b.call(NOTC, 'PushNotice', [S('Text', default='The rain puts out the torches.'), it('Tier', default='1')], 2600, 100, target=(nc, 'AsBP Notice HUD'), tag='Notice')
G.link(nc, 'then', pn, 'execute')
# ---- eased: night -> torch-bearer, day -> fires back at once
Y = 900
bn = b.branch(b.getm('IsNight', DNC, BOOL, dn(1100, Y + 200), 1250, Y + 200), 1300, Y, tag='IfStillNight'); G.link(bd, 'else', bn, 'execute')
# day: restore all at once
fe2 = b.foreach(ACT, 1600, Y + 500); b.wire(g('DousedList', ACTA, 1450, Y + 650), fe2, 'Array'); G.link(bn, 'else', fe2, 'Exec')
fin2, fout2 = fire(b, (fe2, 'Array Element'), True, 1900, Y + 500); chain_in(b, (fe2, 'LoopBody'), fin2)
# night: spawn the torch-bearer next to a garrison soldier (else the hero)
sol = b.actor_of('/Game/CastleDefender/Characters/Knight/BP_SoldierSword', ACT, 1600, Y)
G.link(bn, 'then', sol, 'execute')
hero = b.lib(GS, 'GetPlayerCharacter', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CHARC, out=True)], 1600, Y + 250, pure=True, tag='Hero')
vs = b.valid((sol, 'ReturnValue'), 1800, Y + 150)
sl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1800, Y + 250, target=(sol, 'ReturnValue'), pure=True, const=True, tag='SolLoc')
hl = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1800, Y + 350, target=(hero, 'ReturnValue'), pure=True, const=True, tag='HeroLoc')
at = b.selvec((sl, 'ReturnValue'), (hl, 'ReturnValue'), vs, 2000, Y + 250)
at2 = b.v2('Add_VectorVector', at, None, 2200, Y + 250, db='150, 0, 30')
sp = spawn(b, P_TB, TBC, transform(b, at2, 2350, Y + 250), 2500, Y)
G.link(sol, 'then', sp, 'execute')
self_c = b.name('SelfC'); G.node(self_c, 'K2Node_Self', [], [{'name': 'self', 'cat': 'object', 'sub': 'self', 'out': True}], 2600, Y + 400)
beg = b.call(TBC, 'Begin', [arr(ob('Torches', ACT)), ob('Weather', ACOMP)], 2800, Y, target=(sp, 'ReturnValue'), tag='BearerBegin')
b.wire(g('DousedList', ACTA, 2600, Y + 250), beg, 'Torches'); b.wire((self_c, 'self'), beg, 'Weather'); G.link(sp, 'then', beg, 'execute')
check_write(G, 'Weather_Torches_graph.txt')
json.dump({'blueprint': 'BPC_Weather', '_built_on': 'handoffs/weather-226/BPC_Weather_graph.txt (#275; export it after pasting)',
           'pastes': [{'file': 'Weather_Torches_graph.txt', 'offset': [0, 6200]}],
           'rewires': [{'from': 'WxSeq.then_4', 'to': vd + '.execute', 'note': 'the free 5th output of the weather tick'}]},
          open(os.path.join(HERE, 'manifest_weather_torches.json'), 'w'), indent=1)
bpv = lambda n, t, d, tag: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, tag + n).hex.upper() if n != 'Doused' else '2FBBCDEA7BC85357BD016B4671BD8848', t, n, d)
ACTT = 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.Actor\'"'
open(os.path.join(HERE, 'VARIABLES_Torches_BPVar.txt'), 'w', newline='\r\n').write(
    '# BPC_Weather - 2 variables for the torches add-on (v2)\n' + bpv('Doused', 'PinCategory="bool"', 'false', 'wt/') + '\n' +
    bpv('DousedList', ACTT + ',ContainerType=Array', '', 'torch355/') + '\n')

# ================================================================ BP_TorchBearer
G = Graph(); b = bpkit.B(G, 'tb'); g = b.get
b.event('Begin', [arr(ob('Torches', ACT)), ob('Weather', ACOMP)], 0, 0)
s1 = b.set('List', ACTA, ('Begin', 'Torches'), 300, 0)
s2 = b.set('Idx', INT, None, 550, 0)
s3 = b.set('Home', VECT, b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 550, 250, pure=True, const=True, tag='MyLoc') and ('tbMyLoc%d' % b.n, 'ReturnValue'), 800, 0)
cw = 'tbCastWx'; cast(G, cw, WXC, 'AsWeather', 1050, 0); b.wire(('Begin', 'Weather'), cw, 'Object')
s4 = b.set('Wx', ob('v', WXC), (cw, 'AsWeather'), 1350, 0)
fdn = b.actor_of(P_DN, DNC, 1600, 0)
s5 = b.set('DN', ob('v', DNC), (fdn, 'ReturnValue'), 1850, 0)
tm = b.timer('Step', 2100, 0, dtime='0.4', loop=True); b.wire(b.self_node(1950, 200), tm, 'Object')
G.link('Begin', 'then', s1, 'execute'); b.chain(s1, s2, s3, cw); G.link(cw, 'then', s4, 'execute'); G.link(cw, 'CastFailed', s4, 'execute'); b.chain(s4, fdn, s5, tm)
# ---- Step
Y = 800
b.event('Step', [], 0, Y)
st = b.set('T', DBL, b.d2('Add_DoubleDouble', g('T', DBL, 150, Y + 250), None, 300, Y + 250, db='0.4'), 250, Y)
G.link('Step', 'then', st, 'execute')
n_ = b.alen('List', ob('v', ACT), 400, Y + 400)
more = b.icmp('Less_IntInt', g('Idx', INT, 550, Y + 500), n_, 750, Y + 450)
day = b.bnot(b.b2('BooleanAND', b.valid(g('DN', ob('v', DNC), 550, Y + 650), 700, Y + 650), b.getm('IsNight', DNC, BOOL, g('DN', ob('v', DNC), 550, Y + 750), 700, Y + 750), 900, Y + 700), 1050, Y + 700)
wet = b.b2('BooleanAND', b.valid(g('Wx', ob('v', WXC), 550, Y + 850), 700, Y + 850), b.getm('Doused', WXC, BOOL, g('Wx', ob('v', WXC), 550, Y + 950), 700, Y + 950), 900, Y + 900)
bday = b.branch(b.b2('BooleanAND', more, day, 1100, Y + 500), 550, Y, tag='IfDayBreak'); G.link(st, 'then', bday, 'execute')
# day broke: relight the rest at once, go home
fe = b.foreach(ACT, 850, Y - 400); b.wire(g('List', ACTA, 700, Y - 250), fe, 'Array'); G.link(bday, 'then', fe, 'Exec')
fin, fout = fire(b, (fe, 'Array Element'), True, 1150, Y - 400); chain_in(b, (fe, 'LoopBody'), fin)
done = b.set('Idx', INT, n_, 1150, Y - 150); G.link(fe, 'Completed', done, 'execute')
brain = b.branch(wet, 850, Y, tag='IfRainAgain'); G.link(bday, 'else', brain, 'execute')
rain_end = b.set('Idx', INT, b.alen('List', ob('v', ACT), 1000, Y + 250), 1150, Y + 150); G.link(brain, 'then', rain_end, 'execute')
bm = b.branch(more, 1150, Y, tag='IfMoreTorches'); G.link(brain, 'else', bm, 'execute')
# work: walk to List[Idx]; near (1.7 m) or 25 s -> relight, next
cur = b.aget('List', ob('v', ACT), g('Idx', INT, 1250, Y - 100), 1350, Y - 150)
cl_ = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1600, Y - 150, target=cur, pure=True, const=True, tag='TorchLoc')
ctrl = b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], 1600, Y + 300, PAWN, pure=True, const=True)
mv = b.lib(CLS('AIBlueprintHelperLibrary'), 'SimpleMoveToLocation', [ob('Controller', CTRL), V('Goal')], 1800, Y)
b.wire((ctrl, 'ReturnValue'), mv, 'Controller'); b.wire((cl_, 'ReturnValue'), mv, 'Goal'); G.link(bm, 'then', mv, 'execute')
dist = b.math('Vector_Distance2D', [(V('V1'), (cl_, 'ReturnValue')), (V('V2'), b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1800, Y + 400, pure=True, const=True, tag='MyLoc2') and ('tbMyLoc2%d' % b.n, 'ReturnValue'))],
              D('ReturnValue', out=True), 2000, Y + 350)
arrive = b.b2('BooleanOR', b.dcmp('Less_DoubleDouble', dist, None, 2200, Y + 350, db='170.0'), b.dcmp('Greater_DoubleDouble', g('T', DBL, 2050, Y + 550), None, 2200, Y + 500, db='25.0'), 2400, Y + 400)
ba = b.branch(arrive, 2100, Y, tag='IfAtTorch'); G.link(mv, 'then', ba, 'execute')
fin, fout = fire(b, cur, True, 2400, Y - 300); chain_in(b, (ba, 'then'), fin)
nx = b.set('Idx', INT, b.i2('Add_IntInt', g('Idx', INT, 3500, Y - 100), None, 3700, Y - 100, db='1'), 3700, Y - 300); chain_in(b, fout, (nx, 'execute'))
t0 = b.set('T', DBL, None, 3950, Y - 300); G.link(nx, 'then', t0, 'execute')
# home: walk back, leave there (or after 40 s)
mh = b.lib(CLS('AIBlueprintHelperLibrary'), 'SimpleMoveToLocation', [ob('Controller', CTRL), V('Goal')], 1450, Y + 1300, tag='GoHome')
b.wire((b.call_self('GetController', [ob('ReturnValue', CTRL, out=True)], 1300, Y + 1500, PAWN, pure=True, const=True, tag='Ctrl2'), 'ReturnValue'), mh, 'Controller')
b.wire(g('Home', VECT, 1300, Y + 1600), mh, 'Goal'); G.link(bm, 'else', mh, 'execute')
dh = b.math('Vector_Distance2D', [(V('V1'), g('Home', VECT, 1600, Y + 1600)), (V('V2'), b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1600, Y + 1700, pure=True, const=True, tag='MyLoc3') and ('tbMyLoc3%d' % b.n, 'ReturnValue'))],
            D('ReturnValue', out=True), 1800, Y + 1650)
gone = b.b2('BooleanOR', b.dcmp('Less_DoubleDouble', dh, None, 2000, Y + 1650, db='150.0'), b.dcmp('Greater_DoubleDouble', g('T', DBL, 1850, Y + 1800), None, 2000, Y + 1800, db='40.0'), 2200, Y + 1700)
bg = b.branch(gone, 1750, Y + 1300, tag='IfHome'); G.link(mh, 'then', bg, 'execute')
G.link(bg, 'then', b.call_self('K2_DestroyActor', [], 2000, Y + 1300, ACT), 'execute')
check_write(G, 'BP_TorchBearer_graph.txt')
TBV = [('List', ACTT + ',ContainerType=Array', ''), ('Idx', 'PinCategory="int"', '0'), ('T', 'PinCategory="real",PinSubCategory="double"', '0.0'),
       ('Home', 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Vector\'"', '0, 0, 0'),
       ('Wx', 'PinCategory="object",PinSubCategoryObject="%s"' % WXC.strip('"'), ''), ('DN', 'PinCategory="object",PinSubCategoryObject="%s"' % DNC.strip('"'), '')]
open(os.path.join(HERE, 'VARIABLES_TorchBearer_BPVar.txt'), 'w', newline='\r\n').write(
    '# #355 BP_TorchBearer - paste one line at a time on the VARIABLES header, then Compile\n' + '\n'.join(bpv(n, t, d, 'torch355/tb/') for n, t, d in TBV) + '\n')
