# Obsidian complete set as an activatable skill, card #477 (i5, 2026-11-03). Design + decisions: DESIGN.md.
#   python gen_ember.py   -> ember_paste.txt + ember_manifest.json (then applyall merge on a fresh export, see README.md)
# At 4/4 the shockwave fires on EmberKey (default 7) with a cooldown instead of automatically on hit. Tier 3 keeps its on-hit shock
# (same ShockReadyAt, so taking a bundle off cannot dodge the cooldown). DR -15 % and embers stay passive. Save format unchanged.
# Hook: DrawArmoury (called every DrawHUD by BP_ArmoryHUD, skipped while Vesna covers the screen) -> Sequence -> DrawEmberSkill, then the old body.
import json, os, sys
_ME = os.path.dirname(os.path.abspath(__file__))
_pot = os.path.join(_ME, '..', 'potion-polish-1102', 'gen_potion_polish.py')
_src = open(_pot, encoding='utf-8').read()
_src = _src[:_src.index('# ---------------------------------------------------------------- event, viewport, time')]   # all the helpers
__file__ = _pot
exec(compile(_src, 'gen_potion-preamble', 'exec'))
HERE = _ME
G = Graph(); b = B(G, 'emb'); XY[0], XY[1] = 0, 300
KISL, KTXL = "\"/Script/CoreUObject.Class'/Script/Engine.KismetInputLibrary'\"", "\"/Script/CoreUObject.Class'/Script/Engine.KismetTextLibrary'\""
INTV_ = it('v', default='0')
KEYV = st('v', KEY)
SET = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet', 'BPC_ObsidianSet')

# ---- the event (paste is self-contained, so the same file works on set v3 and v4)
b.event('DrawEmberSkill', [ob('Hud', HUDC), it('SizeX', default='0'), it('SizeY', default='0')], 0, 0)
hud = ('DrawEmberSkill', 'Hud')
fl0 = Flow(('DrawEmberSkill', 'then'))
paused = b.lib(GS, 'IsGamePaused', [WC(), bo('ReturnValue', out=True, default='false')], *P(), pure=True, tag='Paused')
tier = lambda: get('Tier', INTV_)
f, _off = fl0.iff(AND(icmp('EqualEqual_IntInt', tier(), 4), NOT((paused, 'ReturnValue'))), 'IfComplete')
pcn = b.call(HUDC, 'GetOwningPlayerController', [ob('ReturnValue', PCON, out=True)], *P(), target=hud, pure=True, const=True, tag='PC')
SXd, SYd = i2d(('DrawEmberSkill', 'SizeX')), i2d(('DrawEmberSkill', 'SizeY'))
U = dop('Divide_DoubleDouble', SYd, 1080.0)
def px(v): return dop('Multiply_DoubleDouble', U, float(v) if isnum(v) else v)
now_ = b.lib(GS, 'GetTimeSeconds', [WC(), D('ReturnValue', out=True)], *P(), pure=True, tag='GameNow'); NOW = (now_, 'ReturnValue')

# ---- badge MID, created once
fm, fhas = f.iff(NOT(b.valid(get('EmberMID', MIDV), *P())), 'IfNoMID')
cm = b.lib(MATL, 'CreateDynamicMaterialInstance', [WC(), ob('Parent', CLS('MaterialInterface')), NAME_('OptionalName', 'None'),
           {'name': 'CreationFlags', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.EMIDCreationFlags\'"', 'default': 'None'},
           ob('ReturnValue', MIDC, out=True)], *P(), tag='MakeMID')
b.wire(get('EmberMat', MATV_), cm, 'Parent')
fm.go(cm)
setvar(fm, 'EmberMID', MIDV, (cm, 'ReturnValue'))
ti = b.call(MIDC, 'SetTextureParameterValue', [NAME_('ParameterName', 'Icon'), ob('Value', CLS('Texture'))], *P(), target=get('EmberMID', MIDV), tag='MidIcon')
b.wire(get('EmberIcon', TEXV), ti, 'Value'); fm.go(ti)
f1 = fm.join(fhas)
# the key path may end in the live flare chain, so key and draw hang off a Sequence
SEQ2 = b.name('SeqDraw'); b.seq(SEQ2, 2, *P())
f1.go(SEQ2)
fkey = Flow((SEQ2, 'then_0'))

# ---- key: fire or refuse
KEYN = b.call(PCON, 'WasInputKeyJustPressed', [st('Key', KEY), bo('ReturnValue', out=True, default='false')], *P(), target=(pcn, 'ReturnValue'), pure=True, const=True, tag='Key')
b.wire(get('EmberKey', KEYV), KEYN, 'Key')
pp = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], *P(), pure=True, tag='Pawn')
cast(G, 'embAsHero', HERO, 'AsBP Third Person Character', *P()); b.wire((pp, 'ReturnValue'), 'embAsHero', 'Object')
HEROH = ('embAsHero', 'AsBP Third Person Character')
DEAD = b.getm('IsDead', HERO, bo('v', default='false'), HEROH, *P())
fk, fnk = fkey.iff((KEYN, 'ReturnValue'), 'IfKey')
fk.go('embAsHero')                                      # impure cast: the Python graph editor has no pure-cast node
READY = dcmp('GreaterEqual_DoubleDouble', NOW, dget('ShockReadyAt'))
fy, fr = fk.iff(AND(READY, NOT(DEAD)), 'IfReady')
setvar(fy, 'ShockReadyAt', DBLV, add(NOW, dget('EmberCooldown')))
PUSH = b.call_self('PushZombies', [D('Radius', default='0.0'), D('Damage', default='0.0'), D('Push', default='900.000000')], *P(), cls=SET, tag='CallPush')
b.wire(dget('EmberRadius'), PUSH, 'Radius'); b.wire(dget('EmberDamage'), PUSH, 'Damage')
fy.go(PUSH)                                             # manifest: PUSH.then -> the live flare chain (oGetObsSet480)
setvar(fr, 'EmberRefuseAt', DBLV, NOW)
sound(fr, SND_FAIL, '0.5')

# ---- badge: sweep = cooldown left, ring flash on refuse, key cap from the key's own name
XY[0], XY[1] = 6000, 300
cool = clamp01(dop('Divide_DoubleDouble', sub(dget('ShockReadyAt'), NOW), dmax(dget('EmberCooldown'), 0.1)))
refuse = one_minus(ramp(sub(NOW, dget('EmberRefuseAt')), 0.0, 0.4))
def mv(fl_, pname, color):
    n = b.call(MIDC, 'SetVectorParameterValue', [NAME_('ParameterName', pname), st('Value', LC, default=WHITE)], *P(), target=get('EmberMID', MIDV), tag='MidSet')
    b.wire(color, n, 'Value'); fl_.go(n)
fd = Flow((SEQ2, 'then_1'))
mv(fd, 'Pot', mcol(cool, 0.0, 0.0, dmax(refuse, 0.001)))
mv(fd, 'Pot2', mcol(0.0, 0.0, 0.0, 1.0))
X, Y = mul(SXd, dget('EmberX')), mul(SYd, dget('EmberY'))
BQ = 84.0
dm = b.call(HUDC, 'DrawMaterial', [ob('Material', CLS('MaterialInterface')), F('ScreenX'), F('ScreenY'), F('ScreenW'), F('ScreenH'), F('MaterialU'), F('MaterialV'),
            F('MaterialUWidth', default='1.0'), F('MaterialVHeight', default='1.0'), F('Scale', default='1.0'), bo('bScalePosition', default='false'),
            F('Rotation'), st('RotPivot', V2D, default='(X=0.500000,Y=0.500000)')], *P(), target=hud, tag='Badge')
b.wire(get('EmberMID', MIDV), dm, 'Material')
for pin, v in (('ScreenX', sub(X, px(BQ / 2))), ('ScreenY', sub(Y, px(BQ / 2))), ('ScreenW', px(BQ)), ('ScreenH', px(BQ))): b.wire(v, dm, pin)
fd.go(dm)
kn = b.lib(KISL, 'Key_GetDisplayName', [st('Key', KEY), bo('bLongDisplayName', default='true'), {'name': 'ReturnValue', 'cat': 'text', 'out': True}], *P(), pure=True, tag='KeyName')
b.wire(get('EmberKey', KEYV), kn, 'Key')
ks = b.lib(KTXL, 'Conv_TextToString', [{'name': 'InText', 'cat': 'text'}, S('ReturnValue', out=True)], *P(), pure=True, tag='KeyStr')
b.wire((kn, 'ReturnValue'), ks, 'InText')
FH = b.call(HUDC, 'GetTextSize', [S('Text', default='0'), F('OutWidth', out=True), F('OutHeight', out=True), dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0')], *P(), target=hud, pure=True, const=True, tag='FontH')
dt_ = b.call(HUDC, 'DrawText', [S('Text', default=''), st('TextColor', LC, default=WHITE), F('ScreenX'), F('ScreenY'), dict(ob('Font', FONTC), dobj=FONT), F('Scale', default='1.0'), bo('bScalePosition', default='false')], *P(), target=hud, tag='KeyCap')
b.wire((ks, 'ReturnValue'), dt_, 'Text'); b.wire(mcol(0.98, 0.86, 0.56, 1.0), dt_, 'TextColor')
b.wire(dop('Divide_DoubleDouble', px(18.0), (FH, 'OutHeight')), dt_, 'Scale')
b.wire(sub(X, px(38.0)), dt_, 'ScreenX'); b.wire(sub(Y, px(42.0)), dt_, 'ScreenY')
fd.go(dt_)

# ---- hook + tier-3 condition
XY[0], XY[1] = 0, -700
SEQ = b.name('Seq'); b.seq(SEQ, 2, *P())
CALL = b.call_self('DrawEmberSkill', [ob('Hud', HUDC), it('SizeX', default='0'), it('SizeY', default='0')], *P(), cls=SET, tag='CallDraw')
G.link(SEQ, 'then_0', CALL, 'execute')
T3 = icmp('EqualEqual_IntInt', tier(), 3)

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links %s' % bad)
open(os.path.join(HERE, 'ember_paste.txt'), 'w', newline='\r\n').write(G.render()); print('paste', len(G.nodes), 'nodes', len(G.links), 'links')
json.dump({'blueprint': 'BPC_ObsidianSet', 'note': '#477 complete set shockwave on a key', 'pastes': ['ember_paste.txt'],
           'rewires': [{'from': 'DrawArmoury.then', 'to': SEQ + '.execute', 'replace': True, 'note': 'was -> oGetShop528'},
                       {'from': SEQ + '.then_1', 'to': 'oGetShop528.execute', 'replace': True},
                       {'from': 'DrawArmoury.Hud', 'to': CALL + '.Hud'}, {'from': 'DrawArmoury.SizeX', 'to': CALL + '.SizeX'}, {'from': 'DrawArmoury.SizeY', 'to': CALL + '.SizeY'},
                       {'from': PUSH + '.then', 'to': 'oGetObsSet480.execute', 'note': 'same flare as the on-hit shock'},
                       {'from': T3[0] + '.' + T3[1], 'to': 'oBooleanAND468.A', 'replace': True, 'note': 'on-hit shock now only at tier 3 (was Tier >= 3)'}]},
          open(os.path.join(HERE, 'ember_manifest.json'), 'w'), indent=1)
