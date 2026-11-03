# #301 kit flights the AAA way (i5, 2026-11-03), on the #447 bake pipeline (build_stair.py: watertight low poly, high poly of
# real masonry: 1.5 cm mortar joints, per-stone bulge, worn nosings; 4K bake of normal + masks AO / joint / wear / tone).
#   py stair_baked451_ue.py assets [13 20 31]                  import build451/SM_StairBaked451_N<n>_low.fbx (+ _N / _M) as NEW
#                                                              assets in /Game/CastleDefender/Environment/Castle/StairsBaked451,
#                                                              2 new MIs per flight from MI_StairBaked_Tread / _Body (keep stone
#                                                              scans), complex-as-simple collision. The low poly is turned -90 deg
#                                                              at import so it matches the kit footprint (x 0..200, y 0..-30n).
#   py stair_baked451_ue.py swap [--only Stair279_03] --dry-run | --apply | --revert     kit mesh -> baked flight, backup json
#   py stair_baked451_ue.py check                               trace down onto every placed flight (collision test)
import json, os, sys, unreal
A = sys.argv[1:]; mode = A[0]
H = 'C:/Users/hossam.rabea/agent-office/handoffs/stairs-447/'
BUILD = H + 'build451/'
DST = '/Game/CastleDefender/Environment/Castle/StairsBaked451'
SRC = '/Game/CastleDefender/Environment/Castle/StairsBaked/'
BK = H + 'work/stair_baked451_backup.json'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary


def imp(path, name, ui=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = DST; t.destination_name = name
    t.automated = True; t.replace_existing = True; t.save = False
    if ui: t.options = ui
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return unreal.load_asset(DST + '/' + name)


def make_mi(name, src, tn, tm):
    p = DST + '/' + name
    mi = unreal.load_asset(p) if EAL.does_asset_exist(p) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    s = unreal.load_asset(SRC + src)
    MEL.set_material_instance_parent(mi, s.get_editor_property('parent'))
    for n in MEL.get_scalar_parameter_names(s): MEL.set_material_instance_scalar_parameter_value(mi, n, MEL.get_material_instance_scalar_parameter_value(s, n))
    for n in MEL.get_vector_parameter_names(s): MEL.set_material_instance_vector_parameter_value(mi, n, MEL.get_material_instance_vector_parameter_value(s, n))
    for n in MEL.get_texture_parameter_names(s):
        t = MEL.get_material_instance_texture_parameter_value(s, n)
        if t: MEL.set_material_instance_texture_parameter_value(mi, n, t)
    MEL.set_material_instance_texture_parameter_value(mi, 'BakedNormal', tn); MEL.set_material_instance_texture_parameter_value(mi, 'BakedMasks', tm)
    MEL.update_material_instance(mi); EAL.save_loaded_asset(mi); return mi


if mode == 'assets':
    for n in [int(x) for x in A[1:]] or [13, 20, 31]:
        name = 'SM_StairBaked451_N%d' % n
        ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_materials = False; ui.import_textures = False; ui.import_as_skeletal = False
        sm = ui.static_mesh_import_data; sm.combine_meshes = True; sm.generate_lightmap_u_vs = True; sm.auto_generate_collision = False
        sm.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS; sm.build_nanite = False
        sm.import_rotation = unreal.Rotator(0.0, 0.0, -90.0)
        mesh = imp(BUILD + name + '_low.fbx', name, ui)
        tn = imp(BUILD + name + '_N.png', 'T_StairBaked451_N%d_N' % n)
        tn.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP); tn.set_editor_property('srgb', False); tn.set_editor_property('flip_green_channel', True)
        tm = imp(BUILD + name + '_M.png', 'T_StairBaked451_N%d_M' % n)
        tm.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS); tm.set_editor_property('srgb', False)
        mt = make_mi('MI_StairBaked451_N%d_Tread' % n, 'MI_StairBaked_Tread', tn, tm)
        mb = make_mi('MI_StairBaked451_N%d_Body' % n, 'MI_StairBaked_Body', tn, tm)
        mesh.set_material(0, mt); mesh.set_material(1, mb)
        mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        for a in (mesh, tn, tm): EAL.save_loaded_asset(a)
        b = mesh.get_bounding_box()
        print('assets OK', name, 'tris', mesh.get_num_triangles(0), 'bbox', [round(v, 1) for v in (b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z)],
              'slots', [(s.material_slot_name, s.material_interface.get_name() if s.material_interface else None) for s in mesh.static_materials])
    raise SystemExit
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = {a.get_path_name(): a for a in EAS.get_all_level_actors()}
only = A[A.index('--only') + 1].split(',') if '--only' in A else None
if mode == 'check':
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for a in acts.values():
        c = a.get_component_by_class(unreal.StaticMeshComponent) if a.get_class().get_name() == 'StaticMeshActor' else None
        m = c.get_editor_property('static_mesh') if c else None
        if not m or 'StairBaked451' not in m.get_name(): continue
        o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
        h = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(o.x, o.y, o.z + e.z + 300), unreal.Vector(o.x, o.y, o.z - e.z - 50), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True).to_tuple()
        print('CHECK %-12s hit %-28s z %.1f  (stair top %.1f, bottom %.1f) %s' % (a.get_actor_label(), h[9].get_actor_label() if h[0] and h[9] else None, h[4].z if h[0] else -1, o.z + e.z, o.z - e.z, 'OK' if h[0] and h[9] == a else 'NO HIT ON STAIR'))
    raise SystemExit
if '--revert' in A:
    for path, b in json.load(open(BK)).items():
        a = acts.get(path)
        if not a or (only and a.get_actor_label() not in only): continue
        c = a.static_mesh_component; a.modify(); c.set_static_mesh(unreal.load_asset(b['mesh']))
        for i, m in enumerate(b['mats']): c.set_material(i, unreal.load_asset(m) if m else None)
        print('reverted', b['label'])
    raise SystemExit
bk = json.load(open(BK)) if os.path.exists(BK) else {}
k = 0
for a in acts.values():
    if a.get_class().get_name() != 'StaticMeshActor': continue
    c = a.static_mesh_component; m = c.get_editor_property('static_mesh')
    if not m or not m.get_name().startswith('SM_Stair_W200_Solid_N') or (only and a.get_actor_label() not in only): continue
    n = m.get_name().split('_N')[-1]; newp = DST + '/SM_StairBaked451_N' + n
    if not EAL.does_asset_exist(newp): print('SKIP no baked mesh', a.get_actor_label(), n); continue
    nm = unreal.load_asset(newp)
    print('%s %s: %s -> SM_StairBaked451_N%s' % ('SWAP' if '--apply' in A else 'WOULD', a.get_actor_label(), m.get_name(), n))
    if '--apply' in A:
        bk.setdefault(a.get_path_name(), {'label': a.get_actor_label(), 'mesh': m.get_path_name(), 'mats': [x.get_path_name() if x else '' for x in c.get_materials()]})
        a.modify(); c.set_static_mesh(nm)
        for i, s in enumerate(nm.static_materials): c.set_material(i, s.material_interface)
    k += 1
if '--apply' in A: json.dump(bk, open(BK, 'w'), indent=0)
print('%s: %d flights' % ('APPLIED' if '--apply' in A else 'DRY RUN', k))
