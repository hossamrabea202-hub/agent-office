# #418 shop v2: shields. EventGraph of the NEW hero component BPC_ShieldKit (one off-hand shield worn at a time).
#   python gen_shieldkit.py -> handoffs/shop-v2-418/shields/BPC_ShieldKit_graph.txt + shieldkit_data.json
# Data (defaults, set by setup_shieldkit_ue.py): Names, Prices, BlockChance, BlockMult, Meshes, GripLoc, GripRot.
# State: Owned (bit per shield), Worn (-1 = none), saved in slot "ShieldKit" (SG_ShieldKit: Owned, Worn).
# Events:
#   Buy(Index)   the shop has already taken the gold: Owned |= bit, then Wear(Index)
#   Wear(Index)  toggles: wearing the worn one takes it off; another one swaps (one off-hand at a time)
#   Apply        shows the worn shield on the hero's OffHand component (tag OffHand), or hides it
#   Roll         the hero's damage path calls it on every hit: LastMult = BlockMult[Worn] when RandomFloat < BlockChance[Worn],
#                else 1. The hero multiplies the damage by LastMult (one call + one multiply, README step 4).
import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, 'gen_trade.py'), encoding='utf-8').read().split('\n')
L_EV = next(i for i, l in enumerate(SRC, 1) if l.startswith('# ---------------------------------------------------------------- event + scale'))
exec('\n'.join(SRC[:L_EV - 1]))                          # imports, value helpers, Flow (gen_trade's kit)
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(REPO, 'handoffs', 'shop-v2-418', 'shields'); os.makedirs(OUT, exist_ok=True)
KITC = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_ShieldKit', 'BPC_ShieldKit')
SGC = BPC('/Game/CastleDefender/Gameplay/Castle/SG_ShieldKit', 'SG_ShieldKit')
SMC_, SM_, SG_BASE = CLS('StaticMeshComponent'), CLS('StaticMesh'), CLS('SaveGame')
SLOT = 'ShieldKit'

SHIELDS = [  # name, price, block chance, blocked-hit damage multiplier, mesh, art (turntable / icon)
    ('Round Shield',          180, 0.12, 0.50, '/Game/CastleDefender/Weapons/RoundShield/SM_RoundShield', 'RoundShield'),
    ("Knight's Heater Shield", 250, 0.15, 0.50, '/Game/CastleDefender/Weapons/HeaterShield/SM_HeaterShield', 'HeaterShield'),
    ('Gilded Shield',          450, 0.20, 0.45, '/Game/CastleDefender/Equipment/Weapons/Shield/SM_Shield', None),
]

def me(fl_, member, pins=()): return selfcall(fl_, member, pins, cls=KITC)
def selfcall(fl_, member, pins=(), cls=KITC):
    n = b.call_self(member, list(pins), *P(), cls, tag='Call' + member); fl_.go(n); return n
def setv(fl_, var, pin, src, lit=None):
    n = b.set(var, pin, None if lit is not None else src, *P())
    if lit is not None: G.nodes[-1][3][2]['default'] = lit
    fl_.go(n); return n
OWNER_ = b.name('Owner'); callfn(G, OWNER_, CLS('ActorComponent'), 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=P()[0], y=P()[1], self_hidden=True)
OWNER = (OWNER_, 'ReturnValue')
WORN = lambda: get('Worn', INT)
OFFV = ob('v', SMC_)

# ---------------------------------------------------------------- BeginPlay: find OffHand, load, apply
bpn = b.name('BeginPlay')
G.node(bpn, 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % CLS('ActorComponent'), 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % CLS('ActorComponent')}, ex('then', True)], 0, 0)
fl = Flow((bpn, 'then'))
gc = b.call(ACT, 'GetComponentsByTag', [CLSPIN('ComponentClass', CLS('ActorComponent'), '/Script/Engine.StaticMeshComponent'), NAME_('Tag', 'OffHand'),
            arr(ob('ReturnValue', CLS('ActorComponent'), out=True))], *P(), target=OWNER, pure=True, const=True, tag='FindOffHand')
cast(G, 'AsOffHand', SMC_, 'AsStatic Mesh Component', *P(), pure=True)
b.wire(b.item((gc, 'ReturnValue'), ob('v', CLS('ActorComponent')), None, *P()), 'AsOffHand', 'Object')
setv(fl, 'OffHand', OFFV, ('AsOffHand', 'AsStatic Mesh Component'))
ex_ = b.lib(GS, 'DoesSaveGameExist', [S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], *P(), pure=True, tag='HasSave')
f1, f2 = fl.iff((ex_, 'ReturnValue'), 'IfSave')
ld = b.lib(GS, 'LoadGameFromSlot', [S('SlotName', default=SLOT), it('UserIndex', default='0'), ob('ReturnValue', SG_BASE, out=True)], *P(), tag='LoadKit'); f1.go(ld)
cast(G, 'AsSG', SGC, 'AsSG Shield Kit', *P(), pure=True); b.wire((ld, 'ReturnValue'), 'AsSG', 'Object')
SGH = ('AsSG', 'AsSG Shield Kit')
fv, fnv = f1.iff(b.valid(SGH, *P()), 'IfSGValid')
setv(fv, 'Owned', INT, b.getm('Owned', SGC, INT, SGH, *P())); setv(fv, 'Worn', INT, b.getm('Worn', SGC, INT, SGH, *P()))
fl = fv.join(fnv, f2)
me(fl, 'Apply')

# ---------------------------------------------------------------- Buy(Index): the shop has paid
Y0 = 1200
b.event('Buy', [it('Index')], 0, Y0); XY[0], XY[1] = 0, Y0
fl = Flow(('Buy', 'then'))
pw = rnd(b.math('MultiplyMultiply_FloatFloat', [(D('Base', default='2.0'), None), (D('Exp', default='0.0'), i2d(('Buy', 'Index')))], D('ReturnValue', out=True), *P()))
setv(fl, 'Owned', INT, iop('Or_IntInt', get('Owned', INT), pw))
wr = me(fl, 'Wear', [it('Index', default='0')]); b.wire(('Buy', 'Index'), wr, 'Index')

# ---------------------------------------------------------------- Wear(Index): toggle / swap, owned only
Y0 = 2400
b.event('Wear', [it('Index')], 0, Y0); XY[0], XY[1] = 0, Y0
fl = Flow(('Wear', 'then'))
pw2 = rnd(b.math('MultiplyMultiply_FloatFloat', [(D('Base', default='2.0'), None), (D('Exp', default='0.0'), i2d(('Wear', 'Index')))], D('ReturnValue', out=True), *P()))
fo, fno = fl.iff(icmp('Greater_IntInt', iop('And_IntInt', get('Owned', INT), pw2), 0), 'IfOwnedW')
fsame, fother = fo.iff(icmp('EqualEqual_IntInt', WORN(), ('Wear', 'Index')), 'IfSame')
setv(fsame, 'Worn', INT, None, '-1'); setv(fother, 'Worn', INT, ('Wear', 'Index'))
fl = fsame.join(fother)
me(fl, 'Apply'); me(fl, 'SaveKit')

# ---------------------------------------------------------------- Apply: OffHand shows the worn shield
Y0 = 3600
b.event('Apply', [], 0, Y0); XY[0], XY[1] = 0, Y0
fl = Flow(('Apply', 'then'))
OFF = get('OffHand', OFFV)
fok, _ = fl.iff(b.valid(OFF, *P()), 'IfOffHand')
fw, fnw = fok.iff(icmp('GreaterEqual_IntInt', WORN(), 0), 'IfWorn')
sm = b.call(SMC_, 'SetStaticMesh', [ob('NewMesh', SM_), bo('ReturnValue', out=True, default='false')], *P(), target=OFF, tag='SetShieldMesh')
b.wire(getarr('Meshes', ob('v', SM_), WORN()), sm, 'NewMesh'); fw.go(sm)
rl = b.call(CLS('SceneComponent'), 'K2_SetRelativeLocationAndRotation', [V('NewLocation'), st('NewRotation', ROT, default='0, 0, 0'), bo('bSweep', default='false'),
            st('SweepHitResult', HITRES, out=True), bo('bTeleport', default='true')], *P(), target=OFF, tag='SetGrip')
b.wire(getarr('GripLoc', VECT, WORN()), rl, 'NewLocation'); b.wire(getarr('GripRot', st('v', ROT), WORN()), rl, 'NewRotation'); fw.go(rl)
def vis(fl_, on):
    n = b.call(CLS('SceneComponent'), 'SetVisibility', [bo('bNewVisibility', default='true' if on else 'false'), bo('bPropagateToChildren', default='false')], *P(), target=OFF,
               tag='ShowShield' if on else 'HideShield'); fl_.go(n)
vis(fw, True); vis(fnw, False)

# ---------------------------------------------------------------- Roll: block test for the hero's damage path
Y0 = 4800
b.event('Roll', [], 0, Y0); XY[0], XY[1] = 0, Y0
fl = Flow(('Roll', 'then'))
setv(fl, 'LastMult', DBL, None, '1.0')
rnd_ = b.lib(KML, 'RandomFloat', [D('ReturnValue', out=True)], *P(), pure=True, tag='BlockRoll')
hit = AND(icmp('GreaterEqual_IntInt', WORN(), 0), dcmp('Less_DoubleDouble', (rnd_, 'ReturnValue'), getarr('BlockChance', DBL, WORN())))
fh, _ = fl.iff(hit, 'IfBlocked')
setv(fh, 'LastMult', DBL, getarr('BlockMult', DBL, WORN()))

# ---------------------------------------------------------------- SaveKit
Y0 = 6000
b.event('SaveKit', [], 0, Y0); XY[0], XY[1] = 0, Y0
fl = Flow(('SaveKit', 'then'))
mk = b.lib(GS, 'CreateSaveGameObject', [CLSPIN('SaveGameClass', SG_BASE, cpath('/Game/CastleDefender/Gameplay/Castle/SG_ShieldKit')), ob('ReturnValue', SG_BASE, out=True)],
           *P(), tag='MakeSG'); fl.go(mk)
cast(G, 'AsSG2', SGC, 'AsSG Shield Kit', *P(), pure=True); b.wire((mk, 'ReturnValue'), 'AsSG2', 'Object')
SG2 = ('AsSG2', 'AsSG Shield Kit')
fl.go(b.setm('Owned', SGC, INT, get('Owned', INT), SG2, *P())); fl.go(b.setm('Worn', SGC, INT, WORN(), SG2, *P()))
sv_ = b.lib(GS, 'SaveGameToSlot', [ob('SaveGameObject', SG_BASE), S('SlotName', default=SLOT), it('UserIndex', default='0'), bo('ReturnValue', out=True, default='false')], *P(), tag='SaveSG')
b.wire((mk, 'ReturnValue'), sv_, 'SaveGameObject'); fl.go(sv_)

# ---------------------------------------------------------------- self-check + write
names = [n[0] for n in G.nodes]
assert len(names) == len(set(names)), 'duplicate node names'
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
open(os.path.join(OUT, 'BPC_ShieldKit_graph.txt'), 'w', newline='\r\n', encoding='utf-8').write(G.render())
print('BPC_ShieldKit: nodes %d, links %d' % (len(G.nodes), len(G.links)))
json.dump(dict(shields=[dict(name=n, price=p, block=bc, mult=m, mesh=me_, art=a) for n, p, bc, m, me_, a in SHIELDS], slot=SLOT),
          open(os.path.join(OUT, 'shieldkit_data.json'), 'w'), indent=1)
print('shieldkit_data.json: %d shields' % len(SHIELDS))

