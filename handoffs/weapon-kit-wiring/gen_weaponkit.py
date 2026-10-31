# Weapon kit wiring (checkking, 2026-10-31): makes the 25 checkking weapons (#233) buyable and holdable.
#   python gen_weaponkit.py -> BPC_WeaponKit_graph.txt, ArmoryHUD_WeaponHook_graph.txt, manifest_armoryhud_weapons.json,
#                              VARIABLES_BPVar.txt, weapons.json (the data table setup_weaponkit_ue.py writes into the defaults)
# BPC_WeaponKit (hero component "WeaponKit"):
#   BeginPlay: finds the hero's KitWeapon StaticMeshComponent (tag KitWeapon) and KnightMesh (tag ObsKnight, from set v2),
#              attaches the weapon to hand_r (snap) with WeaponRot, loads the save, shows the equipped weapon.
#   DrawWeapons(Hud, SizeX, SizeY): while Vesna's shop is open, a WEAPONSMITH panel on the LEFT edge (the Obsidian panel is
#              on the right): 25 rows "name  DMG n  BUY price / EQUIP / EQUIPPED"; click = buy (HUD Gold) or equip / unequip.
#   Save slot CastleSaveWeapons (BP_CastleSave, Data = [Owned, Equipped]).
# Damage: the component exposes Damage[Equipped] for the hero's hit code; wiring it into the sword damage is the next step.
import os, sys, json, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'motion-graphics-66')); sys.path.insert(0, os.path.join(ROOT, 'obsidian-set-v2'))
import gen_motionfx as gm          # B2 drawing helpers (re-writes its own graph file with the same content)
import gen_set_v2 as gs            # mpc_get / has / bit helpers (same)
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

WEAPONS = [  # (folder, display name, price, damage, speed)
    ('ArmingSword', 'Arming Sword', 300, 40, 1.10), ('VikingSword', 'Viking Sword', 350, 44, 1.05), ('Falchion', 'Falchion', 380, 48, 1.00),
    ('Messer', 'Messer', 400, 46, 1.05), ('Katzbalger', 'Katzbalger', 420, 45, 1.15), ('RondelDagger', 'Rondel Dagger', 200, 28, 1.40),
    ('Longsword', 'Longsword', 600, 58, 0.95), ('Estoc', 'Estoc', 650, 55, 1.00), ('Zweihander', 'Zweihander', 1200, 80, 0.75),
    ('BeardedAxe', 'Bearded Axe', 350, 50, 0.95), ('WarAxe', 'War Axe', 450, 52, 1.00), ('DaneAxe', 'Dane Axe', 900, 72, 0.80),
    ('Bardiche', 'Bardiche', 1000, 74, 0.75), ('LochaberAxe', 'Lochaber Axe', 1050, 76, 0.75), ('FlangedMace', 'Flanged Mace', 500, 56, 0.90),
    ('WarHammer', 'War Hammer', 550, 58, 0.90), ('MorningStar', 'Morning Star', 520, 60, 0.85), ('WingedSpear', 'Winged Spear', 500, 46, 1.00),
    ('BoarSpear', 'Boar Spear', 550, 50, 0.95), ('Partisan', 'Partisan', 800, 62, 0.85), ('Ranseur', 'Ranseur', 850, 62, 0.85),
    ('Guisarme', 'Guisarme', 850, 64, 0.85), ('Glaive', 'Glaive', 900, 66, 0.80), ('Halberd', 'Halberd', 1100, 75, 0.75),
    ('Pollaxe', 'Pollaxe', 1150, 78, 0.75)]
json.dump([dict(folder=f, name=n, price=p, damage=d, speed=s) for f, n, p, d, s in WEAPONS], open(os.path.join(HERE, 'weapons.json'), 'w'), indent=1)

SELF = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit', 'BPC_WeaponKit')
ZHUD = BPC('/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD', 'BP_ZombieHUD')
SAVEC = BPC('/Game/CastleDefender/Gameplay/Save/BP_CastleSave', 'BP_CastleSave')
SMC = CLS('StaticMeshComponent'); SM = CLS('StaticMesh'); HUDC = CLS('HUD'); SAVEG = CLS('SaveGame')
KEY = '"/Script/CoreUObject.ScriptStruct\'/Script/InputCore.Key\'"'
INT, DBL, BOOL = it('v', default='0'), D('v', default='0.0'), bo('v', default='false')
NAME_ = lambda n, default=None, out=False: {'name': n, 'cat': 'name', 'default': default, 'out': out}
RULE = lambda n: {'name': n, 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EAttachmentRule\'"', 'default': 'SnapToTarget'}
F = gm.F; col = gm.col; SLOT = 'CastleSaveWeapons'


class B3(gm.B2):
    mpc_get = gs.B2.mpc_get; has = gs.B2.has; bit = gs.B2.bit; round_ = gs.B2.round_; pow = gs.B2.pow; item = gs.B2.item
    b2d = gs.B2.b2d; seli = gs.B2.seli; owner = gs.B2.owner
    def me(s, member, x, y, pins=()):
        return s.call_self(member, list(pins), x, y, SELF, tag='Call' + member)


G = Graph(); b = B3(G, 'wk')
COMP = CLS('ActorComponent')
# ---------------------------------------------------------------- BeginPlay
G.node('BP', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
own = b.owner(0, 250)
fw = b.call(ACT, 'GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.StaticMeshComponent'), NAME_('Tag', 'KitWeapon'), arr(ob('ReturnValue', SMC, out=True))],
            300, 250, target=own, const=True, pure=True, tag='FindWeapon')
sh = b.set('Held', ob('v', SMC), b.item((fw, 'ReturnValue'), ob('v', SMC), None, 550, 300), 700, 0); G.link('BP', 'then', sh, 'execute')
fk = b.call(ACT, 'GetComponentsByTag', [CLSPIN('ComponentClass', COMP, '/Script/Engine.SkeletalMeshComponent'), NAME_('Tag', 'ObsKnight'), arr(ob('ReturnValue', SKEL, out=True))],
            700, 450, target=b.owner(500, 450), const=True, pure=True, tag='FindKnight')
held = lambda x, y: b.get('Held', ob('v', SMC), x, y)
bv = b.branch(b.valid(held(900, 250), 1000, 250), 1000, 0, tag='IfHeld'); G.link(sh, 'then', bv, 'execute')
at = b.call(SCENE, 'K2_AttachToComponent', [ob('Parent', SCENE), NAME_('SocketName', 'hand_r'), RULE('LocationRule'), RULE('RotationRule'), RULE('ScaleRule'),
            bo('bWeldSimulatedBodies', default='false'), bo('ReturnValue', out=True, default='false')], 1300, 0, target=held(1200, 300))
kn = b.item((fk, 'ReturnValue'), ob('v', SKEL), None, 1000, 500)
b.wire(kn, at, 'Parent')
sk = b.set('Knight', ob('v', SKEL), kn, 1150, -250); G.link(bv, 'then', sk, 'execute'); G.link(sk, 'then', at, 'execute')
rr = b.call(SCENE, 'K2_SetRelativeRotation', [st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'), st('SweepHitResult', HITRES, out=True),
            bo('bTeleport', default='true')], 1600, 0, target=held(1500, 300))
b.wire(b.get('WeaponRot', st('v', ROT), 1400, 450), rr, 'NewRotation'); G.link(at, 'then', rr, 'execute')
b.chain(rr, b.me('LoadSaved', 1900, 0), b.me('ApplyEquip', 2200, 0))

# ---------------------------------------------------------------- ApplyEquip: show Meshes[Equipped] in the hand, or hide
Y = 900
b.event('ApplyEquip', [], 0, Y)
bh = b.branch(b.valid(held(0, Y + 250), 200, Y + 250), 200, Y, tag='IfHeld2'); G.link('ApplyEquip', 'then', bh, 'execute')
eq = b.get('Equipped', INT, 300, Y + 400)
on = b.icmp('GreaterEqual_IntInt', eq, None, 500, Y + 400, db='0')
be = b.branch(on, 450, Y, tag='IfEquipped'); G.link(bh, 'then', be, 'execute')
ssm = b.call(SMC, 'SetStaticMesh', [ob('NewMesh', SM), bo('ReturnValue', out=True, default='false')], 700, Y, target=held(600, Y + 250))
b.wire(b.aget('Meshes', ob('v', SM), eq, 600, Y + 550), ssm, 'NewMesh'); G.link(be, 'then', ssm, 'execute')
sv = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='false'), bo('bPropagateToChildren', default='false')], 1000, Y, target=held(900, Y + 250))
b.wire(on, sv, 'bNewVisibility'); G.link(ssm, 'then', sv, 'execute'); G.link(be, 'else', sv, 'execute')
knv = b.get('Knight', ob('v', SKEL), 1100, Y + 400)
bk_ = b.branch(b.b2('BooleanAND', b.valid(knv, 1300, Y + 400), on, 1500, Y + 400), 1300, Y, tag='IfHideSword'); G.link(sv, 'then', bk_, 'execute')
bvk = b.branch(b.valid(knv, 1300, Y + 600), 1300, Y + 200, tag='IfKnight'); G.link(bk_, 'else', bvk, 'execute')
hb = b.call(SKIN, 'HideBoneByName', [NAME_('BoneName'), {'name': 'PhysBodyOption', 'cat': 'byte', 'obj': "\"/Script/CoreUObject.Enum'/Script/Engine.EPhysBodyOp'\"", 'default': 'PBO_None'}], 1600, Y, target=knv, tag='HideSword')
b.wire(b.get('KnightSwordBone', NAME_('v'), 1450, Y + 700), hb, 'BoneName'); G.link(bk_, 'then', hb, 'execute')
ub = b.call(SKIN, 'UnHideBoneByName', [NAME_('BoneName')], 1600, Y + 200, target=knv, tag='ShowSword')
b.wire(b.get('KnightSwordBone', NAME_('v'), 1450, Y + 800), ub, 'BoneName'); G.link(bvk, 'then', ub, 'execute')

# ---------------------------------------------------------------- save / load (Data = [Owned, Equipped])
Y = 1700
b.event('SaveNow', [], 0, Y)
cs = b.lib(GS, 'CreateSaveGameObject', [CLSPIN('SaveGameClass', SAVEG, '/Game/CastleDefender/Gameplay/Save/BP_CastleSave.BP_CastleSave_C'), ob('ReturnValue', SAVEC, out=True)], 300, Y, tag='NewSave')
G.link('SaveNow', 'then', cs, 'execute')
cast(G, 'AsSave', SAVEC, 'AsBP Castle Save', 300, Y + 300, pure=True); b.wire((cs, 'ReturnValue'), 'AsSave', 'Object')
mk = b.name('MakeData'); G.node(mk, 'K2Node_MakeArray', ['NumInputs=2'], [D('[0]', default='0.0'), D('[1]', default='0.0'), arr(D('Array', out=True))], 600, Y + 300)
b.wire(b.i2d(b.get('Owned', INT, 300, Y + 500), 450, Y + 500), mk, '[0]'); b.wire(b.i2d(b.get('Equipped', INT, 300, Y + 600), 450, Y + 600), mk, '[1]')
sd = b.setm('Data', SAVEC, arr(D('Data')), (mk, 'Array'), ('AsSave', 'AsBP Castle Save'), 900, Y); G.link(cs, 'then', sd, 'execute')
svg = b.lib(GS, 'SaveGameToSlot', [ob('SaveGameObject', SAVEG), S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 1200, Y, tag='Save')
b.wire(('AsSave', 'AsBP Castle Save'), svg, 'SaveGameObject'); G.link(sd, 'then', svg, 'execute')
Y = 2400
b.event('LoadSaved', [], 0, Y)
hs = b.lib(GS, 'DoesSaveGameExist', [S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], 200, Y + 200, pure=True, tag='HasSave')
bl = b.branch((hs, 'ReturnValue'), 300, Y, tag='IfSave'); G.link('LoadSaved', 'then', bl, 'execute')
ld = b.lib(GS, 'LoadGameFromSlot', [S('SlotName', default=SLOT), it('UserIndex', default='0'), ob('ReturnValue', SAVEG, out=True)], 600, Y, tag='Load'); G.link(bl, 'then', ld, 'execute')
cast(G, 'AsLoad', SAVEC, 'AsBP Castle Save', 600, Y + 300, pure=True); b.wire((ld, 'ReturnValue'), 'AsLoad', 'Object')
dat = b.getm('Data', SAVEC, arr(D('Data')), ('AsLoad', 'AsBP Castle Save'), 850, Y + 300)
s1 = b.set('Owned', INT, b.round_(b.item(dat, D('v'), None, 1050, Y + 450), 1250, Y + 450), 1000, Y); G.link(ld, 'then', s1, 'execute')
s2 = b.set('Equipped', INT, b.round_(b.item(dat, D('v'), b.i2('Add_IntInt', None, None, 1050, Y + 650, da='1'), 1250, Y + 600), 1450, Y + 600), 1300, Y)
G.link(s1, 'then', s2, 'execute')

# ---------------------------------------------------------------- DrawWeapons (left edge of Vesna's shop)
Y = 3400
b.event('DrawWeapons', [ob('Hud', HUDC), it('SizeX'), it('SizeY')], 0, Y)
hud = ('DrawWeapons', 'Hud')
gsh, csh = b.mpc_get('Shop', 300, Y); G.link('DrawWeapons', 'then', gsh, 'execute')
paused = b.lib(GS, 'IsGamePaused', [WC(), bo('ReturnValue', out=True, default='false')], 500, Y + 450, pure=True, tag='Paused')
bo_ = b.branch(b.b2('BooleanAND', b.dcmp('Greater_DoubleDouble', csh['R'], None, 700, Y + 350, db='0.5'), (paused, 'ReturnValue'), 900, Y + 400), 700, Y, tag='IfShop')
G.link(gsh, 'then', bo_, 'execute')
sc = b.d2('Divide_DoubleDouble', b.i2d(('DrawWeapons', 'SizeY'), 300, Y + 700), None, 500, Y + 700, db='1080.0')
u = lambda v, x, y: b.mul(sc, None, x, y, db=str(float(v)))
PX, PY, W, RH = u(30, 700, Y + 1000), u(170, 700, Y + 1100), u(380, 700, Y + 1200), u(29, 700, Y + 1300)
bg = b.call(HUDC, 'DrawRect', [st('RectColor', LC, default=col(0.02, 0.015, 0.01, 0.72)), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH')], 1100, Y, target=hud, tag='PanelBg')
b.wire(b.sub(PX, u(14, 900, Y + 1400), 1000, Y + 1400), bg, 'ScreenX'); b.wire(b.sub(PY, u(60, 900, Y + 1500), 1000, Y + 1500), bg, 'ScreenY')
b.wire(b.add(W, u(28, 900, Y + 1600), 1000, Y + 1600), bg, 'ScreenW'); b.wire(b.add(b.mul(RH, None, 900, Y + 1700, db=str(float(len(WEAPONS)))), u(80, 900, Y + 1800), 1000, Y + 1750), bg, 'ScreenH')
G.link(bo_, 'then', bg, 'execute')
t1 = b.text(hud, 'WEAPONSMITH', b.colr(None, None, None, None, 1300, Y + 1900, dr='1.0', dg='0.72', db_='0.28'), PX, b.sub(PY, u(52, 1100, Y + 2000), 1300, Y + 2000), u(0.40, 1300, Y + 2100), 1500, Y, tag='Title')
G.link(bg, 'then', t1, 'execute')
pcn = b.call(HUDC, 'GetOwningPlayerController', [ob('ReturnValue', PCON, out=True)], 1500, Y + 2300, target=hud, pure=True, const=True, tag='PC')
mp = b.call(PCON, 'GetMousePosition', [F('LocationX', out=True), F('LocationY', out=True), bo('ReturnValue', out=True, default='false')], 1700, Y + 2300, target=(pcn, 'ReturnValue'), pure=True, const=True, tag='Mouse')
clk = b.call(PCON, 'WasInputKeyJustPressed', [st('Key', KEY, default='LeftMouseButton'), bo('ReturnValue', out=True, default='false')], 1700, Y + 2500, target=(pcn, 'ReturnValue'), pure=True, const=True, tag='Click')
lr = b.forloop(None, b.i2('Subtract_IntInt', b.alen('Names', S('v'), 1900, Y + 300), None, 2100, Y + 300, db='1'), 2300, Y); G.link(t1, 'then', lr, 'execute')
ri = (lr, 'Index')
ry = b.add(PY, b.mul(RH, b.i2d(ri, 2300, Y + 2700), 2500, Y + 2700), 2700, Y + 2700)
bitr = b.bit(b.i2('Add_IntInt', ri, None, 2300, Y + 2850, db='10'), 2300, Y + 2850)     # bit(Id-10) helper -> bit(i)
own_ = b.has(b.get('Owned', INT, 2900, Y + 3000), bitr, 3100, Y + 3000)
iseq = b.icmp('EqualEqual_IntInt', b.get('Equipped', INT, 2900, Y + 3150), ri, 3100, Y + 3150)
price = b.aget('Prices', INT, ri, 2900, Y + 3300)
cz = b.name('AsZHud'); cast(G, cz, ZHUD, 'AsBP Zombie HUD', 2900, Y + 3450, pure=True); b.wire(hud, cz, 'Object')
gold = b.getm('Gold', ZHUD, INT, (cz, 'AsBP Zombie HUD'), 3100, Y + 3450)
afford = b.icmp('GreaterEqual_IntInt', gold, price, 3300, Y + 3400)
istr = lambda src, x, y: (lambda n: (b.wire(src, n, 'InInt'), (n, 'ReturnValue'))[1])(b.lib(KSTR, 'Conv_IntToString', [it('InInt', default='0'), S('ReturnValue', out=True)], x, y, pure=True))
stt = b.selstr(None, b.concat(None, istr(price, 3300, Y + 3600), 3500, Y + 3600, da='BUY  '), b.bnot(own_, 3500, Y + 3750), 3700, Y + 3650, da='EQUIP')
stt = b.selstr(None, stt, iseq, 3900, Y + 3650, da='EQUIPPED')
line = b.concat(b.concat(b.aget('Names', S('v'), ri, 3300, Y + 3900), None, 3500, Y + 3900, db='   DMG '), istr(b.aget('Damage', INT, ri, 3300, Y + 4050), 3500, Y + 4050), 3700, Y + 3950)
selc = lambda a, c, pick, x, y, da, db: b.math('SelectColor', [(st('A', LC, default=da), a), (st('B', LC, default=db), c), (bo('bPickA', default='false'), pick)], st('ReturnValue', LC, out=True), x, y)
cst = selc(None, None, afford, 3900, Y + 4200, col(0.95, 0.88, 0.76), col(0.85, 0.32, 0.25))
cst = selc(cst, None, b.bnot(own_, 3900, Y + 4350), 4100, Y + 4300, col(0, 0, 0), col(0.80, 0.80, 0.80))
cst = selc(None, cst, iseq, 4300, Y + 4300, col(1.0, 0.74, 0.30), col(0, 0, 0))
mx, my = (mp, 'LocationX'), (mp, 'LocationY')
hov = b.b2('BooleanAND', b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', mx, PX, 2700, Y + 4500), b.dcmp('Less_DoubleDouble', mx, b.add(PX, W, 2700, Y + 4600), 2900, Y + 4600), 3100, Y + 4550),
           b.b2('BooleanAND', b.dcmp('GreaterEqual_DoubleDouble', my, ry, 2900, Y + 4700), b.dcmp('Less_DoubleDouble', my, b.add(ry, RH, 2700, Y + 4800), 2900, Y + 4800), 3100, Y + 4750), 3300, Y + 4650)
bhv = b.branch(hov, 2600, Y, tag='IfHover'); G.link(lr, 'LoopBody', bhv, 'execute')
hl = b.call(HUDC, 'DrawRect', [st('RectColor', LC, default=col(1.0, 0.70, 0.25, 0.12)), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH')], 2900, Y, target=hud, tag='RowHover')
b.wire(PX, hl, 'ScreenX'); b.wire(ry, hl, 'ScreenY'); b.wire(W, hl, 'ScreenW'); b.wire(RH, hl, 'ScreenH'); G.link(bhv, 'then', hl, 'execute')
tn = b.text(hud, '', b.colr(None, None, None, None, 3100, Y + 5000, dr='0.92', dg='0.86', db_='0.74'), b.add(PX, u(6, 3100, Y + 5100), 3300, Y + 5100), b.add(ry, u(5, 3100, Y + 5200), 3300, Y + 5200), u(0.24, 3300, Y + 5300), 3200, Y, tag='RowName')
b.wire(line, tn, 'Text'); G.link(hl, 'then', tn, 'execute'); G.link(bhv, 'else', tn, 'execute')
ts = b.text(hud, '', None, b.add(PX, u(262, 3300, Y + 5400), 3500, Y + 5400), b.add(ry, u(5, 3300, Y + 5500), 3500, Y + 5500), u(0.24, 3500, Y + 5600), 3500, Y, tag='RowState')
b.wire(stt, ts, 'Text'); b.wire(cst, ts, 'TextColor'); G.link(tn, 'then', ts, 'execute')
bc = b.branch(b.b2('BooleanAND', hov, (clk, 'ReturnValue'), 3700, Y + 300), 3800, Y, tag='IfClick'); G.link(ts, 'then', bc, 'execute')
bow = b.branch(own_, 4100, Y, tag='IfOwned'); G.link(bc, 'then', bow, 'execute')
# owned: toggle equip (click the equipped one = put it away)
seq_ = b.set('Equipped', INT, b.seli(None, ri, iseq, 4300, Y + 300, da='-1'), 4400, Y); G.link(bow, 'then', seq_, 'execute')
b.chain(seq_, b.me('ApplyEquip', 4700, Y), b.me('SaveNow', 5000, Y))
# not owned: buy if affordable, then equip it
bg2 = b.branch(afford, 4400, Y + 500, tag='IfGold'); G.link(bow, 'else', bg2, 'execute')
pay = b.setm('Gold', ZHUD, INT, b.i2('Subtract_IntInt', gold, price, 4500, Y + 800), (cz, 'AsBP Zombie HUD'), 4700, Y + 500); G.link(bg2, 'then', pay, 'execute')
so = b.set('Owned', INT, b.i2('Or_IntInt', b.get('Owned', INT, 4800, Y + 800), bitr, 5000, Y + 800), 5000, Y + 500); G.link(pay, 'then', so, 'execute')
se = b.set('Equipped', INT, ri, 5300, Y + 500); G.link(so, 'then', se, 'execute')
b.chain(se, b.me('ApplyEquip', 5600, Y + 500), b.me('SaveNow', 5900, Y + 500))
rt = b.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], 4600, Y + 1100, pure=True, tag='RealNow')
smsg = b.set('MsgUntil', DBL, b.d2('Add_DoubleDouble', (rt, 'ReturnValue'), None, 4800, Y + 1100, db='1.5'), 4700, Y + 900); G.link(bg2, 'else', smsg, 'execute')
rt2 = b.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], 2300, Y + 6000, pure=True, tag='RealNow')
bm = b.branch(b.dcmp('Less_DoubleDouble', (rt2, 'ReturnValue'), b.get('MsgUntil', DBL, 2300, Y + 6150), 2500, Y + 6050), 2600, Y + 5900, tag='IfMsg'); G.link(lr, 'Completed', bm, 'execute')
tm = b.text(hud, 'Not enough gold, hunter.', b.colr(None, None, None, None, 2700, Y + 6500, dr='0.85', dg='0.32', db_='0.25'), PX, b.add(PY, b.mul(RH, None, 2700, Y + 6300, db=str(len(WEAPONS) + 0.3)), 2900, Y + 6300), u(0.26, 2900, Y + 6400), 2900, Y + 5900, tag='NoGold')
G.link(bm, 'then', tm, 'execute')

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
open(os.path.join(HERE, 'BPC_WeaponKit_graph.txt'), 'w', newline='\r\n').write(G.render())
print('BPC_WeaponKit', len(G.nodes), 'nodes', len(G.links), 'links')

# ---------------------------------------------------------------- ArmoryHUD hook add-on (after the 3-pin checkking hook)
G = Graph(); b = bpkit.B(G, 'wh')
pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 0, 200, pure=True, tag='HookPawn')
gc = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, '/Game/CastleDefender/Gameplay/Castle/BPC_WeaponKit.BPC_WeaponKit_C'), ob('ReturnValue', SELF, out=True)],
            250, 200, target=(pp, 'ReturnValue'), pure=True, const=True, tag='HookKit')
branch(G, 'WeaponHookIf', 300, 0); b.wire(b.valid((gc, 'ReturnValue'), 500, 200), 'WeaponHookIf', 'Condition')
me_ = b.self_node(500, 350)
dw = b.call(SELF, 'DrawWeapons', [ob('Hud', HUDC), it('SizeX', default='0'), it('SizeY', default='0')], 700, 0, target=(gc, 'ReturnValue'), tag='HookWeapons')
G.link('WeaponHookIf', 'then', dw, 'execute'); b.wire(me_, dw, 'Hud')
for p in ('SizeX', 'SizeY'):
    n = 'WeaponSize' + p[-1]; mathfn(G, n, 'Add_IntInt', [it('A', default='0'), it('B', default='0'), it('ReturnValue', out=True)], 500, 500 if p == 'SizeX' else 600)
    G.link(n, 'ReturnValue', dw, p)
open(os.path.join(HERE, 'ArmoryHUD_WeaponHook_graph.txt'), 'w', newline='\r\n').write(G.render())
json.dump({'blueprint': 'BP_ArmoryHUD', '_apply': 'after the checkking 3-pin hook (#222/#231) is in: it chains after HookReveal (DrawReveal)',
           'pastes': [{'file': 'ArmoryHUD_WeaponHook_graph.txt', 'offset': [400, -1200]}],
           'rewires': [{'from': 'ohHookReveal10.then', 'to': 'WeaponHookIf.execute'},
                       {'from': 'CX_1.SizeX', 'to': 'WeaponSizeX.A'}, {'from': 'CX_1.SizeY', 'to': 'WeaponSizeY.A'}]},
          open(os.path.join(HERE, 'manifest_armoryhud_weapons.json'), 'w'), indent=1)
print('ArmoryHUD weapon hook', len(G.nodes), 'nodes')

# ---------------------------------------------------------------- BPVar lines for BPC_WeaponKit
def bpvar(name, vt, default):
    return 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),PropertyFlags=5,DefaultValue="%s")' % (name, uuid.uuid4().hex.upper(), vt, default)
REAL = 'PinCategory="real",PinSubCategory="double"'
lines = [bpvar('Owned', 'PinCategory="int"', '0'), bpvar('Equipped', 'PinCategory="int"', '-1'), bpvar('MsgUntil', REAL, '0.0'),
         bpvar('Held', 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.StaticMeshComponent\'"', ''),
         bpvar('WeaponRot', 'PinCategory="struct",PinSubCategoryObject="/Script/CoreUObject.ScriptStruct\'/Script/CoreUObject.Rotator\'"', '0,0,0'),
         bpvar('Names', 'PinCategory="string",ContainerType=Array', ''), bpvar('Prices', 'PinCategory="int",ContainerType=Array', ''),
         bpvar('Damage', 'PinCategory="int",ContainerType=Array', ''),
         bpvar('Speed', 'PinCategory="real",PinSubCategory="double",ContainerType=Array', ''),
         bpvar('KnightSwordBone', 'PinCategory="name"', 'weapon_r'),
         bpvar('Knight', "PinCategory=\"object\",PinSubCategoryObject=\"/Script/CoreUObject.Class'/Script/Engine.SkeletalMeshComponent'\"", ''),
         bpvar('Meshes', 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.StaticMesh\'",ContainerType=Array', '')]
open(os.path.join(HERE, 'VARIABLES_BPVar.txt'), 'w', newline='\r\n').write('# BPC_WeaponKit - paste one line at a time on the VARIABLES header\n' + '\n'.join(lines) + '\n')
