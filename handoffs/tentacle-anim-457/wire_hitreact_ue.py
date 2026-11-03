# #450 phase 2 (i5, 2026-11-03): a hit plays AS_Tentacle_HitReact450 as a montage in the post-process ABP's slot, over the idle clip, at most once per 2.5 s.
# RUN fix_pp_input_ue.py FIRST: without its slot the montage does not show. UE 5.8 graph editing from Python: no paste. Editor idle, not in Play.
#   py wire_hitreact_ue.py --dry-run | --apply | --revert        (--bpc <asset path>: i5 tests on a temporary copy)
import sys, unreal
A = sys.argv[1:]
PATH = A[A.index('--bpc') + 1] if '--bpc' in A else '/Game/CastleDefender/Gameplay/Tentacle/BPC_TentacleSpit'
CLIP, MON = '/Game/CastleDefender/Environment/Tentacles/Rig/Polish457/AS_Tentacle_HitReact450', '/Game/CastleDefender/Environment/Tentacles/Rig/Polish457/AM_Tentacle_HitReact450'
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
bp = unreal.load_asset(PATH); ge = BEL.find_event_graph(bp); ge = GE.get_graph_editor(ge)
nodes = {n.get_name(): n for n in ge.list_all_nodes()}
mine = [n for n in ge.list_all_nodes() if BEL.get_node_pos(n).y == 9000]        # every node of this fix sits on y = 9000
if '--revert' in A:
    if mine:
        s, h = nodes.get('SetWobbleT'), nodes.get('SetHits')
        ge.remove_nodes(mine)
        print('relink', PL.try_create_connection(BEL.find_then_pin(s), BEL.find_execute_pin(h)))
        ge.remove_member_variable('NextReactT'); BEL.compile_blueprint(bp); E.save_asset(PATH, only_if_is_dirty=False); print('removed', len(mine), 'nodes, compiled, saved')
    else: print('nothing to revert')
    raise SystemExit
for k in ('SetWobbleT', 'SetHits'):
    if k not in nodes: raise SystemExit('node missing: %s; BPC_TentacleSpit changed, send i5 an export' % k)
if mine: print('already wired,', len(mine), 'nodes'); raise SystemExit
if '--apply' not in A: print('WOULD make', MON, 'and add', 'NextReactT + the hit chain between SetWobbleT and SetHits'); raise SystemExit
if not E.does_asset_exist(MON):
    clip = unreal.load_asset(CLIP); f = unreal.AnimMontageFactory(); f.set_editor_property('source_animation', clip); f.set_editor_property('target_skeleton', clip.get_editor_property('skeleton'))
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(MON.split('/')[-1], MON.rsplit('/', 1)[0], unreal.AnimMontage, f)
    for k, v in (('blend_in', 0.12), ('blend_out', 0.5)):
        b = m.get_editor_property(k); b.set_editor_property('blend_time', v); m.set_editor_property(k, b)
    E.save_asset(MON, only_if_is_dirty=False); print('made', MON, m.get_play_length())
print('var', ge.add_member_variable('NextReactT', BEL.get_basic_type_by_name('real'), '0.0'))
X = [100]
def place(n):
    BEL.set_node_pos(n, unreal.IntPoint(X[0], 9000)); X[0] += 320; return n
def call(path): return place(ge.add_call_function_node(path))
def lnk(a, pa, b, pb):
    p, q = BEL.find_output_pin(a, pa), BEL.find_input_pin(b, pb)
    if not PL.try_create_connection(p, q): raise SystemExit('link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
now1 = call('/Script/Engine.GameplayStatics:GetTimeSeconds')
due = call('/Script/Engine.KismetMathLibrary:Greater_DoubleDouble')
own = call('/Script/Engine.ActorComponent:GetOwner')
par = call('/Script/Engine.Actor:GetAttachParentActor')
val = call('/Script/Engine.KismetSystemLibrary:IsValid')
both = call('/Script/Engine.KismetMathLibrary:BooleanAND')
br = place(ge.add_branch_node())
gnr = place(ge.add_get_member_variable_node('NextReactT'))
lnk(now1, 'ReturnValue', due, 'A'); lnk(gnr, 'NextReactT', due, 'B')
lnk(own, 'ReturnValue', par, 'self'); lnk(par, 'ReturnValue', val, 'Object')
lnk(due, 'ReturnValue', both, 'A'); lnk(val, 'ReturnValue', both, 'B'); lnk(both, 'ReturnValue', br, 'Condition')
now2 = call('/Script/Engine.GameplayStatics:GetTimeSeconds')
add = call('/Script/Engine.KismetMathLibrary:Add_DoubleDouble')
snr = place(ge.add_set_member_variable_node('NextReactT'))
lnk(now2, 'ReturnValue', add, 'A'); PL.set_pin_value(BEL.find_input_pin(add, 'B'), '2.5'); lnk(add, 'ReturnValue', snr, 'NextReactT')
root = call('/Script/Engine.Actor:K2_GetRootComponent'); lnk(par, 'ReturnValue', root, 'self')
cast = ge.create_node_from_name('Utilities|Casting|CastToSkeletalMeshComponent', unreal.Vector2D(X[0], 9000), []); place(cast)
lnk(root, 'ReturnValue', cast, 'Object')
pp = call('/Script/Engine.SkeletalMeshComponent:GetPostProcessInstance'); lnk(cast, 'AsSkeletal Mesh Component', pp, 'self')
mp = call('/Script/Engine.AnimInstance:Montage_Play'); lnk(pp, 'ReturnValue', mp, 'self')
PL.set_pin_value(BEL.find_input_pin(mp, 'MontageToPlay'), unreal.load_asset(MON).get_path_name())
# exec: SetWobbleT -> If -> SetNext -> Cast -> Montage -> SetHits; every other way out goes straight to SetHits
s, h = nodes['SetWobbleT'], nodes['SetHits']
then_s, ex_h = BEL.find_then_pin(s), BEL.find_execute_pin(h)
PL.break_pin_links(then_s)
print('in ', PL.try_create_connection(then_s, BEL.find_execute_pin(br)))
print('a', PL.try_create_connection(BEL.find_then_pin(br), BEL.find_execute_pin(snr)), PL.try_create_connection(BEL.find_else_pin(br), ex_h))
print('b', PL.try_create_connection(BEL.find_then_pin(snr), BEL.find_execute_pin(cast)))
print('c', PL.try_create_connection(BEL.find_then_pin(cast), BEL.find_execute_pin(mp)), PL.try_create_connection(BEL.find_output_pin(cast, 'CastFailed'), ex_h))
print('d', PL.try_create_connection(BEL.find_then_pin(mp), ex_h))
print('compile', BEL.compile_blueprint(bp), 'errors', [n.get_name() for n in ge.list_nodes_with_errors()], 'warnings', [n.get_name() for n in ge.list_nodes_with_warnings()])
print('montage pin', PL.get_pin_value(BEL.find_input_pin(mp, 'MontageToPlay')), '| next pin B', PL.get_pin_value(BEL.find_input_pin(add, 'B')))
print('saved', E.save_asset(PATH, only_if_is_dirty=False))
