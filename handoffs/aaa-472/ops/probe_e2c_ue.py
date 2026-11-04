# #487 E2 part 2 (i5, read-only): which output pins of H297 / H296 feed H2128's exec in the live BP_ZombieHUD.
import unreal
BEL, PL, GE = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
bp = unreal.load_asset('/Game/CastleDefender/Gameplay/Castle/BP_ZombieHUD'); ge = GE.get_graph_editor(BEL.find_event_graph(bp))
live = {n.get_name(): n for n in ge.list_all_nodes()}
for nm in ('K2Node_CallFunction_H297', 'K2Node_IfThenElse_H296'):
    for pn in ('then', 'else', 'Completed'):
        q = BEL.find_output_pin(live[nm], pn)
        if q and PL.is_valid(q): print(nm, pn, '->', [PL.get_owning_node(x).get_name() for x in PL.list_connected_pins(q)])
