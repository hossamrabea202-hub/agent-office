# #8 Treasure chest, paste-only (adjustedfilm, 2026-10-31). Owner: "a closed treasure chest containing a good amount of
# money in the middle of the tunnel, must be closed, open with E, it opens and its shiny and gold obtained and shine gone
# (surrounded by dangerous creatures protecting the tunnel)". Replaces TGA 2's C++ plugin route (needs a native rebuild).
#   "<blender python>" -I gen_chest8.py -> BP_TreasureChest_graph.txt, VARIABLES_BPVar.txt, VARIABLES.md
# BP_TreasureChest (components made by setup_chest8_ue.py): Body, Hinge (tag ChestHinge) -> Lid, Glow (point light, tag
# ChestGlow), Glint (material billboard, tag ChestGlint).
#   BeginPlay  finds the 3 tagged parts; if the save slot CastleSaveChest<ChestId> exists the chest is already open (no pay,
#              no guards, lid open, no shine); starts ChestPoll every 0.05 s (a timer by name: no self-call nodes, #254).
#   ChestPoll  closed: the shine breathes (warm gold light + glint); hero within GuardRange (35 m) the first time -> guards
#              spawn around the chest (4 BP_Zombie along the tunnel 4.5-9 m in front / behind + 1 BP_HalfHorseZombie behind); hero within UseRange (2.2 m)
#              -> notice "[E] Open the chest" once per visit; E (edge-detected) -> Opened, +Reward gold (BP_ZombieHUD.Gold),
#              banner "Treasure! +1500 gold", coin sound, save.
#              opened: lid swings back over 0.9 s (ease-out cubic), the light bursts x4 then dies out over 1.6 s, the glint
#              goes after 0.25 s = "shine gone". A loaded open chest just sits open and dark.
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))   # bpkit exports its own HERE

P_NOTICE, P_ZHUD = '/Game/CastleDefender/Gameplay/Castle/BP_NoticeHUD', '/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD'
NOTC, ZHUDC = BPC(P_NOTICE, 'BP_NoticeHUD'), BPC(P_ZHUD, 'BP_ZombieHUD')
P_HORSE = '/Game/CastleDefender/Characters/Enemies/HalfHorseZombie/BP_HalfHorseZombie'
HORSE = BPC(P_HORSE, 'BP_HalfHorseZombie')
SAVEC = BPC('/Game/CastleDefender/Gameplay/Save/BP_CastleSave', 'BP_CastleSave')
SAVEG, HUDCLS, PCM, SOUND = CLS('SaveGame'), CLS('HUD'), CLS('PlayerCameraManager'), CLS('SoundBase')
PLC, LIGHTC = CLS('PointLightComponent'), CLS('LightComponent')
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
CH = '/Game/CastleDefender/Gameplay/Chest/'
SFX_OPEN, SFX_CASH = CH + 'SFX_ChestOpen.SFX_ChestOpen', CH + 'SFX_GoldCash.SFX_GoldCash'
MIDC = CLS('MaterialInstanceDynamic')
OBJV = lambda c: ob('v', c)
PRIMC = CLS('PrimitiveComponent')
NAME_ = lambda n, default=None: {'name': n, 'cat': 'name', 'default': default}


class B(bpkit.B):
    def add(s, a, c, x, y, db='0.0'): return s.d2('Add_DoubleDouble', a, c, x, y, db=db)
    def sub(s, a, c, x, y, da='0.0', db='0.0'): return s.d2('Subtract_DoubleDouble', a, c, x, y, da=da, db=db)
    def mul(s, a, c, x, y, db='1.0'): return s.d2('Multiply_DoubleDouble', a, c, x, y, db=db)
    def div(s, a, c, x, y, db='1.0'): return s.d2('Divide_DoubleDouble', a, c, x, y, db=db)
    def sat(s, v, x, y): return s.clamp(v, '0.0', '1.0', x, y)
    def pc(s, x, y):
        return (s.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], x, y, pure=True, tag='PC'), 'ReturnValue')
    def hero(s, x, y):
        return (s.lib(GS, 'GetPlayerCharacter', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', CHARC, out=True)], x, y, pure=True, tag='Hero'), 'ReturnValue')
    def loc(s, actor, x, y):
        return (s.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, target=actor, pure=True, const=True, tag='Loc'), 'ReturnValue')
    def myloc(s, x, y):
        return (s.call_self('K2_GetActorLocation', [V('ReturnValue', out=True)], x, y, ACT, pure=True, const=True, tag='MyLoc'), 'ReturnValue')
    def by_tag(s, cls_path, cls, tag, x, y):
        n = s.call_self('GetComponentsByTag', [CLSPIN('ComponentClass', CLS('ActorComponent'), cls_path), NAME_('Tag', tag), arr(ob('ReturnValue', cls, out=True))],
                        x, y, ACT, pure=True, const=True, tag='Find' + tag)
        it_ = s.name('First' + tag)
        s.G.node(it_, 'K2Node_GetArrayItem', [], [arr(ob('Array', cls)), it('Dimension 1', default='0'), ob('Output', cls, out=True)], x + 260, y)
        s.G.link(n, 'ReturnValue', it_, 'Array'); return (it_, 'Output')
    def slot(s, x, y):
        cv = s.lib(KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], x, y, pure=True, tag='IdStr')
        s.wire(s.get('ChestId', INT, x - 200, y), cv, 'InInt')
        return s.concat(None, (cv, 'ReturnValue'), x + 200, y, da='CastleSaveChest')
    def hud_cast(s, cls, label, x, y):
        hud = s.call(PCON, 'GetHUD', [ob('ReturnValue', HUDCLS, out=True)], x - 150, y + 300, target=s.pc(x - 350, y + 300), pure=True, const=True, tag='HUD')
        nc = s.name('As' + label.replace(' ', '')); cast(s.G, nc, cls, 'As' + label, x, y); s.wire((hud, 'ReturnValue'), nc, 'Object'); return nc, (nc, 'As' + label)
    def timer_ev(s, fn, interval, loop, x, y):
        n = s.lib(KSL, 'K2_SetTimer', [ob('Object', OBJ), S('FunctionName', default=fn), fl('Time', default=interval), bo('bLooping', default=loop),
                                       fl('InitialStartDelay', default='0.000000', advanced=True), fl('InitialStartDelayVariance', default='0.000000', advanced=True),
                                       st('ReturnValue', TIMERH, out=True)], x, y, tag='Timer' + fn)
        s.wire(s.self_node(x - 200, y + 200), n, 'Object'); return n


G = Graph(); b = B(G, 'ch')
g = b.get
# ================================================================================================= BeginPlay
G.node('chBeginPlay', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % ACT}, ex('then', True)], 0, 0)
s1 = b.set('Hinge', OBJV(SCENE), b.by_tag('/Script/Engine.SceneComponent', SCENE, 'ChestHinge', 100, 300), 400, 0)
s2 = b.set('Glow', OBJV(PLC), b.by_tag('/Script/Engine.PointLightComponent', PLC, 'ChestGlow', 400, 450), 700, 0)
s3 = b.set('Glint', OBJV(SCENE), b.by_tag('/Script/Engine.SceneComponent', SCENE, 'ChestGlint', 700, 600), 1000, 0)
s4 = b.set('Rays', OBJV(PRIMC), b.by_tag('/Script/Engine.PrimitiveComponent', PRIMC, 'ChestRays', 1000, 750), 1300, 0)
b.chain('chBeginPlay', s1, s2, s3, s4)
br4 = b.branch(b.valid(g('Rays', OBJV(PRIMC), 1300, 300), 1500, 300), 1550, 0, tag='IfRays'); G.link(s4, 'then', br4, 'execute')
mk = b.call(PRIMC, 'CreateDynamicMaterialInstance', [it('ElementIndex', default='0'), ob('SourceMaterial', CLS('MaterialInterface')), NAME_('OptionalName', 'None'),
            ob('ReturnValue', MIDC, out=True)], 1750, -150, target=g('Rays', OBJV(PRIMC), 1550, 150), tag='RaysMID')
G.link(br4, 'then', mk, 'execute')
smid = b.set('RaysMID', OBJV(MIDC), (mk, 'ReturnValue'), 2000, -150); G.link(mk, 'then', smid, 'execute')
afr = b.seq('chAfterRays', 1, 2250, 0); G.link(smid, 'then', afr, 'execute'); G.link(br4, 'else', afr, 'execute')
hs = b.lib(GS, 'DoesSaveGameExist', [S('SlotName'), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 2500, -300, tag='HasSave')
b.wire(b.slot(1000, 450), hs, 'SlotName')
bs = b.branch((hs, 'ReturnValue'), 2700, 0, tag='IfOpenedBefore'); G.link(afr, 'then_0', hs, 'execute'); G.link(hs, 'then', bs, 'execute')
so = b.set('Opened', bo('v', default='true'), None, 1600, -150); G.link(bs, 'then', so, 'execute')
st0 = b.set('OpenT0', D('v', default='-100.0'), None, 2900, -150); G.link(so, 'then', st0, 'execute')
scp = b.set('CashPlayed', bo('v', default='true'), None, 3150, -150); G.link(st0, 'then', scp, 'execute'); st0 = scp
tmr = b.timer_ev('ChestPoll', '0.05', 'true', 3400, 0)
G.link(st0, 'then', tmr, 'execute'); G.link(bs, 'else', tmr, 'execute')

# ================================================================================================= ChestPoll
Y = 1000
b.event('ChestPoll', [], 0, Y)
seq = b.seq('chPollSeq', 2, 200, Y); G.link('ChestPoll', 'then', seq, 'execute')
now = b.now(200, Y + 2400)
hero = b.hero(300, Y + 300)
dist = b.math('Vector_Distance', [(V('V1'), b.loc(hero, 500, Y + 300)), (V('V2'), b.myloc(500, Y + 450))], D('ReturnValue', out=True), 700, Y + 350)
alive = b.valid(hero, 700, Y + 200)
near = b.b2('BooleanAND', alive, b.dcmp('Less_DoubleDouble', dist, g('UseRange', DBL, 900, Y + 450), 1100, Y + 400), 1300, Y + 300)
# ---- then_0: only while closed
bc = b.branch(b.bnot(g('Opened', BOOL, 500, Y - 200), 700, Y - 200), 500, Y, tag='IfClosed'); G.link(seq, 'then_0', bc, 'execute')
down = b.call(PCON, 'IsInputKeyDown', [st('Key', KEY, default='E'), bo('ReturnValue', out=True, default='false')], 900, Y + 600, target=b.pc(700, Y + 600), pure=True, const=True, tag='KeyE')
press = b.b2('BooleanAND', b.b2('BooleanAND', (down, 'ReturnValue'), b.bnot(g('EWas', BOOL, 1100, Y + 700), 1300, Y + 700), 1500, Y + 650), near, 1700, Y + 600)
sp = b.set('PressNow', BOOL, press, 800, Y); G.link(bc, 'then', sp, 'execute')
se = b.set('EWas', BOOL, (down, 'ReturnValue'), 1050, Y); G.link(sp, 'then', se, 'execute')
# guards, the first time the hero comes within GuardRange
gnear = b.b2('BooleanAND', alive, b.dcmp('Less_DoubleDouble', dist, g('GuardRange', DBL, 1300, Y + 900), 1500, Y + 900), 1700, Y + 850)
bg = b.branch(b.b2('BooleanAND', gnear, b.bnot(g('Guarded', BOOL, 1500, Y + 1000), 1700, Y + 1000), 1900, Y + 950), 1300, Y, tag='IfGuards')
G.link(se, 'then', bg, 'execute')
sgd = b.set('Guarded', bo('v', default='true'), None, 1550, Y - 300); G.link(bg, 'then', sgd, 'execute')
lp = b.forloop(None, b.i2('Subtract_IntInt', g('GuardCount', INT, 1600, Y - 450), None, 1800, Y - 450, db='1'), 1800, Y - 300)
G.link(sgd, 'then', lp, 'execute')
fwd = (b.call_self('GetActorForwardVector', [V('ReturnValue', out=True)], 2900, Y - 800, ACT, pure=True, const=True, tag='Fwd'), 'ReturnValue')
rgt = (b.call_self('GetActorRightVector', [V('ReturnValue', out=True)], 2900, Y - 700, ACT, pure=True, const=True, tag='Right'), 'ReturnValue')
# along the tunnel (it is only 2.5-5 m wide): even guards in front of the chest (between the hero and it), odd ones behind
even = b.icmp('EqualEqual_IntInt', b.i2('Percent_IntInt', (lp, 'Index'), None, 1900, Y - 600, db='2'), None, 2100, Y - 600, db='0')
sign = b.self_(None, None, even, 2300, Y - 600, da='1.0', db='-1.0')
dist_ = b.mul(sign, b.rnd('450.0', '900.0', 2300, Y - 450), 2500, Y - 550)
lat = b.rnd('-120.0', '120.0', 2500, Y - 400)
off = b.v2('Add_VectorVector', b.math('Multiply_VectorFloat', [(V('A'), fwd), (D('B', default='0.0'), dist_)], V('ReturnValue', out=True), 3100, Y - 650),
           b.math('Multiply_VectorFloat', [(V('A'), rgt), (D('B', default='0.0'), lat)], V('ReturnValue', out=True), 3100, Y - 500), 3300, Y - 550)
gl = b.v2('Add_VectorVector', b.v2('Add_VectorVector', b.myloc(3100, Y - 350), off, 3500, Y - 450), None, 3700, Y - 450, db='0.000000, 0.000000, 90.000000')
spz = spawn(b, '/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', BPC('/Game/CastleDefender/Characters/Enemies/Zombie/BP_Zombie', 'BP_Zombie'),
            transform(b, gl, 3900, Y - 450), 2200, Y - 300)
G.link(lp, 'LoopBody', spz, 'execute')
bb = b.branch(g('BruteToo', BOOL, 2100, Y - 100), 2200, Y - 150, tag='IfBrute'); G.link(lp, 'Completed', bb, 'execute')
hl = b.v2('Add_VectorVector', b.v2('Add_VectorVector', b.myloc(2300, Y + 0), b.math('Multiply_VectorFloat', [(V('A'), fwd), (D('B', default='-750.0'), None)], V('ReturnValue', out=True), 2300, Y + 150), 2500, Y + 0), None, 2700, Y + 50, db='0.000000, 0.000000, 120.000000')
sph = spawn(b, P_HORSE, HORSE, transform(b, hl, 2700, Y + 0), 2500, Y - 150)
G.link(bb, 'then', sph, 'execute')
mg = b.seq('chAfterGuards', 1, 2900, Y); G.link(bg, 'else', mg, 'execute'); G.link(bb, 'else', mg, 'execute'); G.link(sph, 'then', mg, 'execute')
# prompt once per visit
first = b.b2('BooleanAND', near, b.bnot(g('Shown', BOOL, 3000, Y + 300), 3200, Y + 300), 3400, Y + 250)
bf = b.branch(first, 3100, Y, tag='IfPrompt'); G.link(mg, 'then_0', bf, 'execute')
nc, nh = b.hud_cast(NOTC, 'BP Notice HUD', 3400, Y - 250); G.link(bf, 'then', nc, 'execute')
pn = b.call(NOTC, 'PushNotice', [S('Text'), it('Tier', default='0')], 3700, Y - 250, target=nh, tag='Prompt')
b.wire(g('Prompt', S('v'), 3500, Y - 400), pn, 'Text'); G.link(nc, 'then', pn, 'execute')
ssh = b.set('Shown', BOOL, near, 4000, Y)
for src, pin in ((bf, 'else'), (pn, 'then'), (nc, 'CastFailed')): G.link(src, pin, ssh, 'execute')
# E: open, pay, banner, sound, save
bp_ = b.branch(g('PressNow', BOOL, 4100, Y + 300), 4300, Y, tag='IfOpen'); G.link(ssh, 'then', bp_, 'execute')
o1 = b.set('Opened', bo('v', default='true'), None, 4550, Y); G.link(bp_, 'then', o1, 'execute')
o2 = b.set('OpenT0', DBL, now, 4800, Y); G.link(o1, 'then', o2, 'execute')
zc, zh = b.hud_cast(ZHUDC, 'BP Zombie HUD', 5100, Y)
zc2, zh2 = b.hud_cast(ZHUDC, 'BP Zombie HUD', 5250, Y + 150); G.link(zc, 'then', zc2, 'execute')      # one cast per consumer (fix_impure)
pay = b.setm('Gold', ZHUDC, INT, b.i2('Add_IntInt', b.getm('Gold', ZHUDC, INT, zh, 5200, Y + 400), g('Reward', INT, 5200, Y + 550), 5400, Y + 450), zh2, 5400, Y)
G.link(zc2, 'then', pay, 'execute')
snd = b.lib(GS, 'PlaySound2D', [WC(), dict(ob('Sound', SOUND), dobj=SFX_OPEN), fl('VolumeMultiplier', default='1.000000'), fl('PitchMultiplier', default='1.000000'),
            fl('StartTime', default='0.000000'), ob('ConcurrencySettings', CLS('SoundConcurrency')), ob('OwningActor', ACT), bo('bIsUISound', default='true')], 5700, Y, tag='Creak')
G.link(pay, 'then', snd, 'execute')
nc2, nh2 = b.hud_cast(NOTC, 'BP Notice HUD', 6000, Y); G.link(snd, 'then', nc2, 'execute')
rs = b.lib(KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], 6000, Y + 450, pure=True, tag='RewardStr')
b.wire(g('Reward', INT, 5800, Y + 450), rs, 'InInt')
msg = b.concat(b.concat(None, (rs, 'ReturnValue'), 6200, Y + 400, da='Treasure!  +'), None, 6400, Y + 400, db=' gold')
pn2 = b.call(NOTC, 'PushNotice', [S('Text'), it('Tier', default='1')], 6300, Y, target=nh2, tag='Reward')
b.wire(msg, pn2, 'Text'); G.link(nc2, 'then', pn2, 'execute')
cs = b.lib(GS, 'CreateSaveGameObject', [CLSPIN('SaveGameClass', SAVEG, '/Game/CastleDefender/Gameplay/Save/BP_CastleSave.BP_CastleSave_C'), ob('ReturnValue', SAVEG, out=True)], 6600, Y, tag='NewSave')
G.link(o2, 'then', cs, 'execute')            # save first: never opened without being saved
sv = b.lib(GS, 'SaveGameToSlot', [ob('SaveGameObject', SAVEG), S('SlotName'), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 6900, Y, tag='Save')
b.wire((cs, 'ReturnValue'), sv, 'SaveGameObject'); b.wire(b.slot(6700, Y + 300), sv, 'SlotName'); G.link(cs, 'then', sv, 'execute')
G.link(sv, 'then', zc, 'execute')

# ---- then_1: visuals (shine breathing while closed; lid, burst and fade once opened)
Y2 = Y + 3200
t = b.sub(now, g('OpenT0', DBL, 300, Y2 + 450), 500, Y2 + 400)
hv = b.branch(b.b2('BooleanAND', b.valid(g('Hinge', OBJV(SCENE), 300, Y2 + 200), 500, Y2 + 200), b.valid(g('Glow', OBJV(PLC), 300, Y2 + 300), 500, Y2 + 300), 700, Y2 + 250),
              400, Y2, tag='IfParts')
G.link(seq, 'then_1', hv, 'execute')
bo_ = b.branch(g('Opened', BOOL, 600, Y2 + 150), 700, Y2, tag='IfOpened'); G.link(hv, 'then', bo_, 'execute')
# closed: breathing shine
breath = b.mul(g('GlowBase', DBL, 900, Y2 - 300), b.add(b.mul(b.math('Sin', [(D('A', default='0.0'), b.mul(now, None, 900, Y2 - 450, db='2.2'))], D('ReturnValue', out=True), 1100, Y2 - 450),
                                                             None, 1300, Y2 - 450, db='0.25'), None, 1500, Y2 - 450, db='0.75'), 1700, Y2 - 350)
si0 = b.call(LIGHTC, 'SetIntensity', [fl('NewIntensity', default='0.0')], 1200, Y2 - 200, target=g('Glow', OBJV(PLC), 1000, Y2 - 100), tag='Shine')
b.wire(breath, si0, 'NewIntensity'); G.link(bo_, 'else', si0, 'execute')
# opened: lid ease-out cubic over 0.9 s, light burst x4 fading to 0 over 1.6 s, glint gone after 0.25 s
a = b.sat(b.div(t, None, 900, Y2 + 600, db='0.9'), 1100, Y2 + 600)
inv = b.sub(None, a, 1300, Y2 + 600, da='1.0')
ease = b.sub(None, b.mul(b.mul(inv, inv, 1500, Y2 + 600), inv, 1700, Y2 + 600), 1900, Y2 + 600, da='1.0')
pitch = b.mul(g('LidPitch', DBL, 1900, Y2 + 750), ease, 2100, Y2 + 650)
rot = b.math('MakeRotator', [(fl('Roll', default='0.0'), None), (fl('Pitch', default='0.0'), pitch), (fl('Yaw', default='0.0'), None)], st('ReturnValue', ROT, out=True), 2300, Y2 + 650)
rr = b.call(SCENE, 'K2_SetRelativeRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True),
            bo('bTeleport', default='true')], 1100, Y2 + 150, target=g('Hinge', OBJV(SCENE), 900, Y2 + 300), tag='Lid')
b.wire(rot, rr, 'NewRotation'); G.link(bo_, 'then', rr, 'execute')
burst = b.mul(b.mul(g('GlowBase', DBL, 1300, Y2 + 900), None, 1500, Y2 + 900, db='4.0'),
              b.d2('FMax', b.sub(None, b.div(t, None, 1500, Y2 + 1050, db='1.6'), 1700, Y2 + 1050, da='1.0'), None, 1900, Y2 + 1050, db='0.0'), 2100, Y2 + 950)
si1 = b.call(LIGHTC, 'SetIntensity', [fl('NewIntensity', default='0.0')], 1400, Y2 + 150, target=g('Glow', OBJV(PLC), 1300, Y2 + 300), tag='Burst')
b.wire(burst, si1, 'NewIntensity'); G.link(rr, 'then', si1, 'execute')
bgl = b.branch(b.valid(g('Glint', OBJV(SCENE), 1500, Y2 + 350), 1700, Y2 + 350), 1700, Y2 + 150, tag='IfGlint'); G.link(si1, 'then', bgl, 'execute')
vis = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='false')], 2000, Y2 + 150,
             target=g('Glint', OBJV(SCENE), 1800, Y2 + 350), tag='GlintVis')
b.wire(b.dcmp('Less_DoubleDouble', t, None, 1900, Y2 + 450, db='0.25'), vis, 'bNewVisibility'); G.link(bgl, 'then', vis, 'execute')
mg2 = b.seq('chAfterGlint', 1, 2300, Y2 + 150); G.link(vis, 'then', mg2, 'execute'); G.link(bgl, 'else', mg2, 'execute')
# rays: grow over 0.45 s (ease-out), full at 0.15 s, fade out from 0.6 s to 2.2 s
bry = b.branch(b.valid(g('RaysMID', OBJV(MIDC), 2300, Y2 + 450), 2500, Y2 + 450), 2500, Y2 + 150, tag='IfRaysMID'); G.link(mg2, 'then_0', bry, 'execute')
gr = b.sat(b.div(t, None, 2500, Y2 + 1300, db='0.45'), 2700, Y2 + 1300)
gi = b.sub(None, gr, 2900, Y2 + 1300, da='1.0')
grow = b.sub(None, b.mul(b.mul(gi, gi, 3100, Y2 + 1300), gi, 3300, Y2 + 1300), 3500, Y2 + 1300, da='1.0')
fade = b.mul(b.sat(b.div(t, None, 2500, Y2 + 1450, db='0.15'), 2700, Y2 + 1450), b.sat(b.sub(None, b.div(b.sub(t, None, 2500, Y2 + 1600, db='0.6'), None, 2700, Y2 + 1600, db='1.6'), 2900, Y2 + 1600, da='1.0'), 3100, Y2 + 1600), 3300, Y2 + 1500)
p1 = b.call(MIDC, 'SetScalarParameterValue', [NAME_('ParameterName', 'Grow'), fl('Value', default='0.0')], 2800, Y2 + 150, target=g('RaysMID', OBJV(MIDC), 2600, Y2 + 600), tag='RaysGrow')
b.wire(grow, p1, 'Value'); G.link(bry, 'then', p1, 'execute')
p2 = b.call(MIDC, 'SetScalarParameterValue', [NAME_('ParameterName', 'Fade'), fl('Value', default='0.0')], 3100, Y2 + 150, target=g('RaysMID', OBJV(MIDC), 2900, Y2 + 600), tag='RaysFade')
b.wire(fade, p2, 'Value'); G.link(p1, 'then', p2, 'execute')
mg3 = b.seq('chAfterRaysFx', 1, 3400, Y2 + 150); G.link(p2, 'then', mg3, 'execute'); G.link(bry, 'else', mg3, 'execute')
# gold cashing sound once, 0.35 s in (lid half open)
cash = b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', t, None, 3400, Y2 + 450, db='0.35'), b.bnot(g('CashPlayed', BOOL, 3400, Y2 + 600), 3600, Y2 + 600), 3800, Y2 + 500)
bca = b.branch(cash, 3700, Y2 + 150, tag='IfCash'); G.link(mg3, 'then_0', bca, 'execute')
scp2 = b.set('CashPlayed', bo('v', default='true'), None, 4000, Y2 + 150); G.link(bca, 'then', scp2, 'execute')
snd2 = b.lib(GS, 'PlaySound2D', [WC(), dict(ob('Sound', SOUND), dobj=SFX_CASH), fl('VolumeMultiplier', default='1.000000'), fl('PitchMultiplier', default='1.000000'),
             fl('StartTime', default='0.000000'), ob('ConcurrencySettings', CLS('SoundConcurrency')), ob('OwningActor', ACT), bo('bIsUISound', default='true')], 4300, Y2 + 150, tag='Cash')
G.link(scp2, 'then', snd2, 'execute')
# closed: rays off
p0 = b.branch(b.valid(g('RaysMID', OBJV(MIDC), 1300, Y2 - 650), 1500, Y2 - 650), 1500, Y2 - 200, tag='IfRaysOff'); G.link(si0, 'then', p0, 'execute')
p0s = b.call(MIDC, 'SetScalarParameterValue', [NAME_('ParameterName', 'Fade'), fl('Value', default='0.0')], 1800, Y2 - 200, target=g('RaysMID', OBJV(MIDC), 1600, Y2 - 650), tag='RaysOff')
G.link(p0, 'then', p0s, 'execute')

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
names = [n[0] for n in G.nodes]
if bad or len(names) != len(set(names)): raise SystemExit('bad links %s / dup names %s' % (bad[:10], sorted({n for n in names if names.count(n) > 1})[:5]))
open(os.path.join(HERE, 'BP_TreasureChest_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BP_TreasureChest_graph.txt: nodes %d, links %d' % (len(G.nodes), len(G.links)))

# ================================================================================================= BPVar lines
VARS = [('ChestId', 'int', '1', 'INSTANCE: unique per placed chest (its save slot is CastleSaveChest<ChestId>)'),
        ('Reward', 'int', '1500', 'INSTANCE: gold paid once'),
        ('Prompt', 'string', '[E] Open the chest', 'notice when the hero comes near'),
        ('UseRange', 'real', '220.0', 'cm'), ('GuardRange', 'real', '3500.0', 'cm: guards appear the first time the hero comes this near'),
        ('GuardCount', 'int', '4', 'BP_Zombie guards along the tunnel, 4.5-9 m in front of and behind the chest'), ('BruteToo', 'bool', 'true', '+1 BP_HalfHorseZombie 7.5 m behind the chest'),
        ('LidPitch', 'real', '-105.0', 'degrees the lid opens (flip the sign if it opens the wrong way)'),
        ('GlowBase', 'real', '60.0', 'candela of the gold shine while closed (x4 burst on opening)'),
        ('Opened', 'bool', 'false', 'state'), ('OpenT0', 'real', '-100.0', 'state'), ('EWas', 'bool', 'false', 'scratch'),
        ('Shown', 'bool', 'false', 'scratch'), ('PressNow', 'bool', 'false', 'scratch'), ('Guarded', 'bool', 'false', 'scratch'),
        ('CashPlayed', 'bool', 'false', 'state'), ('Rays', 'obj:PrimitiveComponent', '', 'found by tag'),
        ('RaysMID', 'obj:MaterialInstanceDynamic', '', 'made at BeginPlay'),
        ('Hinge', 'obj:SceneComponent', '', 'found by tag'), ('Glow', 'obj:PointLightComponent', '', 'found by tag'), ('Glint', 'obj:SceneComponent', '', 'found by tag')]
def vt(kind):
    if kind == 'real': return 'PinCategory="real",PinSubCategory="double"'
    if kind in ('int', 'bool', 'string'): return 'PinCategory="%s"' % kind
    if kind.startswith('obj:'): return 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.%s\'"' % kind[4:]
    raise ValueError(kind)
bpv = lambda n, k, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (
    n, uuid.uuid5(uuid.NAMESPACE_URL, 'chest8/' + n).hex.upper(), vt(k), n, d)
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write(
    '# #8 BP_TreasureChest - paste one line at a time on the VARIABLES header of My Blueprint, then Compile\n' + '\n'.join(bpv(*v[:3]) for v in VARS) + '\n')
with open(os.path.join(HERE, 'VARIABLES.md'), 'w', newline='\n') as f:
    f.write('# #8 BP_TreasureChest variables\n\n| Name | Default | Meaning |\n|---|---|---|\n')
    for n, _k, d, m in VARS: f.write('| %s | %s | %s |\n' % (n, d or '-', m))
print('BPVar lines: %d' % len(VARS))

