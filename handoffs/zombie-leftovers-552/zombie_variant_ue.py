# Second walk and run per zombie (adjustedfilm, 2026-11-06). Editor idle, not in Play. No paste.
#   py zombie_variant_ue.py --dry-run | --apply | --revert
# Half of the walkers spawn with their own gait: a hunched lumber and a run with the arms thrown forward. The choice is made once per zombie, in its ABP_Zombie, on its first anim update.
# How: BS_Zombie_Locomotion (backup BS_Zombie_Locomotion_BAK552) gets a second set of samples 1000 higher (idle 1000, lumber 1113, run 1249, sprint 1350), and A_Run at 999 so the first set can never blend into the second.
# ABP_Zombie adds VariantOffset (0 or 1000) to the speed it feeds the blend space. A zombie scaled above 1.6 (the colossus) always stays on offset 0 and keeps its stomps.
# New nodes sit at y >= 5000 in EventGraph and AnimGraph. --revert removes them and restores the blend space. The script STOPS if a node name is missing.
import os, sys, unreal
HERE = os.path.dirname(os.path.abspath(__file__)); A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split()
R = '/Game/CastleDefender/Characters/Enemies/Zombie'; ABP = R + '/Anim/ABP_Zombie'; BS = R + '/Anim/BS_Zombie_Locomotion'; BAK = R + '/Anim/BS_Zombie_Locomotion_BAK552'; ZV = R + '/Anims_Walkers'; CLIPS = ['ZV_Walk_Lumber', 'ZV_Run_Reach']
E, BEL, PL, GE = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
M = '/Script/Engine.KismetMathLibrary:'; KS = '/Script/Engine.KismetSystemLibrary:'; AC = '/Script/Engine.Actor:'; YMIN = 5000
def say(*a): print('ZV552', ' '.join(str(x) for x in a))
bp = unreal.load_asset(ABP); gra, gev = BEL.find_graph(bp, 'AnimGraph'), BEL.find_graph(bp, 'EventGraph'); ga, ge = GE.get_graph_editor(gra), GE.get_graph_editor(gev)
na, ne = {x.get_name(): x for x in ga.list_all_nodes()}, {x.get_name(): x for x in ge.list_all_nodes()}
for k, d in (('ZbBS', na), ('ZgLen', na), ('K2Node_Event_0', ne), ('K2Node_CallFunction_0', ne)):
    if k not in d: raise SystemExit('ZV552 %s missing; ABP_Zombie changed, send i5 a fresh export' % k)
mine = [x for x in ga.list_all_nodes() + ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]; bsa = unreal.load_asset(BS)
def seq(): return [(round(s.get_editor_property('sample_value').x, 1), s.get_editor_property('animation').get_name()) for s in bsa.get_editor_property('sample_data')]
say('samples', seq())
if '--revert' in A:
    if mine:
        ga.remove_nodes([x for x in ga.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]); ge.remove_nodes([x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YMIN]); say('relink', PL.try_create_connection(BEL.find_output_pin(na['ZgLen'], 'ReturnValue'), BEL.find_input_pin(na['ZbBS'], 'X'))); say('compile', BEL.compile_blueprint(bp)); say('saved', E.save_asset(ABP, only_if_is_dirty=False))
    if E.does_asset_exist(BAK):
        b = unreal.load_asset(BAK); bsa.set_editor_property('blend_parameters', b.get_editor_property('blend_parameters')); bsa.set_editor_property('sample_data', b.get_editor_property('sample_data')); E.save_loaded_asset(bsa); say('samples now', seq())
    say('DONE revert'); raise SystemExit(0)
if '--apply' not in A: say('WOULD import', CLIPS, 'WOULD add 5 samples, axis 1400, already wired:', bool(mine), 'event then links', len(list(PL.list_connected_pins(BEL.find_then_pin(ne['K2Node_Event_0']))))); raise SystemExit(0)
# clips
skel = unreal.load_asset(R + '/SK_Zombie_Skeleton'); tasks = []
for c in CLIPS:
    ui = unreal.FbxImportUI(); ui.set_editor_property('import_mesh', False); ui.set_editor_property('import_animations', True); ui.set_editor_property('import_materials', False); ui.set_editor_property('import_textures', False); ui.set_editor_property('skeleton', skel); ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)
    ad = ui.get_editor_property('anim_sequence_import_data'); ad.set_editor_property('animation_length', unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME); ad.set_editor_property('import_bone_tracks', True); ad.set_editor_property('remove_redundant_keys', False)
    for k, v in (('use_default_sample_rate', False), ('custom_sample_rate', 30)):
        try: ad.set_editor_property(k, v)
        except Exception: pass
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'fbx', c + '.fbx'); t.destination_path = ZV; t.destination_name = c; t.automated = True; t.replace_existing = True; t.save = True; t.options = ui; tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for c in CLIPS:
    a_ = unreal.load_asset(ZV + '/' + c)
    if not a_: raise SystemExit('ZV552 import failed %s; nothing else changed' % c)
    say('clip', c, 'len', round(a_.get_play_length(), 2))
# blend space
if not E.does_asset_exist(BAK): E.duplicate_asset(BS, BAK); E.save_asset(BAK, only_if_is_dirty=False)
b = unreal.load_asset(BAK); smp = list(b.get_editor_property('sample_data')); byx = {round(s.get_editor_property('sample_value').x): s.get_editor_property('animation') for s in smp}
if set(byx) != {0, 113, 249, 350}: raise SystemExit('ZV552 blend space samples changed %s; send i5 the list' % sorted(byx))
def add(x, an):
    s = unreal.BlendSample(); s.set_editor_property('animation', an); s.set_editor_property('sample_value', unreal.Vector(x, 0, 0)); s.set_editor_property('rate_scale', 1.0); smp.append(s)
add(999.0, byx[350]); add(1000.0, byx[0]); add(1113.0, unreal.load_asset(ZV + '/ZV_Walk_Lumber')); add(1249.0, unreal.load_asset(ZV + '/ZV_Run_Reach')); add(1350.0, byx[350])
pr = list(b.get_editor_property('blend_parameters')); pr[0].set_editor_property('max', 1400.0); pr[0].set_editor_property('grid_num', 140); bsa.set_editor_property('blend_parameters', pr); bsa.set_editor_property('sample_data', smp); E.save_loaded_asset(bsa); say('samples now', seq())
if mine: say('graph already wired', len(mine)); say('DONE'); raise SystemExit(0)
# graphs
BEL.compile_blueprint(bp); before = sorted(x.get_name() for x in ga.list_nodes_with_errors() + ge.list_nodes_with_errors())
BEL.add_member_variable(bp, 'VariantOffset', BEL.get_basic_type_by_name('real')); BEL.add_member_variable(bp, 'VariantChosen', BEL.get_basic_type_by_name('boolean')); BEL.compile_blueprint(bp); pos = [0, YMIN]
def place(x):
    BEL.set_node_pos(x, unreal.IntPoint(pos[0], pos[1])); pos[0] += 300; return x
def ip(x, p):
    r = BEL.find_input_pin(x, p)
    if not r: raise SystemExit('ZV552 no input pin %s.%s' % (x.get_name(), p))
    return r
def call(g, path, **lit):
    x = g.add_call_function_node(path)
    if not x: raise SystemExit('ZV552 no function ' + path)
    place(x)
    for k, v in lit.items(): PL.set_pin_value(ip(x, k), str(v))
    return x
def link(a, pa, b, pb):
    if not PL.try_create_connection(BEL.find_output_pin(a, pa), ip(b, pb)): raise SystemExit('ZV552 link failed %s.%s -> %s.%s' % (a.get_name(), pa, b.get_name(), pb))
# AnimGraph: speed + offset
plus = call(ga, M + 'Add_DoubleDouble'); g_ = place(ga.add_get_member_variable_node('VariantOffset')); PL.break_pin_links(ip(na['ZbBS'], 'X')); link(na['ZgLen'], 'ReturnValue', plus, 'A'); link(g_, 'VariantOffset', plus, 'B'); link(plus, 'ReturnValue', na['ZbBS'], 'X')
# EventGraph: choose once
ev, own = ne['K2Node_Event_0'], ne['K2Node_CallFunction_0']; after = list(PL.list_connected_pins(BEL.find_then_pin(ev)))
b1 = place(ge.add_branch_node()); link(place(ge.add_get_member_variable_node('VariantChosen')), 'VariantChosen', b1, 'Condition'); iv = call(ge, KS + 'IsValid'); link(own, 'ReturnValue', iv, 'Object'); b2 = place(ge.add_branch_node()); link(iv, 'ReturnValue', b2, 'Condition')
s1 = place(ge.add_set_member_variable_node('VariantChosen')); PL.set_pin_value(ip(s1, 'VariantChosen'), 'true'); sc = call(ge, AC + 'GetActorScale3D'); link(own, 'ReturnValue', sc, 'self'); bv = call(ge, M + 'BreakVector'); link(sc, 'ReturnValue', bv, 'InVec'); lt = call(ge, M + 'Less_DoubleDouble', B=1.6); link(bv, 'X', lt, 'A'); rb = call(ge, M + 'RandomBool'); an = call(ge, M + 'BooleanAND'); link(lt, 'ReturnValue', an, 'A'); link(rb, 'ReturnValue', an, 'B'); sf = call(ge, M + 'SelectFloat', A=1000.0, B=0.0); link(an, 'ReturnValue', sf, 'bPickA'); s2 = place(ge.add_set_member_variable_node('VariantOffset')); link(sf, 'ReturnValue', s2, 'VariantOffset')
for p in after: PL.break_single_pin_link(BEL.find_then_pin(ev), p)
for a_, b_ in ((BEL.find_then_pin(ev), BEL.find_execute_pin(b1)), (BEL.find_else_pin(b1), BEL.find_execute_pin(b2)), (BEL.find_then_pin(b2), BEL.find_execute_pin(s1)), (BEL.find_then_pin(s1), BEL.find_execute_pin(s2))):
    if not PL.try_create_connection(a_, b_): raise SystemExit('ZV552 exec failed')
ok = BEL.compile_blueprint(bp); now = sorted(x.get_name() for x in ga.list_nodes_with_errors() + ge.list_nodes_with_errors()); say('compile', ok, 'errors before', before, 'after', now, 'old links after the event', len(after))
if after: raise SystemExit('ZV552 the update event already has logic: NOT saved. Close without saving, tell i5')
if set(now) - set(before): raise SystemExit('ZV552 NEW compile errors: NOT saved. Close without saving, tell i5')
say('saved', E.save_asset(ABP, only_if_is_dirty=False)); say('DONE')
