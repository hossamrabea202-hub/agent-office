# #297 Cave door (adjustedfilm, 2026-10-31; owner W:): an inner door in the cave, [E] takes the hero down to the mine
# dungeon (TGA's #309 kit, an always-loaded sub-level far under the map), and a second door there brings him back up.
#   "<blender python>" -I gen_cavedoor297.py -> BP_CaveDoor_graph.txt, VARIABLES_BPVar.txt, VARIABLES.md
# BP_CaveDoor (one class, placed twice; each instance's Target = the other door):
#   BeginPlay  - starts DoorPoll every 0.05 s (a timer by name: no self-call nodes, they don't paste, see #254).
#   DoorPoll   - hero within UseRange (2.2 m): the door's Prompt shows once per visit through BP_NoticeHUD.PushNotice.
#                E pressed (edge-detected, so holding E can't bounce you back) and not Busy and Target set: Busy, the camera
#                fades to black (0.35 s, audio fades too), DoTeleport in 0.4 s.
#   DoTeleport - the hero goes to Target + Target's forward x ExitDist (1.5 m) + 30 cm up, facing away from that door
#                (the camera turns with him), the camera fades back in (0.5 s), Busy off.
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE

P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
NOTC = BPC(P_NOTICE, 'BP_NoticeHUD')
HUDCLS, PCM = CLS('HUD'), CLS('PlayerCameraManager')
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
OBJV = lambda c: ob('v', c)


class B(bpkit.B):
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def pc(s, x, y):
        return (s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC'), 'ReturnValue')
    def hero(s, x, y):
        return (s.lib(GS, 'GetPlayerCharacter', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CHARC, out=True)], x, y, pure=True, tag='Hero'), 'ReturnValue')
    def cam(s, x, y):
        return (s.lib(GS, 'GetPlayerCameraManager', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCM, out=True)], x, y, pure=True, tag='Cam'), 'ReturnValue')
    def loc(s, actor, x, y):
        return (s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'), 'ReturnValue')
    def myloc(s, x, y):
        return (s.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='MyLoc'), 'ReturnValue')
    def fade(s, a0, a1, dur, hold, x, y):
        n = s.call(PCM, 'StartCameraFade', [fl('FromAlpha', default=a0), fl('ToAlpha', default=a1), fl('Duration', default=dur),
                   st('Color', LC, default='(R=0.000000,G=0.000000,B=0.000000,A=1.000000)'), bo('bShouldFadeAudio', default='true'),
                   bo('bHoldWhenFinished', default=hold)], x, y, target=s.cam(x - 200, y + 300), tag='Fade')
        return n
    def timer_ev(s, fn, interval, loop, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default=loop),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n


G = Graph(); b = B(G, 'cd')
g = b.get
G.node('cdBeginPlay', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT}, ex('then', True)], 0, 0)
G.link('cdBeginPlay', 'then', b.timer_ev('DoorPoll', '0.05', 'true', 300, 0), 'execute')

# ---------------------------------------------------------------- DoorPoll
Y = 600
b.event('DoorPoll', [], 0, Y)
hero = b.hero(0, Y + 300)
near = b.b2('BooleanAND', b.valid(hero, 200, Y + 300),
            b.dcmp('Less_DoubleDouble', b.math('Vector_Distance', [(V('V1'), b.loc(hero, 200, Y + 450)), (V('V2'), b.myloc(200, Y + 600))], D('ReturnValue', out=True), 400, Y + 500),
                   g('UseRange', DBL, 400, Y + 650), 600, Y + 550), 800, Y + 400)
down = b.call(PCON, 'IsInputKeyDown', [st('Key', KEY, default='E'), bo('ReturnValue', out=True, default='false')], 400, Y + 800, target=b.pc(200, Y + 800), pure=True, const=True, tag='KeyE')
press = b.b2('BooleanAND',
             b.b2('BooleanAND', (down, 'ReturnValue'), b.bnot(g('EWas', BOOL, 600, Y + 900), 800, Y + 900), 1000, Y + 850),
             b.b2('BooleanAND', b.b2('BooleanAND', near, b.bnot(g('Busy', BOOL, 800, Y + 1050), 1000, Y + 1050), 1200, Y + 1000),
                  b.valid(g('Target', OBJV(ACT), 1000, Y + 1150), 1200, Y + 1150), 1400, Y + 1100), 1600, Y + 950)
# the press is computed before EWas is overwritten (pure nodes are evaluated when the branch reads them, so latch it first)
sp = b.set('PressNow', BOOL, press, 300, Y); G.link('DoorPoll', 'then', sp, 'execute')
se = b.set('EWas', BOOL, (down, 'ReturnValue'), 600, Y); G.link(sp, 'then', se, 'execute')
# prompt once per visit
first = b.b2('BooleanAND', near, b.bnot(g('Shown', BOOL, 1000, Y - 300), 1200, Y - 300), 1400, Y - 250)
bf = b.branch(first, 900, Y, tag='IfPrompt'); G.link(se, 'then', bf, 'execute')
hud = b.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], 1100, Y - 450, target=b.pc(900, Y - 450), pure=True, const=True, tag='HUD')
cast(G, 'cdAsNotice', NOTC, 'AsBP Notice HUD', 1200, Y - 200); b.wire((hud, 'ReturnValue'), 'cdAsNotice', 'Object'); G.link(bf, 'then', 'cdAsNotice', 'execute')
pn = b.call(NOTC, 'PushNotice', [S('Text'), it('Tier', default='0')], 1500, Y - 200, target=('cdAsNotice', 'AsBP Notice HUD'), tag='Notice')
b.wire(g('Prompt', S('v'), 1300, Y - 350), pn, 'Text'); G.link('cdAsNotice', 'then', pn, 'execute')
ssh = b.set('Shown', BOOL, near, 1800, Y)
for src, pin in ((bf, 'else'), (pn, 'then'), ('cdAsNotice', 'CastFailed')): G.link(src, pin, ssh, 'execute')
# E: fade out, teleport in 0.4 s
bp_ = b.branch(g('PressNow', BOOL, 1900, Y + 300), 2100, Y, tag='IfGo'); G.link(ssh, 'then', bp_, 'execute')
sb = b.set('Busy', bo('v', default='true'), None, 2400, Y); G.link(bp_, 'then', sb, 'execute')
f1 = b.fade('0.0', '1.0', '0.35', 'true', 2700, Y); G.link(sb, 'then', f1, 'execute')
G.link(f1, 'then', b.timer_ev('DoTeleport', '0.4', 'false', 3000, Y), 'execute')

# ---------------------------------------------------------------- DoTeleport
Y = 2600
b.event('DoTeleport', [], 0, Y)
tgt = lambda x, y: g('Target', OBJV(ACT), x, y)
hero2 = b.hero(0, Y + 300)
fwd = b.call(ACT, 'GetActorForwardVector', [V('ReturnValue', out=True)], 400, Y + 500, target=tgt(200, Y + 500), pure=True, const=True, tag='TFwd')
off = b.math('Multiply_VectorFloat', [(V('A'), (fwd, 'ReturnValue')), (D('B', default='0.0'), g('ExitDist', DBL, 400, Y + 650))], V('ReturnValue', out=True), 600, Y + 550)
dest = b.v2('Add_VectorVector', b.v2('Add_VectorVector', b.loc(tgt(400, Y + 350), 600, Y + 350), off, 800, Y + 450), None, 1000, Y + 450, db='0, 0, 30.000000')
trot = b.call(ACT, 'K2_GetActorRotation', [st('ReturnValue', ROT, out=True)], 600, Y + 800, target=tgt(400, Y + 800), pure=True, const=True, tag='TRot')
br_ = b.name('BreakRot'); mathfn(G, br_, 'BreakRotator', [st('InRot', ROT, default='0, 0, 0'), fl('Roll', out=True, default='0.0'), fl('Pitch', out=True, default='0.0'),
                                                          fl('Yaw', out=True, default='0.0')], 800, Y + 800)
G.link(trot, 'ReturnValue', br_, 'InRot')
yaw = b.math('MakeRotator', [(fl('Roll', default='0.0'), None), (fl('Pitch', default='0.0'), None), (fl('Yaw', default='0.0'), (br_, 'Yaw'))], st('ReturnValue', ROT, out=True), 1000, Y + 800)
ifv = b.branch(b.b2('BooleanAND', b.valid(hero2, 200, Y + 200), b.valid(tgt(0, Y + 150), 200, Y + 150), 400, Y + 200), 300, Y, tag='IfOk'); G.link('DoTeleport', 'then', ifv, 'execute')
tp = b.call(ACT, 'K2_TeleportTo', [V('DestLocation'), st('DestRotation', ROT, default='0, 0, 0'), bo('ReturnValue', out=True, default='false')], 1200, Y, target=hero2, tag='Teleport')
b.wire(dest, tp, 'DestLocation'); b.wire(yaw, tp, 'DestRotation'); G.link(ifv, 'then', tp, 'execute')
cr = b.call(CTRL, 'SetControlRotation', [st('NewRotation', ROT, default='0, 0, 0')], 1500, Y, target=b.pc(1300, Y + 300), tag='CamYaw')
b.wire(yaw, cr, 'NewRotation'); G.link(tp, 'then', cr, 'execute')
f2 = b.fade('1.0', '0.0', '0.5', 'false', 1800, Y); G.link(cr, 'then', f2, 'execute'); G.link(ifv, 'else', f2, 'execute')
sb2 = b.set('Busy', bo('v', default='false'), None, 2100, Y); G.link(f2, 'then', sb2, 'execute')

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
names = [n[0] for n in G.nodes]
if bad or len(names) != len(set(names)): raise SystemExit('bad links %s / dup names' % bad[:10])
open(os.path.join(HERE, 'BP_CaveDoor_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BP_CaveDoor_graph.txt: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ---------------------------------------------------------------- BPVar lines
VARS = [('Target', 'obj:Actor', '', 'INSTANCE: the other BP_CaveDoor (cave door -> dungeon door and back)'),
        ('Prompt', 'string', '[E] Go down into the mine', 'INSTANCE: shown when the hero comes near (dungeon door: "[E] Climb back up to the cave")'),
        ('UseRange', 'real', '220.0', 'cm: how near the hero must be'),
        ('ExitDist', 'real', '150.0', 'cm: where the hero lands in front of the Target door'),
        ('Busy', 'bool', 'false', 'scratch: a teleport is running'), ('EWas', 'bool', 'false', 'scratch: E held last poll'),
        ('Shown', 'bool', 'false', 'scratch: prompt shown this visit'), ('PressNow', 'bool', 'false', 'scratch: E pressed this poll')]
def vt(kind):
    if kind == 'real': return 'PinCategory="real",PinSubCategory="double"'
    if kind in ('bool', 'string'): return 'PinCategory="%s"' % kind
    if kind.startswith('obj:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % kind[4:]
    raise ValueError(kind)
bpv = lambda n, k, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'cavedoor297/%s' % n).hex.upper(), vt(k), n, d)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# #297 BP_CaveDoor - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' + '\n'.join(bpv(*v[:3]) for v in VARS) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #297 BP_CaveDoor variables (BPVar lines in VARIABLES_BPVar.txt)\n\n| Name | Default | Meaning |\n|---|---|---|\n')
    for n, _k, d, m in VARS: f.write('| %s | %s | %s |\n' % (n, d or '-', m))
print('BPVar lines: %d' % len(VARS))
