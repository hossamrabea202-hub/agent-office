# #450 cannon reactions (i5, 2026-11-06): a cannonball hit plays AM_Tentacle_CannonA or _B (random) as a montage in the
# post-process ABP's slot, over the idle; the death plays AM_Tentacle_CannonC right before the 1.6 s delay + 7.5 s sink.
# RUN fix_pp_input_ue.py FIRST (the #457 slot fix): without the slot no montage shows. Editor idle, not in Play. No paste.
#   py wire_cannon_ue.py --dry-run | --apply | --revert      (--bp <asset path>: i5 tests on a copy; --no-death: hits only)
# Node names come from the 11-03 export of BP_TentacleVitals; the script STOPS if any is missing (send i5 a fresh export).
import sys, unreal
A = sys.argv[1:]
PATH = A[A.index('--bp') + 1] if '--bp' in A else '/Game/CastleDefender/Gameplay/Tentacle/BP_TentacleVitals'
P = '/Game/CastleDefender/Environment/Tentacles/Rig/Polish457/'
MA, MB, MC = P + 'AM_Tentacle_CannonA', P + 'AM_Tentacle_CannonB', P + 'AM_Tentacle_CannonC'
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
Y = 9500
bp = unreal.load_asset(PATH); ge = GE.get_graph_editor(BEL.find_event_graph(bp))
nodes = {n.get_name(): n for n in ge.list_all_nodes()}
mine = [n for n in ge.list_all_nodes() if BEL.get_node_pos(n).y == Y]
# the cannonball branch: CX_199 (if cannonball) -then-> CX_200 (SpawnActor PlasmaBurst) -then-> CX_129
# the death chain: CX_162 (explosion sound at the actor) -then-> CX_163 (Delay 1.6) -> CX_174 (sink 7.5 s)
HIT_FROM, HIT_TO = 'CX_200', 'CX_129'
DIE_FROM, DIE_TO = 'CX_162', 'CX_163'
need = [HIT_FROM, HIT_TO] + ([] if '--no-death' in A else [DIE_FROM, DIE_TO])
missing = [k for k in need if k not in nodes]
if missing: raise SystemExit('nodes missing: %s; BP_TentacleVitals changed, send i5 a fresh export' % missing)
for m in (MA, MB, MC):
    if not E.does_asset_exist(m): raise SystemExit('montage missing: %s (run the import first)' % m)
if '--revert' in A:
    if mine:
        ge.remove_nodes(mine)
        print('relink hit', PL.try_create_connection(BEL.find_then_pin(nodes[HIT_FROM]), BEL.find_execute_pin(nodes[HIT_TO])))
        if DIE_FROM in nodes: print('relink death', PL.try_create_connection(BEL.find_then_pin(nodes[DIE_FROM]), BEL.find_execute_pin(nodes[DIE_TO])))
        print('compile', BEL.compile_blueprint(bp)); E.save_asset(PATH, only_if_is_dirty=False); print('removed', len(mine), 'nodes, saved')
    else: print('nothing to revert')
    raise SystemExit
if mine: print('already wired,', len(mine), 'nodes'); raise SystemExit
if '--apply' not in A:
    print('WOULD add: %s.then -> [mesh -> post-process instance -> Montage_Play(random A|B)] -> %s.execute' % (HIT_FROM, HIT_TO))
    if '--no-death' not in A: print('WOULD add: %s.then -> [mesh -> post-process instance -> Montage_Play(C)] -> %s.execute' % (DIE_FROM, DIE_TO))
    raise SystemExit
X = [100]
def place(n): BEL.set_node_pos(n, unreal.IntPoint(X[0], Y)); X[0] += 320; return n
def call(path): return place(ge.add_call_function_node(path))
def lnk(a, pa, b, pb):
    p, q = BEL.find_output_pin(a, pa), BEL.find_input_pin(b, pb)
    if not PL.try_create_connection(p, q): raise SystemExit('link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
def montage_chain(src_node, dst_node, montage_pin_value, random_pair=None):
    comp = call('/Script/Engine.Actor:GetComponentByClass'); PL.set_pin_value(BEL.find_input_pin(comp, 'ComponentClass'), '/Script/Engine.SkeletalMeshComponent')
    cast = place(ge.create_node_from_name('Utilities|Casting|CastToSkeletalMeshComponent', unreal.Vector2D(X[0], Y), [])); lnk(comp, 'ReturnValue', cast, 'Object')
    pp = call('/Script/Engine.SkeletalMeshComponent:GetPostProcessInstance'); lnk(cast, 'AsSkeletal Mesh Component', pp, 'self')
    then_s, ex_d = BEL.find_then_pin(src_node), BEL.find_execute_pin(dst_node)
    PL.break_pin_links(then_s)
    print('exec in', PL.try_create_connection(then_s, BEL.find_execute_pin(cast)), PL.try_create_connection(BEL.find_output_pin(cast, 'CastFailed'), ex_d))
    if random_pair:   # a Branch on RandomBool picks montage A or B (an object Select cannot feed the typed montage pin)
        rb = call('/Script/Engine.KismetMathLibrary:RandomBool'); br = place(ge.add_branch_node()); lnk(rb, 'ReturnValue', br, 'Condition')
        print('exec branch', PL.try_create_connection(BEL.find_then_pin(cast), BEL.find_execute_pin(br)))
        mps = []
        for pin, mon in (('then', random_pair[0]), ('else', random_pair[1])):
            mp = call('/Script/Engine.AnimInstance:Montage_Play'); lnk(pp, 'ReturnValue', mp, 'self')
            PL.set_pin_value(BEL.find_input_pin(mp, 'MontageToPlay'), unreal.load_asset(mon).get_path_name())
            print('exec', pin, PL.try_create_connection(BEL.find_output_pin(br, pin), BEL.find_execute_pin(mp)), PL.try_create_connection(BEL.find_then_pin(mp), ex_d)); mps.append(mp)
        return mps
    mp = call('/Script/Engine.AnimInstance:Montage_Play'); lnk(pp, 'ReturnValue', mp, 'self')
    PL.set_pin_value(BEL.find_input_pin(mp, 'MontageToPlay'), montage_pin_value)
    print('exec', PL.try_create_connection(BEL.find_then_pin(cast), BEL.find_execute_pin(mp)), PL.try_create_connection(BEL.find_then_pin(mp), ex_d))
    return mp
mp1 = montage_chain(nodes[HIT_FROM], nodes[HIT_TO], None, random_pair=(MA, MB))
if '--no-death' not in A: mp2 = montage_chain(nodes[DIE_FROM], nodes[DIE_TO], unreal.load_asset(MC).get_path_name())
print('compile', BEL.compile_blueprint(bp), 'errors', [n.get_name() for n in ge.list_nodes_with_errors()], 'warnings', [n.get_name() for n in ge.list_nodes_with_warnings()])
print('saved', E.save_asset(PATH, only_if_is_dirty=False))
