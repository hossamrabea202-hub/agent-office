# #141 infection look (checkking, 2026-10-30): an add-on for BPC_MotionFX, applied AFTER #148 (BPC_Infection) is in.
#   python gen_infectionfx.py  ->  MotionFX_Infection_graph.txt  (merged into BPC_MotionFX by manifest_motionfx_141.json:
#                                  DrawReveal's RevealSeq.then_2 -> CallDrawInfection, Hud/SizeX/SizeY passed through)
# #148 already turns the health bar green with a pulsing border. This adds, while the hero is infected:
#   - green toxic clouds at the screen edges (T_FX_ToxinVignette), two layers swaying against each other (confusion),
#     breathing at 0.33 Hz and flaring on every 2 s drain tick (pain): synced to BPC_Infection.InfectedAt
#   - toxin veins (T_FX_ToxinVeins) creeping out from the health bar, growing over 20 s, pulsing with the ticks
#   - 2.5 s fade-in from the moment of infection (real-time clock, so it holds while paused)
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_motionfx as gm          # builds the reveal graph on import (writes BPC_MotionFX_graph.txt again: same content)
from gen_motionfx import *

INF = BPC('/Game/CastleDefender/Gameplay/Castle/BPC_Infection', 'BPC_Infection')
G = Graph(); b = B2(G, 'i')
X, Y = 0, 0
b.event('DrawInfection', [ob('Hud', HUDC), it('SizeX'), it('SizeY')], X, Y)
hud = ('DrawInfection', 'Hud')
# the call the manifest wires from DrawReveal's sequence (fixed name; bSelfContext, see Master gotcha 1)
G.node('CallDrawInfection', 'K2Node_CallFunction', ['FunctionReference=(MemberName="DrawInfection",bSelfContext=True)'],
       [ex(), ex('then', True), selfpin(SELF, hidden=True), ob('Hud', HUDC), it('SizeX', default='0'), it('SizeY', default='0')], X - 400, Y - 300)
sxd, syd = b.i2d(('DrawInfection', 'SizeX'), X + 200, Y + 300), b.i2d(('DrawInfection', 'SizeY'), X + 200, Y + 400)
own = b.name('Owner'); callfn(G, own, COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=X, y=Y + 600, self_hidden=True)
ic = b.call(ACT, 'GetComponentByClass', [CLSPIN('ComponentClass', COMP, '/Game/CastleDefender/Gameplay/Castle/BPC_Infection.BPC_Infection_C'),
            ob('ReturnValue', INF, out=True)], X + 250, Y + 600, target=(own, 'ReturnValue'), pure=True, const=True, tag='InfComp')
icv = (ic, 'ReturnValue')
bv = b.branch(b.valid(icv, X + 500, Y + 600), X + 300, Y, tag='IfInfComp'); G.link('DrawInfection', 'then', bv, 'execute')
inf = b.getm('Infected', INF, bo('v', default='false'), icv, X + 600, Y + 750)
bi = b.branch(inf, X + 600, Y, tag='IfInfected'); G.link(bv, 'then', bi, 'execute')
off = b.set('InfT0', DBL, None, X + 900, Y + 300); G.link(bi, 'else', off, 'execute')          # cured: reset
rt = b.lib(GS, 'GetRealTimeSeconds', [WC(), D('ReturnValue', out=True)], X + 700, Y + 900, pure=True, tag='RealNow'); rnow = (rt, 'ReturnValue')
first = b.branch(b.dcmp('LessEqual_DoubleDouble', b.get('InfT0', DBL, X + 800, Y + 1050), None, X + 1000, Y + 1050, db='0.0'), X + 900, Y, tag='IfInfStart')
G.link(bi, 'then', first, 'execute')
s0 = b.set('InfT0', DBL, rnow, X + 1200, Y - 200); G.link(first, 'then', s0, 'execute')
seq = b.seq('InfSeq', 1, X + 1500, Y); G.link(first, 'else', seq, 'execute'); G.link(s0, 'then', seq, 'execute')
t = b.sub(rnow, b.get('InfT0', DBL, X + 1100, Y + 1200), X + 1300, Y + 1200)
ramp = b.lin(t, 0.0, 2.5, X + 1300, Y + 1350)
gnow = b.now(X + 1100, Y + 1500)
ph = b.d2('Divide_DoubleDouble', b.sub(gnow, b.getm('InfectedAt', INF, DBL, icv, X + 1100, Y + 1650), X + 1300, Y + 1550), None, X + 1500, Y + 1550, db='2.0')
frac = b.math('Fraction', [(D('A', default='0.0'), ph)], D('ReturnValue', out=True), X + 1700, Y + 1550)
p1 = b.sub(None, frac, X + 1900, Y + 1550, da='1.0')
pulse = b.mul(b.mul(p1, p1, X + 2100, Y + 1550), b.mul(p1, p1, X + 2100, Y + 1650), X + 2300, Y + 1600)      # (1 - frac)^4
breathe = b.add(b.mul(b.math('Sin', [(D('A', default='0.0'), b.mul(rnow, None, X + 1900, Y + 1800, db='2.1'))], D('ReturnValue', out=True), X + 2100, Y + 1800),
                      None, X + 2300, Y + 1800, db='0.5'), None, X + 2500, Y + 1800, db='0.5')
va = b.mul(ramp, b.add(b.add(b.mul(breathe, None, X + 2500, Y + 1950, db='0.12'), b.mul(pulse, None, X + 2500, Y + 2050, db='0.35'), X + 2700, Y + 2000), None, X + 2900, Y + 2000, db='0.38'), X + 3100, Y + 1950)
sway1 = b.mul(b.math('Sin', [(D('A', default='0.0'), b.mul(rnow, None, X + 2700, Y + 2200, db='0.7'))], D('ReturnValue', out=True), X + 2900, Y + 2200), None, X + 3100, Y + 2200, db='1.2')
sway2 = b.mul(b.math('Sin', [(D('A', default='0.0'), b.mul(rnow, None, X + 2700, Y + 2350, db='0.53'))], D('ReturnValue', out=True), X + 2900, Y + 2350), None, X + 3100, Y + 2350, db='-1.6')
v1 = b.tex(hud, 'T_FX_ToxinVignette.T_FX_ToxinVignette', None, None, sxd, syd, b.colr(None, None, None, va, X + 3300, Y + 1950), X + 1800, Y, rot=sway1, tag='Vignette1')
G.link(seq, 'then_0', v1, 'execute')
ow, oh = b.mul(sxd, None, X + 3300, Y + 2450, db='1.06'), b.mul(syd, None, X + 3300, Y + 2550, db='1.06')
v2 = b.tex(hud, 'T_FX_ToxinVignette.T_FX_ToxinVignette', b.mul(sxd, None, X + 3500, Y + 2450, db='-0.03'), b.mul(syd, None, X + 3500, Y + 2550, db='-0.03'),
           ow, oh, b.colr(None, None, None, b.mul(va, None, X + 3500, Y + 2650, db='0.5'), X + 3700, Y + 2650), X + 2100, Y, rot=sway2, tag='Vignette2')
G.link(v1, 'then', v2, 'execute')
# veins around the hero bar (BP_ZombieHUD geometry, as in #148: U = SizeX x 0.1365, frame at (0.43175 SizeX, 0.91 SizeY), height U x 0.16412)
u = b.mul(sxd, None, X + 3300, Y + 2900, db='0.1365')
bcx = b.add(b.mul(sxd, None, X + 3300, Y + 3000, db='0.43175'), b.mul(u, None, X + 3500, Y + 2900, db='0.5'), X + 3700, Y + 2950)
bcy = b.add(b.mul(syd, None, X + 3300, Y + 3100, db='0.91'), b.mul(u, None, X + 3500, Y + 3100, db='0.08206'), X + 3700, Y + 3100)
spread = b.add(b.mul(b.lin(t, 0.0, 20.0, X + 3500, Y + 3250), None, X + 3900, Y + 3250, db='0.7'), None, X + 4100, Y + 3250, db='1.1')
vw = b.mul(b.mul(u, None, X + 3900, Y + 3400, db='1.9'), spread, X + 4100, Y + 3400)
vh = b.mul(vw, None, X + 4300, Y + 3400, db='0.25')
vx, vy = b.sub(bcx, b.mul(vw, None, X + 4300, Y + 3550, db='0.5'), X + 4500, Y + 3550), b.sub(bcy, b.mul(vh, None, X + 4300, Y + 3650, db='0.5'), X + 4500, Y + 3650)
vna = b.mul(ramp, b.add(b.mul(pulse, None, X + 4300, Y + 3800, db='0.45'), None, X + 4500, Y + 3800, db='0.55'), X + 4700, Y + 3800)
vn = b.tex(hud, 'T_FX_ToxinVeins.T_FX_ToxinVeins', vx, vy, vw, vh, b.colr(None, None, None, vna, X + 4900, Y + 3800), X + 2400, Y, tag='Veins')
G.link(v2, 'then', vn, 'execute')

pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
bad = [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
if bad: raise SystemExit('bad links: %s' % bad[:10])
open(os.path.join(HERE, 'MotionFX_Infection_graph.txt'), 'w', newline='\r\n').write(G.render())
print('MotionFX infection add-on: nodes %d, links %d' % (len(G.nodes), len(G.links)))
