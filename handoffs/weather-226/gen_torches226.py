# #226 follow-up (adjustedfilm, 2026-10-31): heavy rain at night puts out torches.
#   "<blender python>" -I gen_torches226.py -> Weather_Torches_graph.txt + manifest_weather_torches.json (+ 1 BPVar line)
# On BPC_Weather's free WxSeq.then_4: Doused target = BP_DayNight.IsNight AND CurRain > 0.6. Only when it changes:
#   doused  -> 2 of every 3 actors tagged NightLight (BP_DayNight's torch tag) are hidden (every third keeps burning: under
#              eaves and in the gatehouse), notice "The rain puts out the torches."
#   back    -> all NightLight actors shown again if it is still night (BP_DayNight hides them itself at dawn).
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
G = Graph(); b = bpkit.B(G, 'wt')
g = b.get
dn = lambda x, y: g('DN', ob('v', DNC), x, y)
vd = b.branch(b.valid(dn(0, 300), 150, 300), 200, 0, tag='TorchIfDN')
night = b.getm('IsNight', DNC, BOOL, dn(200, 450), 350, 450)
tgt = b.b2('BooleanAND', night, b.dcmp('Greater_DoubleDouble', g('CurRain', DBL, 350, 600), None, 550, 600, db='0.6'), 750, 500)
ch = b.branch(b.math('NotEqual_BoolBool', [(bo('A', default='false'), tgt), (bo('B', default='false'), g('Doused', BOOL, 750, 650))], bo('ReturnValue', out=True), 950, 600), 500, 0, tag='IfTorchChange')
G.link(vd, 'then', ch, 'execute')
sd = b.set('Doused', BOOL, tgt, 800, 0); G.link(ch, 'then', sd, 'execute')
ga = b.lib(GS, 'GetAllActorsWithTag', [WC(), {'name': 'Tag', 'cat': 'name', 'default': 'NightLight'}, arr(ob('OutActors', ACT, out=True))], 1050, 0, tag='FindTorches')
G.link(sd, 'then', ga, 'execute')
fe = b.foreach(ACT, 1400, 0); G.link(ga, 'then', fe, 'Exec'); b.wire((ga, 'OutActors'), fe, 'Array')
keep = b.icmp('EqualEqual_IntInt', b.i2('Percent_IntInt', (fe, 'Array Index'), None, 1500, 400, db='3'), None, 1700, 400, db='0')
hide = b.b2('BooleanAND', g('Doused', BOOL, 1700, 500), b.bnot(keep, 1900, 400), 2100, 450)
sh = b.call(ACT, 'SetActorHiddenInGame', [bo('bNewHidden', default='false')], 1800, 0, target=(fe, 'Array Element'), tag='DouseTorch')
b.wire(hide, sh, 'bNewHidden'); G.link(fe, 'LoopBody', sh, 'execute')
bn = b.branch(g('Doused', BOOL, 1800, 300), 1900, 200, tag='IfDousedNow'); G.link(fe, 'Completed', bn, 'execute')
pcn = b.lib(GS, 'GetPlayerController', [WC(), it('PlayerIndex', default='0'), ob('ReturnValue', PCON, out=True)], 1900, 600, pure=True, tag='PC')
hud = b.call(PCON, 'GetHUD', [ob('ReturnValue', CLS('HUD'), out=True)], 2100, 600, target=(pcn, 'ReturnValue'), pure=True, const=True, tag='HUD')
nc = b.name('AsNoticeHUD'); cast(G, nc, NOTC, 'AsBP Notice HUD', 2200, 200); b.wire((hud, 'ReturnValue'), nc, 'Object'); G.link(bn, 'then', nc, 'execute')
pn = b.call(NOTC, 'PushNotice', [S('Text', default='The rain puts out the torches.'), it('Tier', default='1')], 2500, 200, target=(nc, 'AsBP Notice HUD'), tag='Notice')
G.link(nc, 'then', pn, 'execute')
pins = {(n[0], p['name']) for n in G.nodes for p in n[3]}
assert not [l for l in G.links if (l[0], l[1]) not in pins or (l[2], l[3]) not in pins]
open(os.path.join(HERE, 'Weather_Torches_graph.txt'), 'w', newline='\r\n').write(G.render())
json.dump({'blueprint': 'BPC_Weather', '_built_on': 'handoffs/weather-226/BPC_Weather_graph.txt (#275; export it after pasting)',
           'pastes': [{'file': 'Weather_Torches_graph.txt', 'offset': [0, 6200]}],
           'rewires': [{'from': 'WxSeq.then_4', 'to': vd + '.execute', 'note': 'the free 5th output of the weather tick'}]},
          open(os.path.join(HERE, 'manifest_weather_torches.json'), 'w'), indent=1)
open(os.path.join(HERE, 'VARIABLES_Torches_BPVar.txt'), 'w', newline='\r\n').write(
    '# BPC_Weather - one more variable for the torches add-on\nBPVar(VarName="Doused",VarGuid=%s,VarType=(PinCategory="bool"),FriendlyName="Doused",Category=NSLOCTEXT("KismetSchema", "Default", "Default"),PropertyFlags=5,DefaultValue="false")\n'
    % uuid.uuid5(uuid.NAMESPACE_URL, 'weather226/Doused').hex.upper())
print('Weather_Torches: nodes %d, links %d' % (len(G.nodes), len(G.links)))
