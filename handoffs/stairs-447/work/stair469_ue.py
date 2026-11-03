# #469 stone scale (i5, 2026-11-03): the 9 baked stair flights were placed at the kit actors' NON-uniform scales
# (N20 x5 0.95 x 1.30 x 1.08 = stones 37 % stretched; N13 x2 1.0 x 0.94 x 1.11; N31 x2 1.15 x 1.07 x 1.11). Fix: each size
# re-built + baked at its real placed size (spec_469_*.json, build469/), placed at scale 1. Same footprint (mesh x scale).
#   py stair469_ue.py assets                     import build469/SM_StairBaked469_N13/N20/N31 (+ _N _M _C) as NEW assets in
#                                                /Game/.../Castle/StairsBaked469 + W2 MIs (copies of the approved
#                                                MI_StairBaked451_N*_W2 look, own textures), complex-as-simple collision, saved
#   py stair469_ue.py swap --dry-run | --apply | --revert   Stair279_*: mesh 451 -> 469, actor scale -> 1, material
#                                                overrides -> the new W2 MI (backup stair469_backup.json). Map: Master saves.
#   py stair469_ue.py check                      trace down onto every flight (collision)
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]; mode = A[0]
H = next((h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/stairs-447/', 'C:/Users/hossa/Documents/agent-office/handoffs/stairs-447/')
          if os.path.isdir(h)), None)
B = H + 'build469/'; BK = H + 'work/stair469_backup.json'
DST = '/Game/CastleDefender/Environment/Castle/StairsBaked469'
OLD = '/Game/CastleDefender/Environment/Castle/StairsBaked451/'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
NS = [13, 20, 31]
ld = lambda p: unreal.load_asset(p)

def imp(path, name, ui=None):
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = DST; t.destination_name = name
    t.automated = True; t.replace_existing = True; t.save = False
    if ui: t.options = ui
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]); return ld(DST + '/' + name)

if mode == 'assets':
    for n in NS:
        nm = 'SM_StairBaked469_N%d' % n
        ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_materials = False; ui.import_textures = False; ui.import_as_skeletal = False
        sm = ui.static_mesh_import_data; sm.combine_meshes = True; sm.generate_lightmap_u_vs = True; sm.auto_generate_collision = False
        sm.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS; sm.build_nanite = False
        sm.import_rotation = unreal.Rotator(0.0, 0.0, -90.0)              # same as 451: matches the kit footprint
        mesh = imp(B + nm + '_low.fbx', nm, ui)
        tn = imp(B + nm + '_N.png', 'T_StairBaked469_N%d_N' % n)
        tn.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP); tn.set_editor_property('srgb', False); tn.set_editor_property('flip_green_channel', True)
        tm = imp(B + nm + '_M.png', 'T_StairBaked469_N%d_M' % n)
        tm.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS); tm.set_editor_property('srgb', False)
        tc = imp(B + nm + '_C.png', 'T_StairBaked469_N%d_C' % n); tc.set_editor_property('srgb', True)
        src = ld(OLD + 'MI_StairBaked451_N%d_W2' % n)                       # the approved W2 look (Alien OK, chat 1142)
        mi_n = 'MI_StairBaked469_N%d_W2' % n
        mi = ld(DST + '/' + mi_n) if EAL.does_asset_exist(DST + '/' + mi_n) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(mi_n, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, src.get_editor_property('parent'))
        for k in MEL.get_scalar_parameter_names(src): MEL.set_material_instance_scalar_parameter_value(mi, k, MEL.get_material_instance_scalar_parameter_value(src, k))
        for k in MEL.get_vector_parameter_names(src): MEL.set_material_instance_vector_parameter_value(mi, k, MEL.get_material_instance_vector_parameter_value(src, k))
        for k in MEL.get_texture_parameter_names(src):
            t = MEL.get_material_instance_texture_parameter_value(src, k)
            if t: MEL.set_material_instance_texture_parameter_value(mi, k, t)
        for k, t in (('BakedColor', tc), ('BakedNormal', tn), ('BakedAO', tm)): MEL.set_material_instance_texture_parameter_value(mi, k, t)
        MEL.update_material_instance(mi)
        mesh.set_material(0, mi); mesh.set_material(1, mi)
        mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        for a in (mesh, tn, tm, tc, mi): EAL.save_loaded_asset(a)
        b = mesh.get_bounding_box()
        print('ASSETS OK', nm, 'tris', mesh.get_num_triangles(0), 'bbox', [round(v, 1) for v in (b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z)])
    raise SystemExit

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
flights = []
for a in EAS.get_all_level_actors():
    if not a.get_actor_label().startswith('Stair279_') or a.get_class().get_name() != 'StaticMeshActor': continue
    c = a.get_component_by_class(unreal.StaticMeshComponent); m = c.get_editor_property('static_mesh')
    if m: flights.append((a, c, m))

if mode == 'check':
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for a, c, m in flights:
        o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
        h = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(o.x, o.y, o.z + e.z + 300), unreal.Vector(o.x, o.y, o.z - e.z - 50), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True).to_tuple()
        print('CHECK %-12s %-24s scale %s hit %s' % (a.get_actor_label(), m.get_name(), [round(v, 3) for v in a.get_actor_scale3d().to_tuple()], 'OK' if h[0] and h[9] == a else 'NO HIT'))
    raise SystemExit

if mode == 'swap':
    bk = json.load(open(BK)) if os.path.exists(BK) else {}
    for a, c, m in flights:
        lbl = a.get_actor_label()
        if '--revert' in A:
            if lbl not in bk: continue
            d = bk[lbl]; print('REVERT', lbl, m.get_name(), '->', d['mesh'].split('/')[-1], d['scale'])
            a.modify(); c.modify(); c.set_static_mesh(ld(d['mesh'])); a.set_actor_scale3d(unreal.Vector(*d['scale']))
            for i, p in enumerate(d['mats']): c.set_material(i, ld(p) if p else None)
            continue
        if not (m.get_name().startswith('SM_StairBaked451_N') or m.get_name().startswith('SM_Stair_W200_Solid_N')): print('SKIP', lbl, m.get_name()); continue   # Master: 451 bake; a map still on the kit works too
        n = int(m.get_name().split('_N')[-1]); new = ld(DST + '/SM_StairBaked469_N%d' % n); mi = ld(DST + '/MI_StairBaked469_N%d_W2' % n)
        sc = a.get_actor_scale3d()
        print('SWAP', lbl, m.get_name(), 'scale', [round(v, 3) for v in sc.to_tuple()], '->', new.get_name(), 'scale 1')
        if '--dry-run' in A: continue
        bk.setdefault(lbl, {'mesh': m.get_path_name(), 'scale': [sc.x, sc.y, sc.z], 'mats': [c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]})
        a.modify(); c.modify(); c.set_static_mesh(new); a.set_actor_scale3d(unreal.Vector(1, 1, 1))
        c.set_material(0, mi); c.set_material(1, mi)                       # explicit, no stale overrides (#301 lesson)
    if '--apply' in A: json.dump(bk, open(BK, 'w'), indent=1)
    raise SystemExit
