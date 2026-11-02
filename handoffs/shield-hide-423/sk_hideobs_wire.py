import unreal
BEL, PIN = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary
P = '/Game/CastleDefender/Gameplay/Castle/BPC_ShieldKit'
bp = unreal.load_asset(P); eg = BEL.find_event_graph(bp)
N = {n.get_name(): n for n in unreal.ObjectIterator(unreal.K2Node) if n.get_outer() == eg}
f = lambda pre: [N[k] for k in sorted(N) if k.startswith(pre)][-1]
L = ['nodes %s' % sorted(k for k in N if k.startswith('sho'))]
own, cast, get, hide, show = f('shoOwner1'), f('shoCastHero2'), f('shoGetObs3'), f('shoHideObs4'), f('shoShowObs5')
on, off = N['vShowShield54'], N['vHideShield55']
pins = lambda n: {str(PIN.get_pin_name(p)): p for p in BEL.list_all_pins(n)}
po, pc, pg, ph, ps = pins(own), pins(cast), pins(get), pins(hide), pins(show)
L.append('cast pins %s' % list(pc)); L.append('get pins %s' % list(pg)); L.append('vis pins %s' % list(ph))
L.append(PIN.try_create_connection(po['ReturnValue'], pc['Object']))
asout = [p for k, p in pc.items() if k.startswith('As')][0]
L.append(PIN.try_create_connection(asout, pg['self']))
obs = pg['ObsidianShield']
L.append(PIN.try_create_connection(obs, ph['self'])); L.append(PIN.try_create_connection(obs, ps['self']))
for p, v in ((ph['bNewVisibility'], 'false'), (ph['bPropagateToChildren'], 'true'), (ps['bNewVisibility'], 'true'), (ps['bPropagateToChildren'], 'true')):
    PIN.set_pin_value(p, v)
# chain after the kit's own show/hide of the OffHand shield
for src, dst in ((on, ph), (off, ps)):
    t = BEL.find_then_pin(src)
    nxt = PIN.list_connected_pins(t)
    L.append('%s.then was -> %s' % (src.get_name(), [q.get_owning_node().get_name() for q in nxt]))
    for q in nxt: PIN.break_single_pin_link(t, q)
    L.append(PIN.try_create_connection(t, dst['execute']))
    for q in nxt: L.append(PIN.try_create_connection(dst['then'], q))
BEL.compile_blueprint(bp)
L.append('status %s' % bp.get_editor_property('status'))
L.append('vals %s' % [PIN.get_pin_value(p) for p in (ph['bNewVisibility'], ph['bPropagateToChildren'], ps['bNewVisibility'], ps['bPropagateToChildren'])])
L.append('saved %s' % unreal.EditorAssetLibrary.save_asset(P, False))
unreal.log_warning('SKHIDE %s' % L)
