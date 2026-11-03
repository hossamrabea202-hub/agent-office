# #451 arrow loops (i5, 2026-11-03). The castle's 42 arrow slits are 3 cm plates (35 x 150 cm) with M_Shadow, a LIT opaque
# navy material: they read as painted blue rectangles (shots/t2_bailey_se.png). A real arrow loop is a deep opening: the
# inside falls to near-black within a few cm and has no specular (RESEARCH_seams.md; arrow loops / embrasures). New
# material M_ArrowLoopVoid451 (UNLIT, emissive 0.004 warm grey = darkness with a hint of bounce, so it never glows and
# never shows a highlight) is assigned to the slit plates only. M_Shadow is NOT edited. Does not save the map.
#   py slit_void_ue.py --dry-run | --apply | --revert        (backup slit_void_backup.json)
import json, os, sys, unreal
H = 'C:/Users/hossam.rabea/agent-office/handoffs/gpt-review-polish/'
A = sys.argv[1:]
BK = H + 'slit_void_backup.json'
P = '/Game/CastleDefender/Environment/Castle/ArrowLoop451/M_ArrowLoopVoid451'
EAS, EAL, MEL = unreal.get_editor_subsystem(unreal.EditorActorSubsystem), unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
acts = {a.get_path_name(): a for a in EAS.get_all_level_actors()}
if '--revert' in A:
    for path, b in json.load(open(BK)).items():
        a = acts.get(path)
        if a: a.modify(); a.static_mesh_component.set_material(0, unreal.load_asset(b['mat'])); print('reverted', b['label'])
    raise SystemExit


def void_mat():
    if EAL.does_asset_exist(P): return unreal.load_asset(P)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(P.split('/')[-1], P.rsplit('/', 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -300, 0)
    c.set_editor_property('constant', unreal.LinearColor(0.0045, 0.0038, 0.0032, 1.0))
    MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(P)
    return m


hits = []
for a in acts.values():
    if a.get_class().get_name() != 'StaticMeshActor': continue
    c = a.static_mesh_component; mats = c.get_materials()
    if not mats or not mats[0] or mats[0].get_name() != 'M_Shadow' or not c.is_visible(): continue
    o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
    d = sorted([e.x * 2, e.y * 2, e.z * 2])
    if d[0] > 6 or not (100 < d[2] < 200) or not (20 < d[1] < 50): continue        # only the slit plates
    hits.append(a)
if '--apply' in A:
    vm = void_mat(); bk = json.load(open(BK)) if os.path.exists(BK) else {}
    for a in hits:
        c = a.static_mesh_component
        bk.setdefault(a.get_path_name(), {'label': a.get_actor_label(), 'mat': c.get_materials()[0].get_path_name()})
        a.modify(); c.set_material(0, vm)
    json.dump(bk, open(BK, 'w'), indent=0)
print('%s: %d arrow-slit plates %s' % ('APPLIED' if '--apply' in A else 'DRY RUN', len(hits), '-> M_ArrowLoopVoid451' if '--apply' in A else 'match'))
