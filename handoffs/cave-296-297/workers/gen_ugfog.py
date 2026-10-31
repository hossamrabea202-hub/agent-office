# #341 fix (adjustedfilm, 2026-10-31): the global ExponentialHeightFog is a solid wall 50 m underground. BP_UndergroundFog
# (one placed actor): every 0.5 s, hero below DepthZ (-2500 cm) -> the height fog is hidden; back up -> shown again.
# Only acts when the state changes.   "<blender python>" -I gen_ugfog.py -> BP_UndergroundFog_graph.txt (+ BPVar lines)
import os, sys, uuid
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'laptop2', 'bpgen'))
import bpkit
from bpkit import *
HERE = os.path.dirname(os.path.abspath(__file__))
FOGA, FOGC = CLS('ExponentialHeightFog'), CLS('ExponentialHeightFogComponent')
G = Graph(); b = bpkit.B(G, 'uf'); g = b.get
b.override('ufBegin', 'ReceiveBeginPlay', 0, 0)
fa = b.lib(GS, 'GetActorOfClass', [WC(), CLSPIN('ActorClass', ACT, '/Script/Engine.ExponentialHeightFog'), ob('ReturnValue', FOGA, out=True)], 300, 0, tag='FindFog')
G.link('ufBegin', 'then', fa, 'execute')
fc = b.getm('Component', FOGA, ob('v', FOGC), (fa, 'ReturnValue'), 550, 250)
sf = b.set('Fog', ob('v', FOGC), fc, 700, 0); G.link(fa, 'then', sf, 'execute')
tm = b.timer('Poll', 1000, 0, dtime='0.5', loop=True); b.wire(b.self_node(850, 200), tm, 'Object'); G.link(sf, 'then', tm, 'execute')
b.event('Poll', [], 0, 600)
hero = b.lib(GS, 'GetPlayerPawn', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PAWN, out=True)], 100, 900, pure=True, tag='Hero')
hz = b.brk(b.call(ACT, 'K2_GetActorLocation', [V('ReturnValue', out=True)], 300, 900, target=(hero, 'ReturnValue'), pure=True, const=True, tag='HeroLoc') and ('ufHeroLoc%d' % b.n, 'ReturnValue'), 500, 900)
under = b.b2('BooleanAND', b.valid((hero, 'ReturnValue'), 500, 1050), b.dcmp('Less_DoubleDouble', hz['Z'], g('DepthZ', DBL, 600, 1150), 800, 1000), 1000, 1000)
ch = b.branch(b.b2('BooleanAND', b.math('NotEqual_BoolBool', [(bo('A', default='false'), under), (bo('B', default='false'), g('Under', BOOL, 1000, 1150))], bo('ReturnValue', out=True), 1200, 1050),
                   b.valid(g('Fog', ob('v', FOGC), 1200, 1200), 1300, 1200), 1400, 1100), 300, 600, tag='IfChange')
G.link('Poll', 'then', ch, 'execute')
su = b.set('Under', BOOL, under, 600, 600); G.link(ch, 'then', su, 'execute')
vis = b.call(SCENE, 'SetVisibility', [bo('bNewVisibility', default='true'), bo('bPropagateToChildren', default='false')], 900, 600, target=g('Fog', ob('v', FOGC), 800, 800), tag='FogOnOff')
b.wire(b.bnot(g('Under', BOOL, 800, 900), 950, 900), vis, 'bNewVisibility'); G.link(su, 'then', vis, 'execute')
open(os.path.join(HERE, 'BP_UndergroundFog_graph.txt'), 'w', newline='\r\n').write(G.render())
bpv = lambda n, t, d: 'BPVar(VarName="%s",VarGuid=%s,VarType=(%s),FriendlyName="%s",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="%s")' % (n, uuid.uuid5(uuid.NAMESPACE_URL, 'ugfog/' + n).hex.upper(), t, n, d)
open(os.path.join(HERE, 'BP_UndergroundFog_BPVar.txt'), 'w', newline='\r\n').write('# BP_UndergroundFog - paste on the VARIABLES header, then Compile\n' + '\n'.join([
    bpv('Fog', 'PinCategory="object",PinSubCategoryObject="/Script/CoreUObject.Class\'/Script/Engine.ExponentialHeightFogComponent\'"', ''),
    bpv('Under', 'PinCategory="bool"', 'false'), bpv('DepthZ', 'PinCategory="real",PinSubCategory="double"', '-2500.0')]) + '\n')
print('nodes %d links %d' % (len(G.nodes), len(G.links)))
