# #184 Skill-point gain: XP-style flying sparkles in the skill-tree colour, from the hero to the skill-tree icon.
# Generates a paste for BP_SkillTreeHUD's EventGraph (one paste + 5 rewires, no new Blueprint, 3 variables).
#   python gen184.py  ->  SkillTreeHUD_SkillSplines_graph.txt + manifest.json
# How it works (inserted at the top of DrawHUD: CX_1 -> SPTickIn -> CX_2):
#   watch the hero's Level (BP_ThirdPersonCharacter.Level); when it rises, start a burst (SPT = now, SPN = levels gained)
#   for 1.4 s draw 6 T_XPGlow sprites, each a little behind the previous, flying on an arc from the hero (projected to the
#   screen, 1.2 m above the feet) to the skill-tree icon (its X/Y/W are taken from the icon's own draw node CX_2402
#   sources: CX_2396 / CX_2398 / CX_2322, via rewires), shrinking and fading, tinted violet-blue (0.55, 0.45, 1.0).
# Variables to add (VARIABLES.md): SPT (float 0), SPN (int 0), SPPrevLevel (int 0).
import os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools', 'laptop2', 'bpgen'))
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))

HUD = CLS('HUD'); TEXC = CLS('Texture')
P_HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
HERO = BPC(P_HERO, 'BP_ThirdPersonCharacter')
XPGLOW = '/Game/CastleDefender/UI/T_XPGlow.T_XPGlow'
EBLEND = '"/Script/CoreUObject.Enum\'/Script/Engine.EBlendMode\'"'
VEC2 = STRUCT('Vector2D')
G = Graph(); b = B(G, 'sp')
def pins(name): return next(n[3] for n in G.nodes if n[0] == name)

def drawtex(x, y, tag):
    n = b.call_self('DrawTexture', [
        {'name': 'Texture', 'cat': 'object', 'obj': TEXC, 'dobj': XPGLOW},
        fl('ScreenX', default='0.0'), fl('ScreenY', default='0.0'), fl('ScreenW', default='0.0'), fl('ScreenH', default='0.0'),
        fl('TextureU', default='0.0'), fl('TextureV', default='0.0'), fl('TextureUWidth', default='1.0'), fl('TextureVHeight', default='1.0'),
        st('TintColor', LC, default='(R=0.550000,G=0.450000,B=1.000000,A=1.000000)'),
        {'name': 'BlendMode', 'cat': 'byte', 'obj': EBLEND, 'default': 'BLEND_Translucent', 'advanced': True},
        fl('Scale', default='1.000000', advanced=True), dict(bo('bScalePosition', default='false'), advanced=True),
        fl('Rotation', default='0.000000', advanced=True), dict(st('RotPivot', VEC2, default='(X=0.000000,Y=0.000000)'), advanced=True)], x, y, HUD, tag=tag)
    return n

# ---- tick block ----
Y = 0
seq = b.seq('SPTickIn', 3, 0, Y)
pawn = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 250, Y + 300, pure=True, tag='Pawn')
hero = b.name('AsHero'); cast(G, hero, HERO, 'AsBP_ThirdPersonCharacter', 550, Y + 300, pure=True); b.wire((pawn, 'ReturnValue'), hero, 'Object')
lvl = b.getm('Level', HERO, INT, (hero, 'AsBP_ThirdPersonCharacter'), 850, Y + 300)
prev = b.get('SPPrevLevel', INT, 850, Y + 450)
rose = b.icmp('Greater_IntInt', lvl, prev, 1100, Y + 350)
had = b.icmp('Greater_IntInt', prev, None, 1100, Y + 500, db='0')
br = b.branch(rose, 1350, Y, 'IfLevelUp'); G.link(seq, 'then_0', br, 'execute')
br2 = b.branch(had, 1600, Y, 'IfNotFirst'); G.link(br, 'then', br2, 'execute')
now = b.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], 1600, Y + 300, pure=True, tag='Now')
s1 = b.set('SPT', DBL, (now, 'ReturnValue'), 1850, Y)
gained = b.i2('Subtract_IntInt', lvl, prev, 1850, Y + 450)
s2 = b.set('SPN', INT, gained, 2100, Y)
s3 = b.set('SPPrevLevel', INT, lvl, 2400, Y)
G.link(br2, 'then', s1, 'execute'); G.link(s1, 'then', s2, 'execute'); G.link(s2, 'then', s3, 'execute'); G.link(br2, 'else', s3, 'execute')
# ---- draw block ----
Y2 = 900
spt = b.get('SPT', DBL, 250, Y2 + 200)
el = b.d2('Subtract_DoubleDouble', (now, 'ReturnValue'), spt, 500, Y2 + 200)
live = b.b2('BooleanAND', b.dcmp('Less_DoubleDouble', el, None, 750, Y2 + 200, db='1.4'), b.dcmp('Greater_DoubleDouble', spt, None, 750, Y2 + 350, db='0.0'), 1000, Y2 + 250)
bd = b.branch(live, 1250, Y2, 'IfBurst'); G.link(seq, 'then_1', bd, 'execute')
# start = hero projected to the screen (+120 cm), end = icon centre (icon X/Y/W arrive by rewire into the Add nodes below)
hloc = b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 1250, Y2 + 500, target=(hero, 'AsBP_ThirdPersonCharacter'), pure=True, const=True, tag='HeroLoc')
hup = b.v2('Add_VectorVector', (hloc, 'ReturnValue'), None, 1500, Y2 + 500, db='0, 0, 120')
scr = b.call_self('Project', [V('Location'), V('ReturnValue', out=True)], 1750, Y2 + 500, HUD, pure=True, const=True, tag='Project'); b.wire(hup, scr, 'Location')
sc = b.brk((scr, 'ReturnValue'), 2000, Y2 + 500)
halfw = b.d2('Multiply_DoubleDouble', None, None, 1250, Y2 + 800, da='0.0', db='0.5')          # A <- CX_2322.ReturnValue (icon W) by rewire
ex = b.d2('Add_DoubleDouble', None, halfw, 1500, Y2 + 750, da='0.0')                           # A <- CX_2396.ReturnValue (icon X)
ey = b.d2('Add_DoubleDouble', None, halfw, 1500, Y2 + 900, da='0.0')                           # A <- CX_2398.ReturnValue (icon Y)
ICON_X, ICON_Y, ICON_W = ex, ey, halfw
dx = b.d2('Subtract_DoubleDouble', ex, sc['X'], 1800, Y2 + 750); dy = b.d2('Subtract_DoubleDouble', ey, sc['Y'], 1800, Y2 + 900)
prev_exec = bd; prev_pin = 'then'
for i in range(6):
    yy = Y2 + 1200 + i * 450
    ti = b.clamp(b.d2('Divide_DoubleDouble', b.d2('Subtract_DoubleDouble', el, None, 2200, yy, db=str(round(i * 0.07, 2))), None, 2450, yy, db='1.0'), '0.0', '1.0', 2700, yy)
    arc = b.math('Sin', [(D('A', default='0.0'), b.d2('Multiply_DoubleDouble', ti, None, 2700, yy + 120, db='3.14159'))], D('ReturnValue', out=True), 2950, yy + 120)
    px = b.d2('Add_DoubleDouble', sc['X'], b.d2('Multiply_DoubleDouble', dx, ti, 2950, yy - 60), 3200, yy - 60)
    py0 = b.d2('Add_DoubleDouble', sc['Y'], b.d2('Multiply_DoubleDouble', dy, ti, 2950, yy + 30), 3200, yy + 30)
    py = b.d2('Subtract_DoubleDouble', py0, b.d2('Multiply_DoubleDouble', arc, None, 3200, yy + 150, db=str(120 - i * 12)), 3450, yy + 30)
    size = b.d2('Subtract_DoubleDouble', None, b.d2('Multiply_DoubleDouble', ti, None, 3450, yy + 250, db='14.0'), 3700, yy + 250, da='28.0')
    half = b.d2('Multiply_DoubleDouble', size, None, 3950, yy + 250, db='0.5')
    n = drawtex(4300, yy - 100, 'Glow%d' % i)
    b.wire(b.d2('Subtract_DoubleDouble', px, half, 3950, yy - 60), n, 'ScreenX'); b.wire(b.d2('Subtract_DoubleDouble', py, half, 3950, yy + 60), n, 'ScreenY')
    b.wire(size, n, 'ScreenW'); b.wire(size, n, 'ScreenH')
    G.link(prev_exec, prev_pin, n, 'execute'); prev_exec, prev_pin = n, 'then'

open(os.path.join(HERE, 'SkillTreeHUD_SkillSplines_graph.txt'), 'w', encoding='utf-8').write(G.render())
import json
json.dump({'blueprint': 'BP_SkillTreeHUD', 'pastes': ['SkillTreeHUD_SkillSplines_graph.txt'], 'rewires': [
  {'from': 'CX_1.then', 'to': 'SPTickIn.execute', 'replace': True, 'note': 'DrawHUD -> sparkle tick first'},
  {'from': 'SPTickIn.then_2', 'to': 'CX_2.execute', 'note': 'then the original DrawHUD chain'},
  {'from': 'CX_2396.ReturnValue', 'to': ICON_X[0] + '.A', 'note': 'skill icon ScreenX source'},
  {'from': 'CX_2398.ReturnValue', 'to': ICON_Y[0] + '.A', 'note': 'skill icon ScreenY source'},
  {'from': 'CX_2322.ReturnValue', 'to': ICON_W[0] + '.A', 'note': 'skill icon size source'}]},
  open(os.path.join(HERE, 'manifest.json'), 'w'), indent=1)
print('wrote', len(G.nodes), 'nodes', len(G.links), 'links; icon rewires ->', ICON_X[0], ICON_Y[0], ICON_W[0])
