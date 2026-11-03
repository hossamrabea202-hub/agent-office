# #450 / #457 (i5, 2026-11-03). ABP_TentacleStrikePP runs on every tentacle (it is the skeletal mesh's post-process AnimBP), but its Local Pose has NO
# Input Pose wired, so it outputs the reference pose: tested on a probe in Simulate, seg_13 did not move at all while the clip's position ran, and it
# moved as soon as the post-process ABP was disabled. So the idle clips never reach the screen. This adds Input Pose -> Slot 'DefaultSlot' -> Local Pose.
# The slot is what the hit reaction montage plays in. UE 5.8 graph editing from Python: no paste needed. Run with the editor idle, not in Play.
#   py fix_pp_input_ue.py --dry-run | --apply | --revert        (--abp <asset path>: i5 tests on a temporary copy)
import sys, unreal
A = sys.argv[1:]
PATH = A[A.index('--abp') + 1] if '--abp' in A else '/Game/CastleDefender/Gameplay/Tentacle/ABP_TentacleStrikePP'
BEL, PL, GE = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor_by_name(bp, 'AnimGraph')
nodes = {n.get_name(): n for n in ge.list_all_nodes()}
ltc = nodes.get('AnimGraphNode_LocalToComponentSpace_0')
if not ltc: raise SystemExit('LocalToComponentSpace node not found: ' + str(sorted(nodes)))
local = BEL.find_input_pin(ltc, 'LocalPose')
now = ['%s.%s' % (PL.get_owning_node(p).get_name(), PL.get_pin_name(p)) for p in PL.list_connected_pins(local)]
print('Local Pose is linked to:', now or 'NOTHING')
added = [n for name, n in nodes.items() if 'LinkedInputPose' in name or 'AnimGraphNode_Slot' in name]
if '--revert' in A:
    if added: ge.remove_nodes(added); BEL.compile_blueprint(bp); unreal.EditorAssetLibrary.save_asset(PATH, only_if_is_dirty=False); print('removed', len(added), 'nodes, compiled, saved')
    raise SystemExit
if now: print('already wired, nothing to do'); raise SystemExit
if '--apply' not in A: print('WOULD add Input Pose + Slot and wire them into Local Pose'); raise SystemExit
pos = BEL.get_node_pos(ltc)
ip = ge.create_node_from_name('Animation|LinkedAnimGraphs|InputPose', unreal.Vector2D(pos.x - 700, pos.y), [])
sl = ge.create_node_from_name("Animation|Montage|Slot'DefaultSlot'", unreal.Vector2D(pos.x - 350, pos.y), [])
print('link pose -> slot', PL.try_create_connection(BEL.find_output_pin(ip, 'Pose'), BEL.find_input_pin(sl, 'Source')))
print('link slot -> local', PL.try_create_connection(BEL.find_output_pin(sl, 'Pose'), local))
print('compile', BEL.compile_blueprint(bp), 'errors', [n.get_name() for n in ge.list_nodes_with_errors()])
print('saved', unreal.EditorAssetLibrary.save_asset(PATH, only_if_is_dirty=False))
