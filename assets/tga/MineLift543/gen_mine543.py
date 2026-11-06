# #543 Blueprint logic (TGA PC, 2026-11-06), the same paste method as BP_CaveDoor (#297): bpkit + the Master's node kit.
#   "<blender python>" -I gen_mine543.py  ->  BP_MineLift_graph.txt, BP_MineFind_graph.txt, VARIABLES_*_BPVar.txt, VARIABLES.md
# BP_MineLift is ONE class placed twice (MineLift_Top in the winding room, MineLift_Bottom in the dungeon landing),
# Partner = the other one; the top one also has Gate = MineGate_Up (the door at the hut). All motion runs on Tick through
# Phase (no self-calls, the #254 lesson):
#   0 idle      top: hero near the Gate + E -> 1.  bottom: hero near the bucket + E -> blink -> 2
#   1 door      the gate door swings open 100 deg (0.8 s, eased), then a 0.25 s fade to black -> 2
#   2 board     (black) hero: movement off, collision off, attached to Bucket socket Stand, view = this lift's RideCam,
#               fade in 0.4 s; top -> 3, bottom -> 6
#   3 down top  bucket -104 -> -950 cm (DTop 4.5 s, ease in), rope + drum follow; then THE SWAP: the hero and the view jump to
#               the Partner's bucket at +1020, where the 1.3 m cribbing frames line up, Partner -> 4  (this is the hidden load)
#   4 down bot  +1020 -> 0 (DBottom 5.4 s, ease out: same speed as phase 3 ended with) -> 5
#   5 arrive    detach, stand at Exit, movement + collision on, view back to the hero (0.5 s blend), notice -> 0
#   6 up bot    0 -> +1020 (ease in), then the swap up: the Partner's bucket at -950, Partner -> 7
#   7 up top    -950 -> -104 (ease out), fade to black -> 8
#   8 out       (black) hero placed at the Gate's Exit outside the hut door, door shut, fade in, notice -> 0
# BP_MineFind: hero near (Reach 2.2 m) -> "[E] Take the sword" once per visit; E -> the sword, beam and sparks go, the
# info card shows, notice "You found the Ulfberht sword"; the card hides again when the hero walks 6 m away.
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'ref', 'bpgen')); sys.path.insert(0, os.path.join(HERE, 'ref', 't81'))
import kit
sys.modules.setdefault('kit', kit)
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

GP = '/Game/CastleDefender/Gameplay/Mine543'
P_LIFT, P_GATE, P_FIND = GP + '/BP_MineLift', GP + '/BP_MineGateDoor', GP + '/BP_MineFind'
LIFTC, GATEC = BPC(P_LIFT, 'BP_MineLift'), BPC(P_GATE, 'BP_MineGateDoor')
P_NOTICE = '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD'
NOTC = BPC(P_NOTICE, 'BP_NoticeHUD')
HUDCLS, PCM, SMC, ARROW, CAC = CLS('HUD'), CLS('PlayerCameraManager'), CLS('StaticMeshComponent'), CLS('ArrowComponent'), CLS('ChildActorComponent')
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
HITRES = '"/Script/CoreUObject.ScriptStruct\'/Script/Engine.HitResult\'"'
def EN(name, enum, default): return {'name': name, 'cat': 'byte', 'obj': ENUM(enum), 'default': default}
OBJV = lambda c: ob('v', c)


class Bx(bpkit.B):
    def pc(s, x, y): return (s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC'), 'ReturnValue')
    def hero(s, x, y): return (s.lib(GS, 'GetPlayerCharacter', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CHARC, out=True)], x, y, pure=True, tag='Hero'), 'ReturnValue')
    def cam(s, x, y): return (s.lib(GS, 'GetPlayerCameraManager', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCM, out=True)], x, y, pure=True, tag='Cam'), 'ReturnValue')
    def aloc(s, actor, x, y): return (s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'), 'ReturnValue')
    def cloc(s, comp, x, y): return (s.call(SCENE, 'K2_GetComponentLocation', [V('ReturnValue', out=True)], x, y, target=comp, pure=True, const=True, tag='CLoc'), 'ReturnValue')
    def crot(s, comp, x, y): return (s.call(SCENE, 'K2_GetComponentRotation', [st('ReturnValue', ROT, out=True)], x, y, target=comp, pure=True, const=True, tag='CRot'), 'ReturnValue')
    def myloc(s, x, y): return (s.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='MyLoc'), 'ReturnValue')
    def dist(s, a, b_, x, y): return s.math('Vector_Distance', [(V('V1'), a), (V('V2'), b_)], D('ReturnValue', out=True), x, y)
    def fade(s, a0, a1, dur, hold, x, y):
        return s.call(PCM, 'StartCameraFade', [fl('FromAlpha', default=a0), fl('ToAlpha', default=a1), fl('Duration', default=dur),
                      st('Color', LC, default='(R=0.000000,G=0.000000,B=0.000000,A=1.000000)'), bo('bShouldFadeAudio', default='false'),
                      bo('bHoldWhenFinished', default=hold)], x, y, target=s.cam(x - 200, y + 300), tag='Fade')
    def ease(s, a, b_, alpha, func, x, y):
        return s.math('Ease', [(D('A', default=a), None), (D('B', default=b_), None), (D('Alpha', default='0.0'), alpha), (EN('EasingFunc', 'EEasingFunc', func), None),
                               (D('BlendExp', default='2.0'), None), (it('Steps', default='2'), None)], D('ReturnValue', out=True), x, y)
    def setrel(s, comp, loc, x, y):
        n = s.call(SCENE, 'K2_SetRelativeLocation', [V('NewLocation'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')], x, y, target=comp, tag='SetRelLoc')
        s.wire(loc, n, 'NewLocation'); return n
    def setrot(s, comp, rot, x, y):
        n = s.call(SCENE, 'K2_SetRelativeRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')], x, y, target=comp, tag='SetRelRot')
        s.wire(rot, n, 'NewRotation'); return n
    def setscale(s, comp, sc, x, y):
        n = s.call(SCENE, 'SetRelativeScale3D', [V('NewScale3D', default='1, 1, 1')], x, y, target=comp, tag='SetScale'); s.wire(sc, n, 'NewScale3D'); return n
    def rot(s, roll, pitch, yaw, x, y):
        return s.math('MakeRotator', [(fl('Roll', default='0.0'), roll), (fl('Pitch', default='0.0'), pitch), (fl('Yaw', default='0.0'), yaw)], st('ReturnValue', ROT, out=True), x, y)
    def set_i(s, var, val, x, y): return s.set(var, it('v', default=str(val)), None, x, y)
    def set_d(s, var, val, x, y): return s.set(var, D('v', default=val), None, x, y)
    def set_b(s, var, val, x, y): return s.set(var, bo('v', default=val), None, x, y)
    def notice(s, text_src, x, y, default=''):
        """PushNotice on BP_NoticeHUD (cast on the exec chain); returns (first, last) exec nodes."""
        hud = s.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x, y - 250, target=s.pc(x - 200, y - 250), pure=True, const=True, tag='HUD')
        c = s.name('AsNotice'); cast(s.G, c, NOTC, 'AsBP Notice HUD', x, y); s.wire((hud, 'ReturnValue'), c, 'Object')
        pn = s.call(NOTC, 'PushNotice', [S('Text', default=default), it('Tier', default='0')], x + 300, y, target=(c, 'AsBP Notice HUD'), tag='Notice')
        s.wire(text_src, pn, 'Text'); s.G.link(c, 'then', pn, 'execute')
        j = s.seq(s.name('Join'), 1, x + 600, y); s.G.link(pn, 'then', j, 'execute'); s.G.link(c, 'CastFailed', j, 'execute')
        return c, (j, 'then_0')


def ex_chain(G, nodes):
    for a, b_ in zip(nodes, nodes[1:]):
        an, ap = a if isinstance(a, tuple) else (a, 'then'); bn, bp = b_ if isinstance(b_, tuple) else (b_, 'execute')
        G.link(an, ap, bn, bp)


# ===================================================================================================================== BP_MineLift
G = Graph(); b = Bx(G, 'ml'); g = b.get
TICK = 'mlTick'
G.node(TICK, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveTick")' % ACT, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveTick")' % ACT}, ex('then', True),
        fl('DeltaSeconds', out=True, default='0.0')], 0, 0)
st_ = b.set('T', DBL, b.d2('Add_DoubleDouble', g('T', DBL, 0, 200), (TICK, 'DeltaSeconds'), 200, 200), 300, 0); G.link(TICK, 'then', st_, 'execute')
SEQ = b.seq('mlPhases', 9, 600, 0); G.link(st_, 'then', SEQ, 'execute')
def phase_branch(k, x, y):
    br = b.branch(b.icmp('EqualEqual_IntInt', g('Phase', INT, x - 400, y + 150), None, x - 200, y + 150, db=str(k)), x, y, tag='IfPhase%d' % k)
    G.link(SEQ, 'then_%d' % k, br, 'execute'); return br
def alpha(dur_var, x, y):          # clamp(T / dur, 0, 1)
    return b.clamp(b.d2('Divide_DoubleDouble', g('T', DBL, x - 400, y), g(dur_var, DBL, x - 400, y + 80), x - 200, y), '0.0', '1.0', x, y)
def bucket(x, y): return g('Bucket', OBJV(SMC), x, y)
def place_bucket(z, x, y, target_lift=None):
    """bucket z (cm) + rope length (RopeTop - (z + 183)) + drum turn ((z + 104) / 20 rad). target_lift: the Partner cast handle."""
    get = (lambda v, pin, xx, yy: b.getm(v, LIFTC, pin, target_lift, xx, yy)) if target_lift else (lambda v, pin, xx, yy: g(v, pin, xx, yy))
    zc = z if isinstance(z, str) else '0.0'; z = None if isinstance(z, str) else z          # a constant (str) or a live value
    n1 = b.setrel(get('Bucket', OBJV(SMC), x, y + 300), b.vec(None, None, z, x - 200, y + 150, dz=zc), x, y)
    ln = b.d2('Divide_DoubleDouble', b.d2('Subtract_DoubleDouble', get('RopeTop', DBL, x + 100, y + 500), b.d2('Add_DoubleDouble', z, None, x + 100, y + 600, da=zc, db='183.0'), x + 250, y + 520), None, x + 400, y + 520, db='100.0')
    n2 = b.setscale(get('Rope', OBJV(SMC), x + 300, y + 350), b.vec(None, None, ln, x + 550, y + 450, dx='1.0', dy='1.0'), x + 350, y)
    pitch = b.d2('Multiply_DoubleDouble', b.d2('Add_DoubleDouble', z, None, x + 600, y + 650, da=zc, db='104.0'), None, x + 750, y + 650, db='2.864789')  # /20 cm * 57.3
    n3 = b.setrot(get('Drum', OBJV(SMC), x + 650, y + 350), b.rot(None, pitch, None, x + 900, y + 600), x + 700, y)
    ex_chain(G, [n1, n2, n3]); return n1, n3
def board(x, y, target_lift=None):
    """hero onto a bucket (self or the Partner): movement + collision off, attach to socket Stand, view = that lift."""
    hero = b.hero(x - 200, y + 300)
    cm = b.getm('CharacterMovement', CHARC, OBJV(CMC), hero, x, y + 300)
    n1 = b.call(CMC, 'DisableMovement', [], x, y, target=cm, tag='NoMove')
    n2 = b.call(ACT, 'SetActorEnableCollision', [bo('bNewActorEnableCollision', default='false')], x + 300, y, target=hero, tag='NoColl')
    bk = b.getm('Bucket', LIFTC, OBJV(SMC), target_lift, x + 400, y + 350) if target_lift else bucket(x + 400, y + 350)
    n3 = b.call(ACT, 'K2_AttachToComponent', [ob('Parent', SCENE), N('SocketName', default='Stand'), EN('LocationRule', 'EAttachmentRule', 'SnapToTarget'),
                EN('RotationRule', 'EAttachmentRule', 'SnapToTarget'), EN('ScaleRule', 'EAttachmentRule', 'KeepWorld'), bo('bWeldSimulatedBodies', default='false'),
                bo('ReturnValue', out=True, default='false')], x + 600, y, target=hero, tag='Attach')
    b.wire(bk, n3, 'Parent')
    view = target_lift if target_lift else b.self_node(x + 800, y + 350)
    n4 = b.call(PCON, 'SetViewTargetWithBlend', [ob('NewViewTarget', ACT), fl('BlendTime', default='0.0'), EN('BlendFunc', 'EViewTargetBlendFunction', 'VTBlend_Linear'),
                fl('BlendExp', default='0.0'), bo('bLockOutgoing', default='false')], x + 900, y, target=b.pc(x + 700, y + 450), tag='View')
    b.wire(view, n4, 'NewViewTarget')
    ex_chain(G, [n1, n2, n3, n4]); return n1, n4
def leave(exit_comp, x, y):
    """hero off the bucket: detach, stand at the Exit arrow facing along it, movement + collision on, view back."""
    hero = b.hero(x - 200, y + 300)
    n1 = b.call(ACT, 'K2_DetachFromActor', [EN('LocationRule', 'EDetachmentRule', 'KeepWorld'), EN('RotationRule', 'EDetachmentRule', 'KeepWorld'),
                EN('ScaleRule', 'EDetachmentRule', 'KeepWorld')], x, y, target=hero, tag='Detach')
    r = b.crot(exit_comp, x + 100, y + 500); br_ = b.name('BreakRot')
    mathfn(G, br_, 'BreakRotator', [st('InRot', ROT, default='0, 0, 0'), fl('Roll', out=True, default='0.0'), fl('Pitch', out=True, default='0.0'), fl('Yaw', out=True, default='0.0')], x + 300, y + 500)
    G.link(r[0], r[1], br_, 'InRot'); yaw = b.rot(None, None, (br_, 'Yaw'), x + 500, y + 500)
    dest = b.v2('Add_VectorVector', b.cloc(exit_comp, x + 300, y + 400), None, x + 500, y + 400, db='0, 0, 60.000000')
    n2 = b.call(ACT, 'K2_TeleportTo', [V('DestLocation'), st('DestRotation', ROT, default='0, 0, 0'), bo('ReturnValue', out=True, default='false')], x + 300, y, target=hero, tag='Teleport')
    b.wire(dest, n2, 'DestLocation'); b.wire(yaw, n2, 'DestRotation')
    n3 = b.call(ACT, 'SetActorEnableCollision', [bo('bNewActorEnableCollision', default='true')], x + 600, y, target=hero, tag='Coll')
    cm = b.getm('CharacterMovement', CHARC, OBJV(CMC), hero, x + 700, y + 300)
    n4 = b.call(CMC, 'SetMovementMode', [EN('NewMovementMode', 'EMovementMode', 'MOVE_Walking'), {'name': 'NewCustomMode', 'cat': 'byte', 'default': '0'}], x + 900, y, target=cm, tag='Walk')
    n5 = b.call(CTRL, 'SetControlRotation', [st('NewRotation', ROT, default='0, 0, 0')], x + 1200, y, target=b.pc(x + 1000, y + 300), tag='CamYaw'); b.wire(yaw, n5, 'NewRotation')
    n6 = b.call(PCON, 'SetViewTargetWithBlend', [ob('NewViewTarget', ACT), fl('BlendTime', default='0.5'), EN('BlendFunc', 'EViewTargetBlendFunction', 'VTBlend_EaseInOut'),
                fl('BlendExp', default='2.0'), bo('bLockOutgoing', default='false')], x + 1500, y, target=b.pc(x + 1300, y + 450), tag='ViewBack')
    b.wire(b.hero(x + 1300, y + 350), n6, 'NewViewTarget')
    ex_chain(G, [n1, n2, n3, n4, n5, n6]); return n1, n6
def swap(z_partner, partner_phase, z_reset, x, y):
    """THE hidden load: Partner's bucket to z_partner, hero + view onto it, Partner takes over at partner_phase; this lift resets."""
    c = b.name('AsLift'); cast(G, c, LIFTC, 'AsBP Mine Lift', x, y); b.wire(g('Partner', OBJV(ACT), x - 200, y + 200), c, 'Object')
    pl = (c, 'AsBP Mine Lift')
    p1, p3 = place_bucket(z_partner, x + 300, y, target_lift=pl)
    bo1, bo4 = board(x + 1400, y, target_lift=pl)
    s1 = b.setm('Phase', LIFTC, it('v', default=str(partner_phase)), None, pl, x + 2600, y)
    s2 = b.setm('T', LIFTC, D('v', default='0.0'), None, pl, x + 2900, y)
    s3 = b.set_i('Phase', 0, x + 3200, y)
    r1, r3 = place_bucket(z_reset, x + 3500, y)
    ex_chain(G, [(c, 'then'), p1]); ex_chain(G, [p3, bo1]); ex_chain(G, [bo4, s1, s2, s3, r1])
    return c, r3

# ---- phase 0: idle, prompt + E ----
Y = 600; br0 = phase_branch(0, 1000, Y)
hero0 = b.hero(1000, Y + 400)
dg = b.dist(b.aloc(hero0, 1200, Y + 400), b.aloc(g('Gate', OBJV(ACT), 1100, Y + 500), 1250, Y + 500), 1450, Y + 450)
db_ = b.dist(b.aloc(hero0, 1200, Y + 650), b.cloc(bucket(1100, Y + 750), 1250, Y + 750), 1450, Y + 700)
d = b.self_(dg, db_, g('IsTop', BOOL, 1450, Y + 850), 1650, Y + 600)
near = b.b2('BooleanAND', b.dcmp('Less_DoubleDouble', d, g('UseRange', DBL, 1650, Y + 750), 1850, Y + 650), b.valid(g('Partner', OBJV(ACT), 1650, Y + 900), 1850, Y + 900), 2050, Y + 700)
down = b.call(PCON, 'IsInputKeyDown', [st('Key', KEY, default='E'), bo('ReturnValue', out=True, default='false')], 1650, Y + 1050, target=b.pc(1450, Y + 1050), pure=True, const=True, tag='KeyE')
press = b.b2('BooleanAND', b.b2('BooleanAND', (down, 'ReturnValue'), b.bnot(g('EWas', BOOL, 1850, Y + 1150), 2050, Y + 1150), 2250, Y + 1100), near, 2450, Y + 900)
sp = b.set('PressNow', BOOL, press, 1300, Y); se = b.set('EWas', BOOL, (down, 'ReturnValue'), 1600, Y); ex_chain(G, [(br0, 'then'), sp, se])
first = b.b2('BooleanAND', near, b.bnot(g('Shown', BOOL, 2000, Y - 300), 2200, Y - 300), 2400, Y - 250)
bf = b.branch(first, 1900, Y, tag='IfPrompt'); G.link(se, 'then', bf, 'execute')
nc, nend = b.notice(b.selstr(g('PromptTop', STR, 2100, Y - 600), g('PromptBottom', STR, 2100, Y - 500), g('IsTop', BOOL, 2100, Y - 400), 2300, Y - 500), 2200, Y - 150)
G.link(bf, 'then', nc, 'execute')
ssh = b.set('Shown', BOOL, near, 3200, Y); G.link(bf, 'else', ssh, 'execute'); G.link(nend[0], nend[1], ssh, 'execute')
bgo = b.branch(g('PressNow', BOOL, 3300, Y + 300), 3500, Y, tag='IfGo'); G.link(ssh, 'then', bgo, 'execute')
st0 = b.set_d('T', '0.0', 3800, Y); G.link(bgo, 'then', st0, 'execute')
btop = b.branch(g('IsTop', BOOL, 3900, Y + 300), 4100, Y, tag='IfTop'); G.link(st0, 'then', btop, 'execute')
G.link(btop, 'then', b.set_i('Phase', 1, 4400, Y - 100), 'execute')
f0 = b.fade('0.0', '1.0', '0.25', 'true', 4400, Y + 200); G.link(btop, 'else', f0, 'execute'); G.link(f0, 'then', b.set_i('Phase', 2, 4700, Y + 200), 'execute')

# ---- phase 1: the gate door swings open (top) ----
Y = 2200; br1 = phase_branch(1, 1000, Y)
cg = b.name('AsGate'); cast(G, cg, GATEC, 'AsBP Mine Gate Door', 1300, Y); b.wire(g('Gate', OBJV(ACT), 1100, Y + 200), cg, 'Object'); G.link(br1, 'then', cg, 'execute')
a1 = alpha('DDoor', 1500, Y + 500)
yaw = b.d2('Multiply_DoubleDouble', b.ease('0.0', '1.0', a1, 'EaseInOut', 1700, Y + 500), None, 1900, Y + 500, db='-100.0')
sr = b.setrot(b.getm('Door', GATEC, OBJV(SMC), (cg, 'AsBP Mine Gate Door'), 1700, Y + 300), b.rot(None, None, yaw, 2100, Y + 450), 1700, Y); G.link(cg, 'then', sr, 'execute')
bd = b.branch(b.dcmp('GreaterEqual_DoubleDouble', a1, None, 2100, Y + 250, db='1.0'), 2000, Y, tag='IfOpen'); G.link(sr, 'then', bd, 'execute')
f1 = b.fade('0.0', '1.0', '0.25', 'true', 2300, Y); G.link(bd, 'then', f1, 'execute')
t1 = b.set_d('T', '0.0', 2600, Y); s1 = b.set_i('Phase', 2, 2900, Y); ex_chain(G, [f1, t1, s1])

# ---- phase 2: board (black) ----
Y = 3400; br2 = phase_branch(2, 1000, Y)
bb = b.branch(b.dcmp('GreaterEqual_DoubleDouble', g('T', DBL, 1100, Y + 200), None, 1300, Y + 200, db='0.3'), 1300, Y, tag='IfBlack'); G.link(br2, 'then', bb, 'execute')
o1, o4 = board(1700, Y); G.link(bb, 'then', o1, 'execute')
f2 = b.fade('1.0', '0.0', '0.4', 'false', 2900, Y); G.link(o4, 'then', f2, 'execute')
t2 = b.set_d('T', '0.0', 3200, Y); G.link(f2, 'then', t2, 'execute')
nx = b.math('SelectInt', [(it('A', default='3'), None), (it('B', default='6'), None), (bo('bPickA', default='false'), g('IsTop', BOOL, 3300, Y + 300))], it('ReturnValue', out=True), 3500, Y + 250)
s2 = b.set('Phase', INT, nx, 3500, Y); G.link(t2, 'then', s2, 'execute')

# ---- phases 3 / 4 / 6 / 7: the four legs of the ride ----
def leg(k, y, dur, z0, z1, func, swap_to=None, done=None):
    br = phase_branch(k, 1000, y)
    a = alpha(dur, 1200, y + 700); z = b.ease(z0, z1, a, func, 1400, y + 700)
    n1, n3 = place_bucket(z, 1500, y); G.link(br, 'then', n1, 'execute')
    bend = b.branch(b.dcmp('GreaterEqual_DoubleDouble', a, None, 2700, y + 250, db='1.0'), 2700, y, tag='IfEnd%d' % k); G.link(n3, 'then', bend, 'execute')
    if swap_to:
        zp, ph, zr = swap_to
        c, last = swap(zp, ph, zr, 3000, y); G.link(bend, 'then', c, 'execute')
    else:
        done(bend)
Y = 4600
leg(3, Y, 'DTop', '-104.0', '-950.0', 'EaseIn', swap_to=('1020.0', 4, '-104.0'))
leg(4, Y + 1400, 'DBottom', '1020.0', '0.0', 'EaseOut', done=lambda bend: G.link(bend, 'then', b.set_i('Phase', 5, 3000, Y + 1400), 'execute') or None)
# phase 5: arrive at the bottom
Y5 = Y + 2800; br5 = phase_branch(5, 1000, Y5)
l1, l6 = leave(g('Exit', OBJV(ARROW), 1100, Y5 + 600), 1400, Y5); G.link(br5, 'then', l1, 'execute')
nc5, ne5 = b.notice(g('ArriveText', STR, 3000, Y5 - 400), 3200, Y5)
G.link(l6, 'then', nc5, 'execute'); z5 = b.set_i('Phase', 0, 4200, Y5); G.link(ne5[0], ne5[1], z5, 'execute')
G.link(z5, 'then', b.set_b('EWas', 'true', 4500, Y5), 'execute')
leg(6, Y + 4200, 'DBottom', '0.0', '1020.0', 'EaseIn', swap_to=('-950.0', 7, '0.0'))
def end7(bend):
    f = b.fade('0.0', '1.0', '0.25', 'true', 3000, Y + 5600); G.link(bend, 'then', f, 'execute')
    t = b.set_d('T', '0.0', 3300, Y + 5600); s = b.set_i('Phase', 8, 3600, Y + 5600); ex_chain(G, [f, t, s])
leg(7, Y + 5600, 'DTop', '-950.0', '-104.0', 'EaseOut', done=end7)
# phase 8: out at the hut door (black), door shut, fade in
Y8 = Y + 7000; br8 = phase_branch(8, 1000, Y8)
b8 = b.branch(b.dcmp('GreaterEqual_DoubleDouble', g('T', DBL, 1100, Y8 + 200), None, 1300, Y8 + 200, db='0.3'), 1300, Y8, tag='IfBlack8'); G.link(br8, 'then', b8, 'execute')
cg8 = b.name('AsGate'); cast(G, cg8, GATEC, 'AsBP Mine Gate Door', 1600, Y8); b.wire(g('Gate', OBJV(ACT), 1400, Y8 + 200), cg8, 'Object'); G.link(b8, 'then', cg8, 'execute')
gl = (cg8, 'AsBP Mine Gate Door')
k1, k6 = leave(b.getm('Exit', GATEC, OBJV(ARROW), gl, 1700, Y8 + 600), 2000, Y8); G.link(cg8, 'then', k1, 'execute')
shut = b.setrot(b.getm('Door', GATEC, OBJV(SMC), gl, 3500, Y8 + 300), None, 3600, Y8); G.link(k6, 'then', shut, 'execute')
f8 = b.fade('1.0', '0.0', '0.5', 'false', 3900, Y8); G.link(shut, 'then', f8, 'execute')
nc8, ne8 = b.notice(g('ArriveTextTop', STR, 4100, Y8 - 400), 4200, Y8); G.link(f8, 'then', nc8, 'execute')
z8 = b.set_i('Phase', 0, 5200, Y8); G.link(ne8[0], ne8[1], z8, 'execute'); G.link(z8, 'then', b.set_b('EWas', 'true', 5500, Y8), 'execute')

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
names = [n[0] for n in G.nodes]
if bad or len(names) != len(set(names)): raise SystemExit('BP_MineLift: bad links %s / dup names %s' % (bad[:6], len(names) - len(set(names))))
open(os.path.join(HERE, 'BP_MineLift_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BP_MineLift_graph.txt: nodes %d, links %d' % (len(G.nodes), len(G.links)))
LIFT_GRAPH = G

# ===================================================================================================================== BP_MineFind
G = Graph(); b = Bx(G, 'mf'); g = b.get
BEGIN = 'mfBeginPlay'
G.node(BEGIN, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT}, ex('then', True)], 0, 0)
cv = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='true')], 300, 0, target=g('Card', OBJV(SMC), 100, 200), tag='CardOff')
G.link(BEGIN, 'then', cv, 'execute')
tm = b.timer('Poll', 600, 0, dtime='0.05', loop=True); b.wire(b.self_node(400, 200), tm, 'Object'); G.link(cv, 'then', tm, 'execute')
Y = 600; b.event('Poll', [], 0, Y)
hero = b.hero(0, Y + 300)
dd = b.dist(b.aloc(hero, 200, Y + 300), b.myloc(200, Y + 450), 400, Y + 350)
near = b.b2('BooleanAND', b.dcmp('Less_DoubleDouble', dd, g('UseRange', DBL, 400, Y + 500), 600, Y + 400), b.bnot(g('Taken', BOOL, 400, Y + 600), 600, Y + 600), 800, Y + 450)
down = b.call(PCON, 'IsInputKeyDown', [st('Key', KEY, default='E'), bo('ReturnValue', out=True, default='false')], 600, Y + 750, target=b.pc(400, Y + 750), pure=True, const=True, tag='KeyE')
press = b.b2('BooleanAND', b.b2('BooleanAND', (down, 'ReturnValue'), b.bnot(g('EWas', BOOL, 800, Y + 850), 1000, Y + 850), 1200, Y + 800), near, 1400, Y + 700)
sp = b.set('PressNow', BOOL, press, 300, Y); se = b.set('EWas', BOOL, (down, 'ReturnValue'), 600, Y); ex_chain(G, ['Poll', sp, se])
first = b.b2('BooleanAND', near, b.bnot(g('Shown', BOOL, 1000, Y - 300), 1200, Y - 300), 1400, Y - 250)
bf = b.branch(first, 900, Y, tag='IfPrompt'); G.link(se, 'then', bf, 'execute')
nc, ne = b.notice(g('Prompt', STR, 1100, Y - 500), 1200, Y - 150); G.link(bf, 'then', nc, 'execute')
ssh = b.set('Shown', BOOL, near, 2200, Y); G.link(bf, 'else', ssh, 'execute'); G.link(ne[0], ne[1], ssh, 'execute')
# E: take it
bg = b.branch(g('PressNow', BOOL, 2300, Y + 300), 2500, Y, tag='IfTake'); G.link(ssh, 'then', bg, 'execute')
t1 = b.set_b('Taken', 'true', 2800, Y); G.link(bg, 'then', t1, 'execute')
ga = b.call(CAC, 'GetChildActor', [ob('ReturnValue', ACT, out=True)], 2900, Y + 300, target=g('Sword', OBJV(CAC), 2700, Y + 300), pure=True, const=True, tag='SwordActor')
h1 = b.call(ACT, 'SetActorHiddenInGame', [bo('bNewHidden', default='true')], 3100, Y, target=(ga, 'ReturnValue'), tag='HideSword')
def vis(comp, on, x):
    return b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default=on), bo('bPropagateToChildren', default='true')], x, Y, target=g(comp, OBJV(SMC), x - 200, Y + 300), tag='Vis' + comp)
h2, h3, h4 = vis('Beam', 'false', 3400), vis('Motes', 'false', 3700), vis('Card', 'true', 4000)
nc2, ne2 = b.notice(g('FoundText', STR, 4200, Y - 400), 4300, Y)
ex_chain(G, [t1, h1, h2, h3, h4, nc2]); s_on = b.set_b('CardOn', 'true', 5200, Y); G.link(ne2[0], ne2[1], s_on, 'execute')
# walked away: the card hides again
far = b.b2('BooleanAND', g('CardOn', BOOL, 2300, Y + 1100), b.dcmp('Greater_DoubleDouble', dd, None, 2500, Y + 1200, db='600.0'), 2700, Y + 1100)
bfar = b.branch(far, 2700, Y + 900, tag='IfFar'); G.link(bg, 'else', bfar, 'execute')
h5 = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='true')], 3000, Y + 900, target=g('Card', OBJV(SMC), 2800, Y + 1200), tag='CardOff')
G.link(bfar, 'then', h5, 'execute'); G.link(h5, 'then', b.set_b('CardOn', 'false', 3300, Y + 900), 'execute')
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
names = [n[0] for n in G.nodes]
if bad or len(names) != len(set(names)): raise SystemExit('BP_MineFind: bad links %s / dup names' % bad[:6])
open(os.path.join(HERE, 'BP_MineFind_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BP_MineFind_graph.txt: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ===================================================================================================================== variables
LIFT_VARS = [('Partner', 'obj:Actor', '', 'INSTANCE: the other BP_MineLift (set by import_mine543_ue.py --place)'),
             ('Gate', 'obj:Actor', '', 'INSTANCE, top only: MineGate_Up (the hut door it opens)'),
             ('IsTop', 'bool', 'false', 'INSTANCE: true on MineLift_Top'),
             ('RopeTop', 'real', '115.0', 'INSTANCE cm: where the rope leaves (top: the drum, 115; bottom: the shaft top, 1450)'),
             ('PromptTop', 'string', '[E] Open the mine door', 'shown at the hut door'),
             ('PromptBottom', 'string', '[E] Ride the bucket up', 'shown at the bucket in the dungeon'),
             ('ArriveText', 'string', 'The old mine, 50 m down', 'notice on arrival below'),
             ('ArriveTextTop', 'string', 'Back up at the mine entrance', 'notice on arrival above'),
             ('UseRange', 'real', '220.0', 'cm: how near the hero must be'),
             ('DDoor', 'real', '0.8', 's: the door swing'), ('DTop', 'real', '4.5', 's: the top leg (8.5 m)'),
             ('DBottom', 'real', '5.4', 's: the bottom leg (10.2 m); keep DBottom = DTop x 1.2 so the speed matches at the swap'),
             ('Phase', 'int', '0', 'scratch: ride state 0..8'), ('T', 'real', '0.0', 'scratch: time in this phase'),
             ('EWas', 'bool', 'false', 'scratch'), ('PressNow', 'bool', 'false', 'scratch'), ('Shown', 'bool', 'false', 'scratch')]
FIND_VARS = [('Prompt', 'string', '[E] Take the sword', 'shown near the find'),
             ('FoundText', 'string', 'You found the Ulfberht sword', 'notice when taken (the card shows)'),
             ('UseRange', 'real', '220.0', 'cm'), ('Taken', 'bool', 'false', 'scratch'), ('CardOn', 'bool', 'false', 'scratch'),
             ('EWas', 'bool', 'false', 'scratch'), ('PressNow', 'bool', 'false', 'scratch'), ('Shown', 'bool', 'false', 'scratch')]
def vt(kind):
    if kind == 'real': return 'PinCategory="real",PinSubCategory="double"'
    if kind in ('bool', 'string', 'int'): return 'PinCategory="%s"' % kind
    if kind.startswith('obj:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % kind[4:]
    raise ValueError(kind)
def bpv(bp, n, k, d):
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
        n, uuid.uuid5(uuid.NAMESPACE_URL, 'mine543/%s/%s' % (bp, n)).hex.upper(), vt(k), n, d)
for bp, vars_ in (('BP_MineLift', LIFT_VARS), ('BP_MineFind', FIND_VARS)):
    open(os.path.join(HERE, 'VARIABLES_%s_BPVar.txt' % bp), 'w', newline='\r\n').write(
        '# #543 %s - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' % bp + '\n'.join(bpv(bp, *v[:3]) for v in vars_) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    for bp, vars_ in (('BP_MineLift', LIFT_VARS), ('BP_MineFind', FIND_VARS)):
        f.write('## %s (BPVar lines in VARIABLES_%s_BPVar.txt)\n\n| Name | Default | Meaning |\n|---|---|---|\n' % (bp, bp))
        for n, _k, d, m in vars_: f.write('| %s | %s | %s |\n' % (n, d or '-', m))
        f.write('\n')
print('BPVar lines: %d + %d' % (len(LIFT_VARS), len(FIND_VARS)))
