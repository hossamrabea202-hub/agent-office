# #487 E2 (i5, read-only): where do the event tick and the zombie scan of BP_ZombieVariety, BP_JellyShieldAll and BP_HitFeel wire to,
# in the LIVE graph. Prints links of CX_1 (tick) and CX_2 (GetAllActorsOfClass); changes nothing.
import unreal
BEL, PL, GE = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
for p in ('/Game/CastleDefender/Characters/Enemies/Zombie/BP_ZombieVariety', '/Game/CastleDefender/Gameplay/Tentacle/Jelly/BP_JellyShieldAll',
          '/Game/CastleDefender/Gameplay/Polish/BP_HitFeel'):
    bp = unreal.load_asset(p); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); live = {n.get_name(): n for n in ge.list_all_nodes()}
    print('==', p.split('/')[-1], len(live), 'nodes')
    for nm in ('CX_1', 'CX_2'):
        n = live.get(nm)
        if not n: print(' ', nm, 'MISSING'); continue
        for pn in PL.get_pins(n) if hasattr(PL, 'get_pins') else []:
            pass
        for pin_name in ('then', 'execute', 'OutActors', 'DeltaSeconds'):
            for out in (True, False):
                q = BEL.find_output_pin(n, pin_name) if out else BEL.find_input_pin(n, pin_name)
                if q and PL.is_valid(q):
                    print(' ', nm, pin_name, 'out' if out else 'in', '->', [(PL.get_owning_node(x).get_name(), (PL.get_pin_name(x) if hasattr(PL, "get_pin_name") else str(x)[-60:])) for x in PL.list_connected_pins(q)])
